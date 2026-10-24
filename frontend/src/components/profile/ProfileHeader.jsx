export function ProfileHeader({ institutionalId, role }) {
    const badgeText = institutionalId ? institutionalId.substring(0, 3) : "USR";

    return (
        <div className="profile-banner">
            <div className="avatar-badge">{badgeText}</div>
            <div className="profile-identity">
                <h2>Institutional Profile</h2>
                <span className="role-tag">{role || "User"}</span>
            </div>
        </div>
    );
}