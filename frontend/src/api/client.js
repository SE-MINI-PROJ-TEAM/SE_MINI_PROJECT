export async function apiFetch(endpoint, options = {}) {
    const config = {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    };

    const response = await fetch(endpoint, config);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const error = new Error(data.error || "An unexpected network error occurred.");
        error.status = response.status;
        error.code = data.code;
        throw error;
    }

    return data;
}
