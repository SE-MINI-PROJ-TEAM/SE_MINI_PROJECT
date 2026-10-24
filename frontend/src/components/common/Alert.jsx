export function Alert({ type = "error", message }) {
    if (!message) return null;

    return (
        <div className={`alert alert-${type}`} role={type === "error" ? "alert" : "status"}>
            <span>{type === "error" ? "⚠️" : "✅"}</span>
            <span>{message}</span>
        </div>
    );
}