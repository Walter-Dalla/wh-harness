#!/usr/bin/env node
// Drives one page of a headless Chromium over the DevTools protocol, with no dependency (Node 22 or newer: the
// global WebSocket). For a web client whose repo has no screen harness: layout checks, click paths, screenshots.
//
//   node cdp.mjs <steps.json> [--size <W>x<H>] [--scheme light|dark] [--timeout <ms>] [--console fail|show|ignore]
//
// <steps.json>: an array of steps, run in order in the same page; each step is an object with one of these keys.
//   {"size": "390x844"}                       viewport in CSS pixels (--size is the first one)
//   {"scheme": "dark"}                        prefers-color-scheme, light or dark (--scheme is the first one)
//   {"storage": {"key": "value"}}             localStorage entries, set before the scripts of every page loaded after it
//   {"goto": "http://127.0.0.1:5101/path"}    navigate and wait for the load event
//   {"wait": "<js expression>"}               poll until the expression is truthy
//   {"click": "<css selector>"}               wait for the element, scroll it into view, click its center (real mouse)
//   {"type": ["<css selector>", "text"]}      click the element and insert the text
//   {"key": "Enter"}                          Enter, Tab, Escape, Backspace, ArrowUp, ArrowDown, ArrowLeft, ArrowRight
//   {"eval": "<js expression>", "expect": v}  print the value as JSON; with "expect", fail unless it is equal to v
//   {"shot": "<file.png>", "full": true}      screenshot of the viewport; "full": the whole page; "selector": one element
// Every step also takes "timeout": <ms> (default --timeout, 5000) and "name": "<label>" (printed with the result).
//
// Output, one line per step: `OK <n> <key> <detail>` or `XX <n> <key> <reason>` (the run stops at the first XX), then
// `CONSOLE <text>` per console error, failed request or uncaught exception of the page, and as the last line
// `CDP: <ok> ok, <failed> failed, <c> console error(s)`. Exit 0; 1 when a step failed or, with --console fail (the
// default), the page logged an error (show: listed, exit unaffected; ignore: not listed). Exit 2 with
// `CDP FAILED: <reason>`: bad call, bad steps file, no browser, Node without WebSocket.
// Browser: $CHROME, else the newest ~/.cache/ms-playwright/chromium_headless_shell-*, else chromium,
// chromium-browser or google-chrome on the PATH. A "shot" path is relative to the current directory.
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';

const KEYS = { Enter: [13, '\r'], Tab: [9, ''], Escape: [27, ''], Backspace: [8, ''], ArrowLeft: [37, ''], ArrowUp: [38, ''], ArrowRight: [39, ''], ArrowDown: [40, ''] };
const OPS = ['size', 'scheme', 'storage', 'goto', 'wait', 'click', 'type', 'key', 'eval', 'shot'];
const children = [];
const folders = [];
process.on('exit', () => {
  // The browser runs in its own process group: its helpers die with it, before the profile folder is removed.
  for (const child of children) try { process.kill(-child.pid, 'SIGKILL'); } catch { /* already gone */ }
  if (children.some((child) => child.exitCode === null && child.signalCode === null)) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 150);
  for (const folder of folders) try { rmSync(folder, { recursive: true, force: true, maxRetries: 3, retryDelay: 50 }); } catch { /* best effort */ }
});
const die = (reason) => { console.log(`CDP FAILED: ${reason}`); process.exit(2); };
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
const short = (text, max = 300) => (text.length > max ? `${text.slice(0, max)}…` : text);

