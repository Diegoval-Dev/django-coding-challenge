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
