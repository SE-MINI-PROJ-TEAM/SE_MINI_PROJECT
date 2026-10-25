import { useState, useEffect } from "react";
import { Alert } from "../common/Alert";
import { Button } from "../common/Button";

export function UserManagementTable() {
    const [users, setUsers] = useState([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [updatingId, setUpdatingId] = useState(null);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const fetchUsers = async (query = "") => {
        try {
            const response = await fetch(`/api/admin/users?search=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to load user accounts.");
            }

            setUsers(data.users || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers(search);
    }, [search]);

    const handleToggleStatus = async (user) => {
        setError("");
        setMessage("");
        setUpdatingId(user.institutionalId);

        try {
            const response = await fetch(`/api/admin/users/${user.institutionalId}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    isActive: !user.isActive,
                    adminId: "ADM001",
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to update user status.");
            }

            setMessage(data.message);
            await fetchUsers(search);
        } catch (err) {
            setError(err.message);
        } finally {
            setUpdatingId(null);
        }
    };

    const handleRoleChange = async (user, newRole) => {
        setError("");
        setMessage("");
        setUpdatingId(user.institutionalId);

        try {
            const response = await fetch(`/api/admin/users/${user.institutionalId}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    role: newRole,
                    adminId: "ADM001",
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to update role.");
            }

            setMessage(data.message);
            await fetchUsers(search);
        } catch (err) {
            setError(err.message);
        } finally {
            setUpdatingId(null);
        }
    };

    if (loading) {
        return (
            <div className="card spinner-container">
                <p>Loading user accounts...</p>
            </div>
        );
    }

    return (
        <div className="card">
            {/* Centered Title & Subtitle Header Block */}
            <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
                <h2 style={{ margin: "0 0 0.5rem 0", fontSize: "1.5rem", color: "var(--text-main)" }}>
                    Account Status & Role Management
                </h2>
                <p style={{ margin: 0, fontSize: "0.95rem", color: "var(--text-muted)" }}>
                    Search users, modify role claims, and toggle active status (SYS-F-004).
                </p>
            </div>

            {/* Search Bar Row */}
            <div style={{ display: "flex", justifyContent: "center", marginBottom: "1.25rem" }}>
                <input
                    type="text"
                    placeholder="Search ID, name, email, or role..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="input-control"
                    style={{ width: "100%", maxWidth: "360px", textAlign: "center" }}
                />
            </div>

            <Alert type="error" message={error} />
            <Alert type="success" message={message} />

            {/* Full Width Table - All Columns & Headings Centered */}
            <div style={{ width: "100%", overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                        <tr style={{ borderBottom: "2px solid var(--border-color)", textAlign: "center" }}>
                            <th style={{ padding: "0.85rem 1rem", color: "var(--text-muted)", textAlign: "center" }}>User ID</th>
                            <th style={{ padding: "0.85rem 1rem", color: "var(--text-muted)", textAlign: "center" }}>Name</th>
                            <th style={{ padding: "0.85rem 1rem", color: "var(--text-muted)", textAlign: "center" }}>Email</th>
                            <th style={{ padding: "0.85rem 1rem", color: "var(--text-muted)", textAlign: "center" }}>Role</th>
                            <th style={{ padding: "0.85rem 1rem", color: "var(--text-muted)", textAlign: "center" }}>Status</th>
                            <th style={{ padding: "0.85rem 1rem", color: "var(--text-muted)", textAlign: "center" }}>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map((u) => (
                            <tr key={u.institutionalId} style={{ borderBottom: "1px solid var(--border-color)", textAlign: "center" }}>
                                <td style={{ padding: "0.85rem 1rem", fontWeight: 700, fontFamily: "monospace", textAlign: "center" }}>
                                    {u.institutionalId}
                                </td>
                                <td style={{ padding: "0.85rem 1rem", textAlign: "center" }}>{u.name || "N/A"}</td>
                                <td style={{ padding: "0.85rem 1rem", color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center" }}>
                                    {u.personalEmail || "N/A"}
                                </td>
                                <td style={{ padding: "0.85rem 1rem", textAlign: "center" }}>
                                    <select
                                        value={u.role}
                                        onChange={(e) => handleRoleChange(u, e.target.value)}
                                        disabled={updatingId === u.institutionalId}
                                        className="input-control"
                                        style={{
                                            padding: "0.4rem 2.2rem 0.4rem 0.75rem",
                                            minWidth: "125px",
                                            fontSize: "0.875rem",
                                            boxSizing: "border-box",
                                            display: "inline-block",
                                            width: "auto",
                                        }}
                                    >
                                        <option value="Student">Student</option>
                                        <option value="Faculty">Faculty</option>
                                        <option value="Admin">Admin</option>
                                    </select>
                                </td>
                                <td style={{ padding: "0.85rem 1rem", textAlign: "center" }}>
                                    <span
                                        style={{
                                            padding: "0.3rem 0.75rem",
                                            borderRadius: "var(--radius-sm)",
                                            fontSize: "0.75rem",
                                            fontWeight: 700,
                                            backgroundColor: u.isActive ? "var(--success-bg)" : "var(--error-bg)",
                                            color: u.isActive ? "var(--success-text)" : "var(--error-text)",
                                            border: `1px solid ${u.isActive ? "var(--success-border)" : "var(--error-border)"}`,
                                            display: "inline-block",
                                        }}
                                    >
                                        {u.isActive ? "ACTIVE" : "INACTIVE"}
                                    </span>
                                </td>
                                <td style={{ padding: "0.85rem 1rem", textAlign: "center" }}>
                                    <Button
                                        variant={u.isActive ? "secondary" : "primary"}
                                        onClick={() => handleToggleStatus(u)}
                                        disabled={updatingId === u.institutionalId}
                                        style={{ padding: "0.4rem 0.85rem", fontSize: "0.825rem" }}
                                    >
                                        {updatingId === u.institutionalId
                                            ? "Processing..."
                                            : u.isActive
                                                ? "Deactivate (Revoke JWT)"
                                                : "Activate Account"}
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}