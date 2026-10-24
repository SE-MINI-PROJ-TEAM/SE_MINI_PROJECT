import unittest
from app import app, db, Profile


class UserProvisioningTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

        with app.app_context():
            db.drop_all()
            db.create_all()

            # Seed initial user for conflict testing
            existing_user = Profile(
                institutional_id="EXISTING01",
                name="Existing User",
                personal_email="existing@example.com",
                role="Student",
                is_temporary_password=False,
            )
            db.session.add(existing_user)
            db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_tc_acc_01_successful_user_provisioning(self):
        """TC-ACC-01: Verify valid user provisioning and temp password generation."""
        payload = {
            "institutionalId": "STU101",
            "name": "Alice Smith",
            "personalEmail": "alice@example.com",
            "role": "Student",
        }
        response = self.client.post("/api/admin/users", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.get_json()
        self.assertIn("temporaryPassword", data)
        self.assertTrue(len(data["temporaryPassword"]) >= 8)
        self.assertEqual(data["user"]["institutionalId"], "STU101")
        self.assertTrue(data["user"]["isTemporaryPassword"])

        # Verify DB persistence
        with app.app_context():
            user = db.session.get(Profile, "STU101")
            self.assertIsNotNone(user)
            self.assertTrue(user.is_temporary_password)
            self.assertTrue(user.check_password(data["temporaryPassword"]))

    def test_tc_acc_01_duplicate_institutional_id_rejection(self):
        """TC-ACC-01: Verify 409 conflict on duplicate institutional ID."""
        payload = {
            "institutionalId": "EXISTING01",
            "name": "Duplicate ID Person",
            "personalEmail": "unique_email@example.com",
            "role": "Faculty",
        }
        response = self.client.post("/api/admin/users", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertIn("already exists", response.get_json()["error"])

    def test_tc_acc_01_duplicate_email_rejection(self):
        """TC-ACC-01: Verify 409 conflict on duplicate personal email."""
        payload = {
            "institutionalId": "NEW_ID_999",
            "name": "Duplicate Email Person",
            "personalEmail": "existing@example.com",
            "role": "Admin",
        }
        response = self.client.post("/api/admin/users", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertIn("already in use", response.get_json()["error"])

    def test_tc_acc_01_missing_required_fields(self):
        """TC-ACC-01: Verify 400 error on missing required attributes."""
        payload = {"institutionalId": "STU999", "name": "Incomplete User"}
        response = self.client.post("/api/admin/users", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_tc_acc_01_invalid_role_rejection(self):
        """TC-ACC-01: Verify 400 error on invalid role claim."""
        payload = {
            "institutionalId": "STU999",
            "name": "Invalid Role User",
            "personalEmail": "invalid_role@example.com",
            "role": "SuperUser",
        }
        response = self.client.post("/api/admin/users", json=payload)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()