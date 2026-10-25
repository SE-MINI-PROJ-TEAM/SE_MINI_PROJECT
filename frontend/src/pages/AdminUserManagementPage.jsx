import { UserManagementTable } from "../components/admin/UserManagementTable";

export function AdminUserManagementPage() {
    return (
        <div className="app-container">
            <main className="main-content">
                <header className="page-header">
                    <h1>User Administration</h1>
                    <p>Modify user status, role claims, and revoke active JWT sessions (SYS-F-004).</p>
                </header>

                <UserManagementTable />
            </main>
        </div>
    );
}