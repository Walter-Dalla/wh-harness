---
aliases: [Orders, Pickup]
---

# Orders and pickup

A customer places an order for a pickup slot; each line reserves shelf stock.

## Invariants

- An order line never reserves more than the shelf holds.

## Entry symbols

Backend: `OrderService`, `Order`, `PickupSlot`.

## Interactions

- **Stock** ([stock.md](stock.md)): each order line reserves `ShelfStock`; cancel releases it.
- **Loyalty** ([loyalty.md](loyalty.md)): a picked-up order adds one stamp.