function parseArgs(argv) {
  const opts = { size: '1280x800', scheme: null, timeout: 5000, console: 'fail', steps: null };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (!arg.startsWith('--')) {
      if (opts.steps) die(`more than one steps file: ${opts.steps}, ${arg}`);
      opts.steps = arg;
      continue;
    }
    const name = arg.slice(2);
    if (!['size', 'scheme', 'timeout', 'console'].includes(name)) die(`unknown option ${arg}`);
    if (i + 1 >= argv.length) die(`${arg} without a value`);
    opts[name] = argv[++i];
  }
  if (!opts.steps) die('usage: cdp.mjs <steps.json> [--size <W>x<H>] [--scheme light|dark] [--timeout <ms>] [--console fail|show|ignore]');
  if (!/^\d+x\d+$/.test(opts.size)) die(`--size '${opts.size}' is not <W>x<H>`);
  if (opts.scheme !== null && !['light', 'dark'].includes(opts.scheme)) die(`--scheme is light or dark, not '${opts.scheme}'`);
  if (!['fail', 'show', 'ignore'].includes(opts.console)) die(`--console is fail, show or ignore, not '${opts.console}'`);
  opts.timeout = Number(opts.timeout);
  if (!Number.isInteger(opts.timeout) || opts.timeout <= 0) die('--timeout is a number of milliseconds');
  return opts;
}

function readSteps(path) {
  let steps;
  try { steps = JSON.parse(readFileSync(path, 'utf8')); } catch (err) { die(`cannot read ${path}: ${err.message}`); }
  if (!Array.isArray(steps) || !steps.length) die(`${path} is not a non-empty array of steps`);
  steps.forEach((step, i) => {
    const ops = step && typeof step === 'object' ? OPS.filter((op) => op in step) : [];
    if (ops.length !== 1) die(`step ${i + 1} of ${path} needs exactly one of: ${OPS.join(', ')}`);
  });
  return steps;
}

function findBrowser() {
  if (process.env.CHROME) return process.env.CHROME;
  const cache = join(homedir(), '.cache', 'ms-playwright');
  if (existsSync(cache)) {
    const build = (name) => Number(name.split('-').pop()) || 0;
    const shells = readdirSync(cache).filter((name) => name.startsWith('chromium_headless_shell-')).sort((a, b) => build(b) - build(a));
    for (const shell of shells) {
      for (const sub of readdirSync(join(cache, shell))) {
        const bin = join(cache, shell, sub, 'chrome-headless-shell');
        if (existsSync(bin)) return bin;
      }
    }
  }
  for (const dir of (process.env.PATH || '').split(':')) {
    for (const name of ['chromium', 'chromium-browser', 'google-chrome']) {
      if (dir && existsSync(join(dir, name))) return join(dir, name);
    }
  }
  return die('no browser: set CHROME, or install one (npx playwright install chromium-headless-shell)');
}

