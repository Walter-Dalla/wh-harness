# Glossary — business language ↔ code language

## Orders

| Business | Code | Avoid / note |
|---|---|---|
| Order (what a customer asks for) | `Order`, `OrderService` | "ticket", "request" |
| Order line | `OrderLine` | |
| Pickup slot | `PickupSlot` | "appointment" |
| Cancel an order | cancel (`POST /orders/cancel`) | "delete" an order |

## Stock

| Business | Code | Avoid / note |
|---|---|---|
| Pantry (raw ingredients) | `Pantry`, `PantryItem` | "inventory" (inventory is finished goods) |
| Shelf (finished goods for sale) | `Shelf`, `ShelfStock` | "showcase" |
| Batch (one oven run) | `Batch`, `BakeSchedule` | |

## Loyalty

| Business | Code | Avoid / note |
|---|---|---|
| Stamp card | `StampCard` | "points card" |
| Free item reward | `Reward` | "coupon" (coupons are marketing) |

## Pitfalls

| In code | Means | Why |
|---|---|---|
| `Inventry` | shelf stock table | historic typo |
