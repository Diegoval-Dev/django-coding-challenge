const BASE_URL = "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  const data = response.headers.get("content-type")?.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    const error = new Error(data?.error || `Request failed: ${response.status}`);
    error.data = data;
    error.status = response.status;
    throw error;
  }

  return data;
}

export const api = {
  products: {
    list: () => request("/products/"),
    create: (payload) =>
      request("/products/", { method: "POST", body: JSON.stringify(payload) }),
    update: (id, payload) =>
      request(`/products/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
  },

  orders: {
    list: () => request("/orders/"),
    get: (id) => request(`/orders/${id}/`),
    place: (items) =>
      request("/orders/", {
        method: "POST",
        body: JSON.stringify({ items }),
      }),
    cancel: (id) => request(`/orders/${id}/cancel/`, { method: "POST" }),
  },
};
