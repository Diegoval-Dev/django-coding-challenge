<script>
  import { onMount } from "svelte";
  import { api } from "../api.js";

  export let onNavigate;

  let orders = [];
  let loading = true;
  let error = null;
  let cancellingId = null;
  let cancelError = null;

  onMount(async () => {
    await loadOrders();
  });

  async function loadOrders() {
    loading = true;
    error = null;
    try {
      orders = await api.orders.list();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function handleCancel(orderId) {
    cancellingId = orderId;
    cancelError = null;
    try {
      const updated = await api.orders.cancel(orderId);
      orders = orders.map((o) => (o.id === updated.id ? updated : o));
    } catch (err) {
      cancelError = err.message;
    } finally {
      cancellingId = null;
    }
  }

  function statusClass(status) {
    return { pending: "status-pending", fulfilled: "status-fulfilled", cancelled: "status-cancelled" }[status] || "";
  }

  function formatDate(iso) {
    return new Date(iso).toLocaleString();
  }
</script>

<div class="page">
  <header class="page-header">
    <button class="back-button" on:click={() => onNavigate("products")}>
      ← Back to products
    </button>
    <h2>Order History</h2>
  </header>

  {#if loading}
    <p class="status">Loading orders…</p>
  {:else if error}
    <p class="status error">Failed to load orders: {error}</p>
  {:else if orders.length === 0}
    <p class="status">No orders yet.</p>
    <button class="link-button" on:click={() => onNavigate("products")}>
      Start shopping →
    </button>
  {:else}
    {#if cancelError}
      <div class="error-box" role="alert">{cancelError}</div>
    {/if}

    <ul class="order-list">
      {#each orders as order (order.id)}
        <li class="order-card">
          <div class="order-header">
            <div>
              <span class="order-id">Order #{order.id}</span>
              <span class="order-date">{formatDate(order.created_at)}</span>
            </div>
            <div class="order-header-right">
              <span class="order-total">${order.total}</span>
              <span class="status-badge {statusClass(order.status)}">
                {order.status}
              </span>
            </div>
          </div>

          <table class="items-table">
            <tbody>
              {#each order.items as item}
                <tr>
                  <td>{item.product.name}</td>
                  <td class="muted">×{item.quantity}</td>
                  <td class="muted">@ ${item.unit_price}</td>
                  <td class="subtotal">${item.line_total}</td>
                </tr>
              {/each}
            </tbody>
          </table>

          {#if order.status === "pending"}
            <div class="order-actions">
              <button
                class="cancel-button"
                on:click={() => handleCancel(order.id)}
                disabled={cancellingId === order.id}
              >
                {cancellingId === order.id ? "Cancelling…" : "Cancel order"}
              </button>
            </div>
          {/if}
        </li>
      {/each}
    </ul>
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

  .status.error {
    color: #c0392b;
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
    text-align: center;
  }

  .error-box {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    color: #991b1b;
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 16px;
  }

  .order-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .order-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    background: #fff;
  }

  .order-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
  }

  .order-id {
    font-weight: 600;
    font-size: 1rem;
    display: block;
  }

  .order-date {
    font-size: 0.8rem;
    color: #666;
    display: block;
    margin-top: 2px;
  }

  .order-header-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
  }

  .order-total {
    font-weight: 700;
    font-size: 1.1rem;
  }

  .status-badge {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 99px;
    text-transform: capitalize;
  }

  .status-pending {
    background: #fef9c3;
    color: #854d0e;
  }

  .status-fulfilled {
    background: #dcfce7;
    color: #166534;
  }

  .status-cancelled {
    background: #f3f4f6;
    color: #6b7280;
  }

  .items-table {
    width: 100%;
    border-collapse: collapse;
  }

  .items-table td {
    padding: 4px 6px;
    font-size: 0.9rem;
  }

  .muted {
    color: #666;
  }

  .subtotal {
    text-align: right;
    font-weight: 500;
  }

  .order-actions {
    margin-top: 12px;
    display: flex;
    justify-content: flex-end;
  }

  .cancel-button {
    background: none;
    border: 1px solid #fca5a5;
    color: #991b1b;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .cancel-button:hover:not(:disabled) {
    background: #fef2f2;
  }

  .cancel-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
