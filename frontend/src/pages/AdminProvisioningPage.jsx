import { UserProvisioningForm } from "../components/admin/UserProvisioningForm";

export function AdminProvisioningPage() {
    return (
        <div className="app-container">
            <main className="main-content">
                <header className="page-header">
                    <h1>User Management</h1>
                    <p>Administrative User Provisioning & Credentials Generation (SYS-F-001).</p>
                </header>

                <UserProvisioningForm />
            </main>
        </div>
    );
}