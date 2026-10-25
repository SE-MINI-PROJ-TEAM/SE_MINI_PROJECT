import unittest
from app import app, db, Profile, AuditLog


class AdminAccountManagementTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

        with app.app_context():
            db.drop_all()
            db.create_all()

            # Seed test accounts
            p1 = Profile(
                institutional_id="STU301",
                role="Student",
                name="Active Student",
                personal_email="stu301@example.com",
                is_active=True,
            )
            p2 = Profile(
                institutional_id="FAC302",
                role="Faculty",
                name="Inactive Faculty",
                personal_email="fac302@example.com",
                is_active=False,
            )
            db.session.add_all([p1, p2])
            db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_tc_acc_04_user_search_and_list(self):
        """TC-ACC-04: Verify searching and listing user accounts."""
        response = self.client.get("/api/admin/users?search=STU301")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(len(data["users"]), 1)
        self.assertEqual(data["users"][0]["institutionalId"], "STU301")

    def test_tc_acc_04_deactivate_user_and_revoke_session(self):
        """TC-ACC-04: Verify deactivating an account revokes active JWT sessions immediately."""
        payload = {"isActive": False, "adminId": "ADM001"}
        response = self.client.put("/api/admin/users/STU301/status", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertFalse(data["user"]["isActive"])

        # Verify DB state & audit log writing
        with app.app_context():
            user = db.session.get(Profile, "STU301")
            self.assertFalse(user.is_active)

            log = AuditLog.query.filter_by(target_user_id="STU301").first()
            self.assertIsNotNone(log)
            self.assertEqual(log.admin_id, "ADM001")
            self.assertIn("INACTIVE (JWT Sessions Revoked)", log.details)

    def test_tc_acc_04_activate_user_account(self):
        """TC-ACC-04: Verify toggling inactive user back to active state."""
        payload = {"isActive": True, "adminId": "ADM001"}
        response = self.client.put("/api/admin/users/FAC302/status", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertTrue(data["user"]["isActive"])

    def test_tc_acc_04_update_role_metadata(self):
        """TC-ACC-04: Verify updating user role metadata claim."""
        payload = {"role": "Admin", "adminId": "ADM001"}
        response = self.client.put("/api/admin/users/STU301/status", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["user"]["role"], "Admin")

    def test_tc_acc_04_nonexistent_user_rejection(self):
        """TC-ACC-04: Verify 404 error when updating non-existent user."""
        payload = {"isActive": False, "adminId": "ADM001"}
        response = self.client.put("/api/admin/users/NON_EXISTENT/status", json=payload)
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()