<script>
  import { api } from "../api.js";
  import {
    cartItems,
    cartTotal,
    clearCart,
    removeFromCart,
    updateCartQuantity,
  } from "../stores.js";

  export let onNavigate;

  let submitting = false;
  let submitError = null;
  let confirmedOrder = null;

  async function handleSubmit() {
    submitting = true;
    submitError = null;

    const items = $cartItems.map((item) => ({
      product_id: item.product.id,
      quantity: item.quantity,
    }));

    try {
      confirmedOrder = await api.orders.place(items);
      clearCart();
    } catch (err) {
      // Surface the structured error from the API when available.
      // The backend returns { error, product, available, requested } for
      // stock failures, so we can give the user a specific message.
      if (err.data?.product) {
        submitError = `"${err.data.product}" only has ${err.data.available} unit(s) left, but you requested ${err.data.requested}.`;
      } else {
        submitError = err.message;
      }
    } finally {
      submitting = false;
    }
  }
</script>

<div class="page">
  <header class="page-header">
    <button class="back-button" on:click={() => onNavigate("products")}>
      ← Back to products
    </button>
    <h2>Your Cart</h2>
  </header>

  {#if confirmedOrder}
    <!-- Success state -->
    <div class="success-box">
      <h3>Order confirmed!</h3>
      <p>Order #{confirmedOrder.id} has been placed.</p>
      <table class="summary-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Qty</th>
            <th>Unit price</th>
            <th>Subtotal</th>
          </tr>
        </thead>
        <tbody>
          {#each confirmedOrder.items as item}
            <tr>
              <td>{item.product.name}</td>
              <td>{item.quantity}</td>
              <td>${item.unit_price}</td>
              <td>${item.line_total}</td>
            </tr>
          {/each}
        </tbody>
        <tfoot>
          <tr>
            <td colspan="3" class="total-label">Total</td>
            <td class="total-value">${confirmedOrder.total}</td>
          </tr>
        </tfoot>
      </table>
      <div class="success-actions">
        <button on:click={() => onNavigate("products")}>Continue shopping</button>
        <button on:click={() => onNavigate("orders")}>View order history</button>
      </div>
    </div>
  {:else if $cartItems.length === 0}
    <p class="status">Your cart is empty.</p>
    <button class="link-button" on:click={() => onNavigate("products")}>
      Browse products →
    </button>
  {:else}
    <!-- Cart contents -->
    <table class="cart-table">
      <thead>
        <tr>
          <th>Product</th>
          <th>Price</th>
          <th>Qty</th>
          <th>Subtotal</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {#each $cartItems as item (item.product.id)}
          <tr>
            <td>{item.product.name}</td>
            <td>${item.product.price}</td>
            <td>
              <input
                type="number"
                min="1"
                value={item.quantity}
                on:change={(e) =>
                  updateCartQuantity(item.product.id, parseInt(e.target.value))}
                class="qty-input"
              />
            </td>
            <td>
              ${(parseFloat(item.product.price) * item.quantity).toFixed(2)}
            </td>
            <td>
              <button
                class="remove-button"
                on:click={() => removeFromCart(item.product.id)}
                aria-label="Remove {item.product.name}"
              >
                ✕
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
      <tfoot>
        <tr>
          <td colspan="3" class="total-label">Total</td>
          <td class="total-value">${$cartTotal.toFixed(2)}</td>
          <td></td>
        </tr>
      </tfoot>
    </table>

    {#if submitError}
      <div class="error-box" role="alert">
        <strong>Could not place order:</strong>
        {submitError}
      </div>
    {/if}

    <div class="cart-actions">
      <button
        class="submit-button"
        on:click={handleSubmit}
        disabled={submitting}
      >
        {submitting ? "Placing order…" : "Place order"}
      </button>
    </div>
  {/if}
</div>

<style>
  .page {
    max-width: 800px;
    margin: 0 auto;
    padding: 24px 16px;
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 24px;
  }

  h2 {
    margin: 0;
  }

  .back-button {
    background: none;
    border: 1px solid #ccc;
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .status {
    text-align: center;
    color: #666;
    padding: 48px 0;
  }

  .link-button {
    background: none;
    border: none;
    color: #2563eb;
    cursor: pointer;
    padding: 0;
    font-size: 0.9rem;
    text-decoration: underline;
    display: block;
    margin: 0 auto;
  }

  .cart-table,
  .summary-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 24px;
  }

  .cart-table th,
  .cart-table td,
  .summary-table th,
  .summary-table td {
    padding: 12px 8px;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
  }

  .cart-table th,
  .summary-table th {
    font-size: 0.85rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .qty-input {
    width: 60px;
    padding: 4px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.95rem;
  }

  .remove-button {
    background: none;
    border: none;
    color: #999;
    cursor: pointer;
    font-size: 1rem;
    padding: 4px 8px;
  }

  .remove-button:hover {
    color: #c0392b;
  }

  .total-label {
    text-align: right;
    font-weight: 600;
  }

  .total-value {
    font-weight: 700;
    font-size: 1.1rem;
  }

  .error-box {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    color: #991b1b;
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 16px;
  }

  .cart-actions {
    display: flex;
    justify-content: flex-end;
  }

  .submit-button {
    background: #111;
    color: #fff;
    border: none;
    padding: 12px 28px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
  }

  .submit-button:disabled {
    background: #999;
    cursor: not-allowed;
  }

  .success-box {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: 24px;
  }

  .success-box h3 {
    margin: 0 0 8px;
    color: #166534;
  }

  .success-actions {
    display: flex;
    gap: 12px;
    margin-top: 16px;
  }

  .success-actions button {
    background: #166534;
    color: #fff;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
  }
</style>
