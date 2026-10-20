
import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

const initialProfile = {
  institutionalId: "STU001",
  role: "Student",
  phone: "",
  emergencyContact: "",
  personalEmail: "",
};

function App() {
  const [profile, setProfile] = useState(initialProfile);
  const [formData, setFormData] = useState(initialProfile);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/profile/${initialProfile.institutionalId}`
        );
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Could not load profile.");
        }

        setProfile(data);
        setFormData(data);
      } catch (err) {
        setError(
          `${err.message} Make sure the Flask backend and database are running.`
        );
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((previous) => ({ ...previous, [name]: value }));
    setMessage("");
    setError("");
  };

  const handleSave = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");

    const phonePattern = /^\+?[0-9\s()-]{7,20}$/;
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!phonePattern.test(formData.phone.trim())) {
      setError("Enter a valid phone number.");
      return;
    }

    if (!phonePattern.test(formData.emergencyContact.trim())) {
      setError("Enter a valid emergency contact number.");
      return;
    }

    if (!emailPattern.test(formData.personalEmail.trim())) {
      setError("Enter a valid personal email address.");
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/profile/${profile.institutionalId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            phone: formData.phone.trim(),
            emergencyContact: formData.emergencyContact.trim(),
            personalEmail: formData.personalEmail.trim(),
          }),
        }
      );

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

  const handleEdit = () => {
    setFormData(profile);
    setEditing(true);
    setMessage("");
    setError("");
  };

  const handleCancel = () => {
    setFormData(profile);
    setEditing(false);
    setMessage("");
    setError("");
  };

  if (loading) {
    return <main className="profile-container"><p>Loading profile...</p></main>;
  }

  return (
    <main className="profile-container">
      <h1>My Profile</h1>
      <p>View and update your personal contact information.</p>

      <form onSubmit={handleSave}>
        <label htmlFor="institutionalId">Institutional ID</label>
        <input id="institutionalId" value={profile.institutionalId} readOnly />

        <label htmlFor="role">Role</label>
        <input id="role" value={profile.role} readOnly />

        <label htmlFor="phone">Phone Number</label>
        <input
          id="phone"
          name="phone"
          type="tel"
          value={formData.phone || ""}
          onChange={handleChange}
          placeholder="Enter phone number"
          readOnly={!editing}
          required
        />

        <label htmlFor="emergencyContact">Emergency Contact</label>
        <input
          id="emergencyContact"
          name="emergencyContact"
          type="tel"
          value={formData.emergencyContact || ""}
          onChange={handleChange}
          placeholder="Enter emergency contact number"
          readOnly={!editing}
          required
        />

        <label htmlFor="personalEmail">Personal Email</label>
        <input
          id="personalEmail"
          name="personalEmail"
          type="email"
          value={formData.personalEmail || ""}
          onChange={handleChange}
          placeholder="Enter personal email"
          readOnly={!editing}
          required
        />

        {editing ? (
          <div className="button-group">
            <button type="submit">Save Changes</button>
            <button type="button" onClick={handleCancel}>Cancel</button>
          </div>
        ) : (
          <button type="button" onClick={handleEdit}>Edit Profile</button>
        )}

        {error && <p role="alert">{error}</p>}
        {message && <p role="status">{message}</p>}
      </form>
    </main>
  );
}

export default App;
