export function InputField({ id, name, label, type = "text", value, onChange, placeholder, readOnly, required }) {
    return (
        <div className="input-group">
            <label htmlFor={id}>{label}</label>
            <input
                id={id}
                name={name}
                type={type}
                value={value || ""}
                onChange={onChange}
                placeholder={placeholder}
                readOnly={readOnly}
                required={required}
                className="input-control"
            />
        </div>
    );
}