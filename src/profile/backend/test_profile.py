
import unittest

from app import app, db, Profile, valid_phone, valid_email


class ProfileTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        
        with app.app_context():
            db.drop_all()
            db.create_all()

            profile = Profile(
                institutional_id="STU001",
                role="Student",
                name="Demo Student",
                phone="9876543210",
                emergency_contact="9876501234",
                personal_email="student@example.com",
            )
            db.session.add(profile)
            db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_valid_phone(self):
        self.assertTrue(valid_phone("9876543210"))
        self.assertTrue(valid_phone("+91 9876543210"))

    def test_invalid_phone(self):
        self.assertFalse(valid_phone("abc123"))
        self.assertFalse(valid_phone("123"))

    def test_valid_email(self):
        self.assertTrue(valid_email("student@example.com"))

    def test_invalid_email(self):
        self.assertFalse(valid_email("invalid-email"))
        self.assertFalse(valid_email("student@"))

    def test_get_profile(self):
        response = self.client.get("/api/profile/STU001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["institutionalId"], "STU001"
        )

    def test_update_profile(self):
        response = self.client.put(
            "/api/profile/STU001",
            json={
                "phone": "9123456789",
                "emergencyContact": "9988776655",
                "personalEmail": "updated@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["profile"]["personalEmail"],
            "updated@example.com",
        )

    def test_reject_invalid_phone(self):
        response = self.client.put(
            "/api/profile/STU001",
            json={"phone": "not-a-phone"},
        )
        self.assertEqual(response.status_code, 400)

    def test_reject_role_modification(self):
        response = self.client.put(
            "/api/profile/STU001",
            json={"role": "Admin"},
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_profile(self):
        response = self.client.get("/api/profile/UNKNOWN")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
