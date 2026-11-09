---
name: start-app
description: Starts, stops or restarts the repository's app (services and client) and checks that they respond. Use to run, start, stop or restart the app.
---

# Start the app

Project profile (injected; `PROFILE_MISSING` = `Skill(wh:profile, "start-app")` and then `Read` both files, because the injection below ran before the profile existed):
!`cat .claude/profile/_common.md .claude/profile/start-app.md 2>/dev/null || echo PROFILE_MISSING`

From the root of the `_common § Clone` checkout, with the `_common § Toolchain`. This is the interactive skill: it uses the owner's ports (`_common § Ports`); the other skills bring up their own service on their own port.

## 1. Services

In the order of profile § Services: each one's `start` command; ready when the profile's health responds. Failure: the last lines of the log the profile names, in the answer. Port taken by a process that is not from this repo: ask before killing it.

**Done when every service in the profile answers its health check.**

## 2. Client

Profile § Client: the command, in the background (`run_in_background: true`) when it opens a window. Windowless (session without display, only checking the render): the alternative from profile § Client.

## 3. Alternative

Profile § Alternative (Docker or other), only when asked or when the native toolchain is missing in the checkout. Same port as the native one: stop one before the other.

## Stop

`stop` from profile § Services and the client process you started (`kill <pid>`; `_common § Toolchain` gives the per-OS equivalent). A process you did not start: ask. The owner's state (profile § State) stays as is; a command that deletes state asks for confirmation.

## Answer

One line per live service (URL, port, PID, log), the client, what was skipped and why.