async function connect(bin, timeout) {
  const profile = mkdtempSync(join(tmpdir(), 'wh-cdp-'));
  folders.push(profile);
  const args = ['--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-sandbox', '--disable-gpu', '--no-first-run', 'about:blank'];
  if (!basename(bin).includes('headless-shell')) args.unshift('--headless=new');
  const browser = spawn(bin, args, { stdio: ['ignore', 'ignore', 'pipe'], detached: true });
  children.push(browser);
  const url = await new Promise((done) => {
    let seen = '';
    browser.stderr.on('data', (chunk) => { seen += chunk; const hit = /DevTools listening on (ws:\S+)/.exec(seen); if (hit) done(hit[1]); });
    browser.on('error', (err) => die(`cannot start ${bin}: ${err.message}`));
    browser.on('exit', (code) => die(`${bin} exited (${code}) before opening the debugging port: ${short(seen.trim(), 200)}`));
    setTimeout(() => die(`${bin} did not open the debugging port in ${Math.max(timeout, 15000)} ms`), Math.max(timeout, 15000)).unref();
  });
  browser.removeAllListeners('exit');
  const exited = new Promise((done) => browser.once('exit', done));
  const socket = new WebSocket(url);
  await new Promise((done) => {
    socket.addEventListener('open', done);
    socket.addEventListener('error', () => die('the WebSocket to the browser failed'));
  });
  let last = 0;
  const pending = new Map();
  const listeners = new Set();
  const errors = [];
  socket.addEventListener('message', (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id) { pending.get(msg.id)?.(msg); pending.delete(msg.id); return; }
    const p = msg.params || {};
    if (msg.method === 'Runtime.exceptionThrown') errors.push(`exception: ${p.exceptionDetails.exception?.description ?? p.exceptionDetails.text}`);
    if (msg.method === 'Runtime.consoleAPICalled' && p.type === 'error') errors.push(`console.error: ${p.args.map((a) => a.value ?? a.description ?? '').join(' ')}`);
    if (msg.method === 'Log.entryAdded' && p.entry.level === 'error') errors.push(`${p.entry.source}: ${p.entry.text} ${p.entry.url ?? ''}`.trim());
    for (const listener of [...listeners]) if (listener.method === msg.method) { listeners.delete(listener); listener.done(p); }
  });
  const send = async (method, params = {}, sessionId) => {
    const id = ++last;
    const reply = await new Promise((done) => { pending.set(id, done); socket.send(JSON.stringify({ id, method, params, sessionId })); });
    if (reply.error) throw new Error(`${method}: ${reply.error.message}`);
    return reply.result;
  };
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  const page = (method, params) => send(method, params, sessionId);
  for (const domain of ['Runtime', 'Page', 'Log']) await page(`${domain}.enable`);
  /** Resolves with the event's params, or rejects after `ms`; `cancel` drops it without a rejection. */
  const next = (method, ms) => {
    const listener = { method };
    const promise = new Promise((done, fail) => {
      listener.done = done;
      listener.timer = setTimeout(() => { listeners.delete(listener); fail(new Error(`no ${method} in ${ms} ms`)); }, ms);
    });
    listeners.add(listener);
    promise.catch(() => {}).finally(() => clearTimeout(listener.timer));
    return { promise, cancel: () => { listeners.delete(listener); clearTimeout(listener.timer); } };
  };
  /** Asks the browser to quit and waits for it, so nothing is still writing to its profile folder at exit. */
  const close = async () => {
    send('Browser.close').catch(() => {});
    await Promise.race([exited, sleep(2000)]);
  };
  return { page, next, errors, close };
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const steps = readSteps(opts.steps);
  if (typeof WebSocket === 'undefined') die(`Node ${process.versions.node} has no global WebSocket (22 or newer needed)`);
  const { page, next, errors, close } = await connect(findBrowser(), opts.timeout);

  const evaluate = async (expression) => {
    const r = await page('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error((r.exceptionDetails.exception?.description ?? r.exceptionDetails.text).split('\n')[0]);
    return r.result.value;
  };
  const until = async (expression, ms, what) => {
    const end = Date.now() + ms;
    let lastError = '';
    for (;;) {
      try { const value = await evaluate(expression); if (value) return value; } catch (err) { lastError = err.message; }
      if (Date.now() >= end) throw new Error(`${what} after ${ms} ms${lastError ? ` (${lastError})` : ''}`);
      await sleep(50);
    }
  };
  const setSize = (size) => { const [width, height] = size.split('x').map(Number); return page('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false }); };
  const setScheme = (value) => page('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value }] });
  const box = (selector, ms) => until(`(() => { const e = document.querySelector(${JSON.stringify(selector)}); if (!e) return null;
    e.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' }); const r = e.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height, sx: scrollX, sy: scrollY }; })()`, ms, `no element ${selector}`);
  const click = async (selector, ms) => {
    const b = await box(selector, ms);
    if (!b.w || !b.h) throw new Error(`element ${selector} has no size (hidden?)`);
    const at = { x: b.x + b.w / 2, y: b.y + b.h / 2 };
    await page('Input.dispatchMouseEvent', { type: 'mouseMoved', ...at });
    await page('Input.dispatchMouseEvent', { type: 'mousePressed', button: 'left', clickCount: 1, ...at });
    await page('Input.dispatchMouseEvent', { type: 'mouseReleased', button: 'left', clickCount: 1, ...at });
  };

  const run = {
    size: async (step) => { if (!/^\d+x\d+$/.test(step.size)) throw new Error(`'${step.size}' is not <W>x<H>`); await setSize(step.size); return step.size; },
    scheme: async (step) => { if (!['light', 'dark'].includes(step.scheme)) throw new Error(`'${step.scheme}' is not light or dark`); await setScheme(step.scheme); return step.scheme; },
    storage: async (step) => {
      const source = `try { for (const [k, v] of Object.entries(${JSON.stringify(step.storage)})) localStorage.setItem(k, String(v)); } catch (e) {}`;
      await page('Page.addScriptToEvaluateOnNewDocument', { source });
      return Object.keys(step.storage).join(', ');
    },
    goto: async (step, ms) => {
      const loaded = next('Page.loadEventFired', ms);
      const r = await page('Page.navigate', { url: step.goto });
      if (r.errorText) { loaded.cancel(); throw new Error(`${r.errorText} at ${step.goto}`); }
      await loaded.promise;
      return step.goto;
    },
    wait: async (step, ms) => { await until(step.wait, ms, `not true: ${step.wait}`); return step.wait; },
    click: async (step, ms) => { await click(step.click, ms); return step.click; },
    type: async (step, ms) => {
      const [selector, text] = Array.isArray(step.type) ? step.type : [];
      if (typeof selector !== 'string' || typeof text !== 'string') throw new Error('"type" is ["<selector>", "<text>"]');
      await click(selector, ms);
      await page('Input.insertText', { text });
      return `${selector} ${JSON.stringify(text)}`;
    },
    key: async (step) => {
      if (!(step.key in KEYS)) throw new Error(`key ${step.key} is not one of ${Object.keys(KEYS).join(', ')}`);
      const [code, text] = KEYS[step.key];
      const event = { key: step.key, code: step.key, windowsVirtualKeyCode: code, nativeVirtualKeyCode: code };
      await page('Input.dispatchKeyEvent', { type: text ? 'keyDown' : 'rawKeyDown', ...event, ...(text ? { text } : {}) });
      await page('Input.dispatchKeyEvent', { type: 'keyUp', ...event });
      return step.key;
    },
    eval: async (step) => {
      const value = await evaluate(step.eval);
      const got = JSON.stringify(value === undefined ? null : value);
      if ('expect' in step && got !== JSON.stringify(step.expect)) throw new Error(`${step.eval} = ${short(got)}, expected ${JSON.stringify(step.expect)}`);
      return `${step.eval} = ${short(got)}`;
    },
    shot: async (step, ms) => {
      let clip;
      if (step.selector) {
        const b = await box(step.selector, ms);
        if (!b.w || !b.h) throw new Error(`element ${step.selector} has no size (hidden?)`);
        clip = { x: b.x + b.sx, y: b.y + b.sy, width: b.w, height: b.h, scale: 1 };
      } else if (step.full) {
        const { cssContentSize: size } = await page('Page.getLayoutMetrics');
        clip = { x: 0, y: 0, width: size.width, height: size.height, scale: 1 };
      }
      const { data } = await page('Page.captureScreenshot', { format: 'png', ...(clip ? { clip, captureBeyondViewport: true } : {}) });
      const file = resolve(step.shot);
      mkdirSync(dirname(file), { recursive: true });
      writeFileSync(file, Buffer.from(data, 'base64'));
      return `${step.shot}${clip ? ` ${Math.round(clip.width)}x${Math.round(clip.height)}` : ''}`;
    },
  };

  await setSize(opts.size);
  if (opts.scheme) await setScheme(opts.scheme);
  let ok = 0;
  let failed = 0;
  for (const [i, step] of steps.entries()) {
    const op = OPS.find((name) => name in step);
    const label = `${i + 1} ${op}${step.name ? ` [${step.name}]` : ''}`;
    try {
      const detail = await run[op](step, Number.isInteger(step.timeout) ? step.timeout : opts.timeout);
      ok++;
      console.log(`OK ${label} ${detail}`);
    } catch (err) {
      failed++;
      console.log(`XX ${label} ${short(err.message)}`);
      break;
    }
  }
  await sleep(100); // console messages of the last step are still on their way
  const listed = opts.console === 'ignore' ? [] : errors;
  for (const text of listed) console.log(`CONSOLE ${short(text.replace(/\s+/g, ' '))}`);
  console.log(`CDP: ${ok} ok, ${failed} failed, ${listed.length} console error(s)`);
  await close();
  process.exit(failed || (opts.console === 'fail' && listed.length) ? 1 : 0);
}

main().catch((err) => die(short(err.stack || String(err), 600)));
