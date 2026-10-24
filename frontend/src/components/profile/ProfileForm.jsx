import { InputField } from "../common/InputField";
import { Button } from "../common/Button";

export function ProfileForm({ formData, profile, editing, onChange, onSave, onEdit, onCancel }) {
    return (
        <form onSubmit={onSave} className="form-grid">
            <InputField
                id="institutionalId"
                label="Institutional ID"
                value={profile.institutionalId || ""}
                readOnly
            />

            <InputField
                id="role"
                label="Role"
                value={profile.role || ""}
                readOnly
            />

            <InputField
                id="phone"
                name="phone"
                type="tel"
                label="Phone Number"
                value={formData.phone || ""}
                onChange={onChange}
                placeholder="+91 98765 43210"
                readOnly={!editing}
                required
            />

            <InputField
                id="emergencyContact"
                name="emergencyContact"
                type="tel"
                label="Emergency Contact"
                value={formData.emergencyContact || ""}
                onChange={onChange}
                placeholder="+91 98765 01234"
                readOnly={!editing}
                required
            />

            <InputField
                id="personalEmail"
                name="personalEmail"
                type="email"
                label="Personal Email"
                value={formData.personalEmail || ""}
                onChange={onChange}
                placeholder="student@example.com"
                readOnly={!editing}
                required
            />

            <div className="button-group">
                {editing ? (
                    <>
                        <Button type="submit" variant="primary">
                            Save Changes
                        </Button>
                        <Button type="button" variant="secondary" onClick={onCancel}>
                            Cancel
                        </Button>
                    </>
                ) : (
                    <Button type="button" variant="primary" onClick={onEdit}>
                        Edit Contact Details
                    </Button>
                )}
            </div>
        </form>
    );
}