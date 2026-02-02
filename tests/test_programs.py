"""Tests for program CRUD views."""
from django.test import TestCase, Client, override_settings
from cryptography.fernet import Fernet

from apps.auth_app.models import User
from apps.programs.models import Program, UserProgramRole
import konote.encryption as enc_module

TEST_KEY = Fernet.generate_key().decode()


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class ProgramViewsTest(TestCase):
    def setUp(self):
        enc_module._fernet = None
        self.client = Client()
        self.admin = User.objects.create_user(username="admin", password="testpass123", is_admin=True)
        self.staff = User.objects.create_user(username="staff", password="testpass123", is_admin=False)

    def test_admin_can_list_programs(self):
        self.client.login(username="admin", password="testpass123")
        resp = self.client.get("/programs/")
        self.assertEqual(resp.status_code, 200)

    def test_nonadmin_cannot_list_programs(self):
        self.client.login(username="staff", password="testpass123")
        resp = self.client.get("/programs/")
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_create_program(self):
        self.client.login(username="admin", password="testpass123")
        resp = self.client.post("/programs/create/", {
            "name": "Housing",
            "description": "Housing support",
            "colour_hex": "#10B981",
            "status": "active",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Program.objects.filter(name="Housing").exists())

    def test_nonadmin_cannot_create_program(self):
        self.client.login(username="staff", password="testpass123")
        resp = self.client.post("/programs/create/", {
            "name": "Housing",
            "description": "Housing support",
            "colour_hex": "#10B981",
            "status": "active",
        })
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_edit_program(self):
        self.client.login(username="admin", password="testpass123")
        prog = Program.objects.create(name="Youth", colour_hex="#3B82F6")
        resp = self.client.post(f"/programs/{prog.pk}/edit/", {
            "name": "Youth Services",
            "description": "",
            "colour_hex": "#3B82F6",
            "status": "active",
        })
        self.assertEqual(resp.status_code, 302)
        prog.refresh_from_db()
        self.assertEqual(prog.name, "Youth Services")

    def test_admin_can_view_program_detail(self):
        self.client.login(username="admin", password="testpass123")
        prog = Program.objects.create(name="Employment")
        resp = self.client.get(f"/programs/{prog.pk}/")
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_add_role(self):
        self.client.login(username="admin", password="testpass123")
        prog = Program.objects.create(name="Housing")
        resp = self.client.post(f"/programs/{prog.pk}/roles/add/", {
            "user": self.staff.pk,
            "role": "staff",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(UserProgramRole.objects.filter(user=self.staff, program=prog, status="active").exists())

    def test_admin_can_remove_role(self):
        self.client.login(username="admin", password="testpass123")
        prog = Program.objects.create(name="Housing")
        role = UserProgramRole.objects.create(user=self.staff, program=prog, role="staff")
        resp = self.client.post(f"/programs/{prog.pk}/roles/{role.pk}/remove/")
        self.assertEqual(resp.status_code, 200)
        role.refresh_from_db()
        self.assertEqual(role.status, "removed")
