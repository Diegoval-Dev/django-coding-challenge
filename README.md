# Nimble Store – Coding Challenge

## The Goal

You are building the backend and frontend for a simple e-commerce store. The goal is to produce a working, well-structured application that a small team could ship and maintain. We are not looking for a perfect solution — we are looking for clean code, sensible trade-offs, and your ability to explain your decisions.

This challenge is intentionally open-ended. There are things we have deliberately left unspecified. Make reasonable choices, document them, and be prepared to defend them.

---

## Requirements

### Backend (Django + Django REST Framework)

Build a REST API for a store with **products** and **orders**.

**Products**
- Products have a name, price, and quantity in stock.
- The API should support listing, creating, and editing products.

**Orders**
- A customer places an order by selecting products and quantities.
- Placing an order must **lock in the price at the time of purchase** — a price change on the product should not retroactively affect existing orders.
- Placing an order must **deduct stock**. If a product is out of stock or the requested quantity exceeds available stock, the order must be rejected with a meaningful error.
- **Two simultaneous orders must not be able to oversell a product.** If two customers try to buy the last item at the same time, only one should succeed.
- Orders have a status. A `pending` order can be cancelled; cancelling restores the inventory. An order that has already been `fulfilled` cannot be cancelled.
- The API should support retrieving a list of orders and the details of a single order.

### Frontend (Svelte)

Build a UI on top of the API you create. The `nimblestore_ui` directory contains a Svelte app configured and ready to run — you build what goes inside it.

**User stories:**
- A user can browse available products, see name, price, and current stock.
- A user can add products to a cart and adjust quantities before submitting.
- Submitting an order shows the confirmed total, or a clear error if it failed (e.g. item went out of stock between adding to cart and submitting).
- A user can view a list of past orders.

How you structure components, manage state, and handle loading and error states is up to you.

---

## What We Will Discuss

Add a **"Decisions & Trade-offs"** section to this README when you submit. For at least **three choices** you made — across the API design, data model, or frontend — write a short paragraph on: what you chose, what the alternative was, and why you went the direction you did.

There are no wrong answers. We want to understand how you think, not just what you built.

---

## Setup

The project runs via Docker Compose. You do not need to install Python, Node, or PostgreSQL locally.

```bash
# Start all services
docker compose up --build

# In a separate terminal, apply migrations
docker compose exec django python manage.py migrate
```

- Django API: `http://localhost:8000`
- Svelte UI: `http://localhost:8080`

When you add models, create and apply migrations:
```bash
docker compose exec django python manage.py makemigrations
docker compose exec django python manage.py migrate
```

---

## Tests

Write tests using `pytest`. Run them inside the Django container:

```bash
docker compose exec django pytest
```

Tests live in `checkout/tests/`. Cover the core behaviours — happy paths and the error cases that matter most.

---

## Code Quality

Pre-commit hooks are configured for linting and formatting. Install them once:

```bash
pip install pre-commit
pre-commit install
```

---

## Evaluation Criteria

We evaluate submissions on five dimensions:

| Dimension | What we look at |
|---|---|
| **Correctness** | Does it work? Do the core behaviours (stock deduction, price lock, cancellation) actually hold up? |
| **Architecture** | Is responsibility clearly assigned? Is business logic where it belongs? Would a new developer understand the structure quickly? |
| **Frontend quality** | Are components sensibly decomposed? Is async/error state handled gracefully? Does the UI give useful feedback? |
| **Tests** | Do the tests test *behaviour*, not just HTTP status codes? Are the important edge cases covered? |
| **Trade-off thinking** | Is the Decisions & Trade-offs section specific to *your* implementation? Can you explain why, not just what? |

Good luck.

---

## Decisions & Trade-offs

### 1. Pessimistic locking (`SELECT FOR UPDATE`) over optimistic locking for stock

The requirement that two simultaneous orders must not oversell a product is a concurrency problem. I chose pessimistic locking: `Product.objects.select_for_update().get(pk=...)` inside a `transaction.atomic()` block. This acquires a PostgreSQL row-level lock before reading and decrementing stock, so any second transaction targeting the same row blocks until the first commits or rolls back. The alternative, optimistic locking, adds a `version` integer to the model and retries the UPDATE if the version has changed since the read. Optimistic locking performs better under low contention (no waiting, only retrying), but for a store context — where two orders for the *same* product at the *same* instant is the exact failure mode we're protecting against — pessimistic locking is strictly correct with zero retry complexity. The trade-off is that concurrent orders for the same product are serialised at the DB layer, but for this scale that is entirely acceptable.

### 2. `unit_price` snapshot on `OrderItem` rather than a `total` field on `Order`

The price-lock requirement demands that a product price change never retroactively affects a completed order. I modelled this by storing `unit_price` on each `OrderItem` at placement time, copied from `Product.price` before any writes. `Order.total` is then a computed Python property (`sum(item.line_total for item in self.items.all())`), not a persisted column. The alternative is to store a `total` on the `Order` and skip the per-item snapshot. I rejected this because it loses auditability — without the per-item price you cannot reconstruct the breakdown for a customer receipt or a dispute. A derived `total` column also introduces a risk of drift if items are modified after placement. The cost of my approach is an extra join when loading an order, which `prefetch_related('items__product')` in the ViewSet queryset makes negligible.

### 3. Service layer (`orders/services.py`) rather than fat views or model methods

I extracted `place_order()` and `cancel_order()` into a dedicated service module, leaving views responsible only for HTTP concerns (parse input, call service, serialise output). The alternative was to put this logic directly in the `OrderViewSet.create()` method or as `Order.place()` model methods. Fat views are hard to test without the full HTTP stack, and model methods on `Order` felt wrong because `place_order` orchestrates across *both* the `Order` and `Product` models — it belongs in neither alone. A service function is testable with a direct Python call, reusable (a management command or an admin action could call it too), and makes the transaction boundary explicit rather than hidden inside ORM overrides. The trade-off is one additional file and one indirection layer, which I think any new developer would quickly find and understand.

### 4. Split `products` + `orders` apps over a monolithic `checkout` app

The scaffold provided a single `checkout` app. I chose to split the domain into two apps with clear ownership: `products` owns the `Product` model, and `orders` owns `Order`, `OrderItem`, and all the business logic around them. This makes the dependency direction explicit (`orders` depends on `products`, never the reverse) and ensures that each app's migrations, admin, serializers, and URLs are co-located with the models they serve. The trade-off is a slightly higher file count. For an application of this size a single app would have been fine, but the split better models the actual domain boundary and makes it easier to reason about which app "owns" each piece of behaviour — a quality that pays off as the codebase grows.

### 5. State-based navigation in Svelte over adding a router

The frontend has three views: product list, cart, and order history. I implemented navigation as a single `currentView` string in `App.svelte` rather than adding `svelte-routing` or similar. A router would give users real URLs and functional browser back/forward navigation — meaningful for a production app. But the Svelte 3 setup uses Rollup without a history-API fallback configured on the dev server, so adding a router would require changes to `rollup.config.js` and `sirv` flags for the trade-off of two or three lines of navigation logic. For three views with no deep-linking requirement, the state variable is the simpler and more maintainable choice. I documented this so a future developer understands it was a deliberate decision and not an oversight.
