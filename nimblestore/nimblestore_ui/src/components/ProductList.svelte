<script>
  import { onMount } from "svelte";
  import { api } from "../api.js";
  import {
    addToCart,
    cart,
    cartCount,
    removeFromCart,
    updateCartQuantity,
  } from "../stores.js";

  export let onNavigate;

  let products = [];
  let loading = true;
  let error = null;

  onMount(async () => {
    try {
      products = await api.products.list();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });

  function increment(product) {
    const current = $cart[product.id]?.quantity ?? 0;
    if (current === 0) {
      addToCart(product, 1);
    } else if (current < product.stock) {
      updateCartQuantity(product.id, current + 1);
    }
  }

  function decrement(product) {
    const current = $cart[product.id]?.quantity ?? 0;
    // updateCartQuantity calls removeFromCart when quantity reaches 0
    updateCartQuantity(product.id, current - 1);
  }
</script>

<div class="page">
  <header class="page-header">
    <h1>Nimble Store</h1>
    <button class="cart-button" on:click={() => onNavigate("cart")}>
      Cart
      {#if $cartCount > 0}
        <span class="badge">{$cartCount}</span>
      {/if}
    </button>
  </header>

  {#if loading}
    <p class="status">Loading products…</p>
  {:else if error}
    <p class="status error">Failed to load products: {error}</p>
  {:else if products.length === 0}
    <p class="status">No products available.</p>
  {:else}
    <ul class="product-grid">
      {#each products as product (product.id)}
        {@const qtyInCart = $cart[product.id]?.quantity ?? 0}
        <li class="product-card" class:in-cart={qtyInCart > 0}>
          <div class="product-info">
            <span class="product-name">{product.name}</span>
            <span class="product-price">${product.price}</span>
          </div>
          <div class="product-footer">
            <span class="stock" class:out-of-stock={product.stock === 0}>
              {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
            </span>

            {#if qtyInCart > 0}
              <!-- Quantity stepper — replaces the Add button once in cart -->
              <div class="qty-stepper">
                <button
                  class="stepper-btn"
                  on:click={() => decrement(product)}
                  aria-label="Remove one {product.name} from cart"
                >
                  −
                </button>
                <span class="qty-value">{qtyInCart}</span>
                <button
                  class="stepper-btn"
                  disabled={qtyInCart >= product.stock}
                  on:click={() => increment(product)}
                  aria-label="Add one more {product.name} to cart"
                >
                  +
                </button>
              </div>
            {:else}
              <button
                class="add-button"
                disabled={product.stock === 0}
                on:click={() => increment(product)}
              >
                Add to cart
              </button>
            {/if}
          </div>
        </li>
      {/each}
    </ul>
  {/if}

  <button class="link-button" on:click={() => onNavigate("orders")}>
    View order history →
  </button>
</div>

<style>
  .page {
    max-width: 900px;
    margin: 0 auto;
    padding: 24px 16px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
  }

  h1 {
    margin: 0;
    font-size: 1.8rem;
  }

  .cart-button {
    position: relative;
    background: #111;
    color: #fff;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.95rem;
  }

  .badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: #e53;
    color: #fff;
    font-size: 0.7rem;
    font-weight: bold;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .status {
    text-align: center;
    color: #666;
    padding: 48px 0;
  }

  .status.error {
    color: #c0392b;
  }

  .product-grid {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 16px;
  }

  .product-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    background: #fff;
    transition: border-color 0.15s;
  }

  .product-card.in-cart {
    border-color: #2563eb;
  }

  .product-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .product-name {
    font-weight: 600;
    font-size: 1rem;
  }

  .product-price {
    font-size: 1.25rem;
    color: #111;
  }

  .product-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
  }

  .stock {
    font-size: 0.8rem;
    color: #27ae60;
  }

  .stock.out-of-stock {
    color: #999;
  }

  /* ── Add to cart button ── */
  .add-button {
    background: #2563eb;
    color: #fff;
    border: none;
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: background 0.15s;
  }

  .add-button:hover:not(:disabled) {
    background: #1d4ed8;
  }

  .add-button:disabled {
    background: #ccc;
    cursor: not-allowed;
  }

  /* ── Quantity stepper ── */
  .qty-stepper {
    display: flex;
    align-items: center;
    gap: 0;
    border: 1.5px solid #2563eb;
    border-radius: 6px;
    overflow: hidden;
  }

  .stepper-btn {
    background: #fff;
    border: none;
    color: #2563eb;
    width: 32px;
    height: 32px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    line-height: 1;
    transition: background 0.1s;
  }

  .stepper-btn:hover:not(:disabled) {
    background: #eff6ff;
  }

  .stepper-btn:disabled {
    color: #ccc;
    cursor: not-allowed;
  }

  .qty-value {
    min-width: 28px;
    text-align: center;
    font-size: 0.9rem;
    font-weight: 600;
    color: #111;
    border-left: 1px solid #dbeafe;
    border-right: 1px solid #dbeafe;
    padding: 0 4px;
    line-height: 32px;
  }

  .link-button {
    background: none;
    border: none;
    color: #2563eb;
    cursor: pointer;
    margin-top: 32px;
    padding: 0;
    font-size: 0.9rem;
    text-decoration: underline;
  }
</style>
