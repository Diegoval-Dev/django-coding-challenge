import { derived, writable } from "svelte/store";

// Cart is a map of productId → { product, quantity }
export const cart = writable({});

export const cartItems = derived(cart, ($cart) => Object.values($cart));

export const cartCount = derived(cart, ($cart) =>
  Object.values($cart).reduce((sum, item) => sum + item.quantity, 0)
);

export const cartTotal = derived(cart, ($cart) =>
  Object.values($cart).reduce(
    (sum, item) => sum + parseFloat(item.product.price) * item.quantity,
    0
  )
);

export function addToCart(product, quantity = 1) {
  cart.update((c) => {
    const existing = c[product.id];
    return {
      ...c,
      [product.id]: {
        product,
        quantity: existing ? existing.quantity + quantity : quantity,
      },
    };
  });
}

export function updateCartQuantity(productId, quantity) {
  if (quantity <= 0) {
    removeFromCart(productId);
    return;
  }
  cart.update((c) => ({
    ...c,
    [productId]: { ...c[productId], quantity },
  }));
}

export function removeFromCart(productId) {
  cart.update((c) => {
    const { [productId]: _removed, ...rest } = c;
    return rest;
  });
}

export function clearCart() {
  cart.set({});
}
