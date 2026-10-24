export function Button({
    children,
    type = "button",
    variant = "primary",
    onClick,
    disabled = false,
    className = "",
}) {
    return (
        <button
            type={type}
            onClick={onClick}
            disabled={disabled}
            className={`btn btn-${variant} ${className}`.trim()}
        >
            {children}
        </button>
    );
}