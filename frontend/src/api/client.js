export async function apiFetch(endpoint, options = {}) {
    const config = {
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
        ...options,
    };

    const response = await fetch(endpoint, config);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || "An unexpected network error occurred.");
    }

    return data;
}