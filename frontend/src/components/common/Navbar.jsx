export function Navbar({ institutionalId }) {
    return (
        <header className="navbar">
            <div className="navbar-container">
                <div className="navbar-brand">
                    <span className="brand-icon">🎓</span>
                    <span className="brand-title">Academic Management System</span>
                </div>
                {institutionalId && (
                    <div className="navbar-user">
                        <span className="user-id-badge">{institutionalId}</span>
                    </div>
                )}
            </div>
        </header>
    );
}