<script>
  import Cart from "./components/Cart.svelte";
  import OrderHistory from "./components/OrderHistory.svelte";
  import ProductList from "./components/ProductList.svelte";

  // State-based navigation — no router dependency needed for three views.
  // currentView is the single source of truth for which screen is shown.
  let currentView = "products"; // "products" | "cart" | "orders"

  function navigate(view) {
    currentView = view;
  }
</script>

<main>
  {#if currentView === "products"}
    <ProductList onNavigate={navigate} />
  {:else if currentView === "cart"}
    <Cart onNavigate={navigate} />
  {:else if currentView === "orders"}
    <OrderHistory onNavigate={navigate} />
  {/if}
</main>

<style>
  :global(*, *::before, *::after) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f9fafb;
    color: #111;
    line-height: 1.5;
  }

  main {
    min-height: 100vh;
  }
</style>
