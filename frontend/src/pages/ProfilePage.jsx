import { useEffect, useState } from "react";
import { ProfileForm } from "../components/profile/ProfileForm";
import { Alert } from "../components/common/Alert";

export function ProfilePage({ institutionalId = "STU001" }) {
    const [profile, setProfile] = useState(null);
    const [formData, setFormData] = useState({});
    const [editing, setEditing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    useEffect(() => {
        async function loadProfile() {
            try {
                // Leverages Vite proxy: /api -> http://127.0.0.1:5000
                const response = await fetch(`/api/profile/${institutionalId}`);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Could not load profile.");
                }

                setProfile(data);
                setFormData(data);
            } catch (err) {
                setError(`${err.message} Please check that the Flask server is running.`);
            } finally {
                setLoading(false);
            }
        }

        loadProfile();
    }, [institutionalId]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
        setMessage("");
        setError("");
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");

        const phonePattern = /^\+?[0-9\s()-]{7,20}$/;
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!phonePattern.test(formData.phone?.trim() || "")) {
            setError("Please enter a valid phone number.");
            return;
        }

        if (!phonePattern.test(formData.emergencyContact?.trim() || "")) {
            setError("Please enter a valid emergency contact number.");
            return;
        }

        if (!emailPattern.test(formData.personalEmail?.trim() || "")) {
            setError("Please enter a valid personal email address.");
            return;
        }

        try {
            const response = await fetch(`/api/profile/${profile.institutionalId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    phone: formData.phone.trim(),
                    emergencyContact: formData.emergencyContact.trim(),
                    personalEmail: formData.personalEmail.trim(),
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Could not save profile.");
            }

            setProfile(data.profile);
            setFormData(data.profile);
            setEditing(false);
            setMessage(data.message || "Contact details updated successfully.");
        } catch (err) {
            setError(err.message);
        }
    };

    const handleEdit = (e) => {
        if (e) e.preventDefault();
        setFormData(profile);
        setEditing(true);
        setMessage("");
        setError("");
    };

    const handleCancel = (e) => {
        if (e) e.preventDefault();
        setFormData(profile);
        setEditing(false);
        setMessage("");
        setError("");
    };

    if (loading) {
        return (
            <div className="card spinner-container">
                <p>Loading profile information...</p>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="profile-banner">
                <div className="avatar-badge">
                    {profile?.institutionalId ? profile.institutionalId.substring(0, 3) : "USR"}
                </div>
                <div className="profile-identity">
                    <h2>Institutional Profile</h2>
                    <span className="role-tag">{profile?.role || "User"}</span>
                </div>
            </div>

            <Alert type="error" message={error} />
            <Alert type="success" message={message} />

            {profile && (
                <ProfileForm
                    formData={formData}
                    profile={profile}
                    editing={editing}
                    onChange={handleChange}
                    onSave={handleSave}
                    onEdit={handleEdit}
                    onCancel={handleCancel}
                />
            )}
        </div>
    );
}