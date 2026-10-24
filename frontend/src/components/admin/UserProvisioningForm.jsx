import { useState } from "react";
import { InputField } from "../common/InputField";
import { Alert } from "../common/Alert";

export function UserProvisioningForm() {
    const [formData, setFormData] = useState({
        institutionalId: "",
        name: "",
        personalEmail: "",
        role: "Student",
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [tempPassword, setTempPassword] = useState("");
    const [createdUser, setCreatedUser] = useState(null);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
        setError("");
        setTempPassword("");
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setTempPassword("");
        setCreatedUser(null);
        setLoading(true);

        try {
            const response = await fetch("/api/admin/users", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "User provisioning failed.");
            }

            setCreatedUser(data.user);
            setTempPassword(data.temporaryPassword);
            setFormData({ institutionalId: "", name: "", personalEmail: "", role: "Student" });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
            <h2 style={{ marginTop: 0, fontSize: "1.25rem", color: "var(--text-main)" }}>
                Provision New User Account
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
                Create student, faculty, or administrative accounts with temporary access credentials.
            </p>

            <Alert type="error" message={error} />

            {tempPassword && (
                <div className="alert alert-success" style={{ flexDirection: "column", alignItems: "flex-start" }}>
                    <div>
                        <strong>✅ User Account Created Successfully!</strong>
                    </div>
                    <div style={{ marginTop: "0.5rem" }}>
                        Account for <strong>{createdUser?.name}</strong> ({createdUser?.institutionalId}) is ready.
                    </div>
                    <div
                        style={{
                            marginTop: "0.75rem",
                            padding: "0.75rem 1rem",
                            background: "rgba(0,0,0,0.3)",
                            borderRadius: "var(--radius-sm)",
                            width: "100%",
                            boxSizing: "border-box",
                            fontFamily: "monospace",
                            fontSize: "1.05rem",
                        }}
                    >
                        Temporary Password: <strong style={{ color: "#ffffff" }}>{tempPassword}</strong>
                    </div>
                    <span style={{ fontSize: "0.75rem", marginTop: "0.5rem", opacity: 0.8 }}>
                        Provide this temporary credential to the user. They will be mandated to reset it on initial login.
                    </span>
                </div>
            )}

            <form onSubmit={handleSubmit} className="form-grid">
                <InputField
                    id="name"
                    name="name"
                    label="Full Name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="e.g., Prof. Sarah Jenkins"
                    required
                />

                <InputField
                    id="personalEmail"
                    name="personalEmail"
                    type="email"
                    label="Personal / Institutional Email"
                    value={formData.personalEmail}
                    onChange={handleChange}
                    placeholder="s.jenkins@university.edu"
                    required
                />

                <div className="input-group">
                    <label htmlFor="role">Role Claim</label>
                    <select
                        id="role"
                        name="role"
                        value={formData.role}
                        onChange={handleChange}
                        className="input-control"
                        required
                    >
                        <option value="Student">Student</option>
                        <option value="Faculty">Faculty</option>
                        <option value="Admin">Admin</option>
                    </select>
                </div>

                <InputField
                    id="institutionalId"
                    name="institutionalId"
                    label="Institutional ID"
                    value={formData.institutionalId}
                    onChange={handleChange}
                    placeholder="e.g., FAC042 or STU108"
                    required
                />

                <div className="button-group">
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? "Provisioning..." : "Provision User & Generate Credentials"}
                    </button>
                </div>
            </form>
        </div>
    );
}