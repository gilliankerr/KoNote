"""Tests for public registration views."""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from cryptography.fernet import Fernet

from apps.auth_app.models import User
from apps.programs.models import Program
from apps.registration.models import RegistrationLink, RegistrationSubmission
import konote.encryption as enc_module


TEST_KEY = Fernet.generate_key().decode()


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class PublicRegistrationFormViewTest(TestCase):
    """Tests for the public registration form view."""

    def setUp(self):
        enc_module._fernet = None
        self.client = Client()

        # Create admin user
        self.admin = User.objects.create_user(
            username="admin", password="testpass123", display_name="Admin"
        )
        self.admin.is_admin = True
        self.admin.save()

        # Create a program
        self.program = Program.objects.create(name="Test Program", status="active")

        # Create an active registration link
        self.registration_link = RegistrationLink.objects.create(
            program=self.program,
            title="Test Registration",
            description="Test description for registration.",
            is_active=True,
            created_by=self.admin,
        )

    def tearDown(self):
        enc_module._fernet = None

    def test_public_form_loads_successfully(self):
        """Public registration form should load without authentication."""
        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Registration")
        self.assertContains(response, "Test description for registration.")

    def test_invalid_slug_returns_404(self):
        """Invalid slug should return 404."""
        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": "invalid-slug-12345"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_inactive_link_returns_404(self):
        """Inactive registration links should return 404."""
        self.registration_link.is_active = False
        self.registration_link.save()

        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registration Closed")

    def test_form_submission_creates_submission(self):
        """Valid form submission should create a RegistrationSubmission."""
        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )

        # Submit the form
        response = self.client.post(url, {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "555-1234",
            "consent": "on",
        })

        # Should redirect to confirmation page
        self.assertEqual(response.status_code, 302)
        self.assertIn("submitted", response.url)

        # Check submission was created
        submission = RegistrationSubmission.objects.filter(
            registration_link=self.registration_link
        ).first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.first_name, "John")
        self.assertEqual(submission.last_name, "Doe")
        self.assertEqual(submission.email, "john.doe@example.com")
        self.assertEqual(submission.status, "pending")

    def test_form_submission_requires_consent(self):
        """Form submission without consent should fail."""
        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )

        response = self.client.post(url, {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
        })

        # Should stay on form page with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "consent")

        # No submission should be created
        self.assertEqual(
            RegistrationSubmission.objects.filter(
                registration_link=self.registration_link
            ).count(),
            0
        )

    def test_auto_approve_creates_approved_submission(self):
        """Auto-approve registration should set status to approved."""
        self.registration_link.auto_approve = True
        self.registration_link.save()

        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )

        response = self.client.post(url, {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "consent": "on",
        })

        self.assertEqual(response.status_code, 302)

        submission = RegistrationSubmission.objects.filter(
            registration_link=self.registration_link
        ).first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.status, "approved")


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class RegistrationCapacityTest(TestCase):
    """Tests for registration capacity limits."""

    def setUp(self):
        enc_module._fernet = None
        self.client = Client()

        self.admin = User.objects.create_user(
            username="admin", password="testpass123", display_name="Admin"
        )
        self.admin.is_admin = True
        self.admin.save()

        self.program = Program.objects.create(name="Limited Program", status="active")

        # Create registration with max 2 spots
        self.registration_link = RegistrationLink.objects.create(
            program=self.program,
            title="Limited Registration",
            is_active=True,
            max_registrations=2,
            created_by=self.admin,
        )

    def tearDown(self):
        enc_module._fernet = None

    def test_shows_spots_remaining(self):
        """Form should display remaining spots."""
        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2")  # 2 spots remaining
        self.assertContains(response, "spots remaining")

    def test_closes_when_capacity_reached(self):
        """Registration should close when capacity is reached."""
        # Create 2 submissions (pending)
        for i in range(2):
            sub = RegistrationSubmission(registration_link=self.registration_link)
            sub.first_name = f"User{i}"
            sub.last_name = "Test"
            sub.email = f"user{i}@example.com"
            sub.status = "pending"
            sub.save()

        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registration Closed")
        self.assertContains(response, "reached capacity")


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class RegistrationDeadlineTest(TestCase):
    """Tests for registration deadline."""

    def setUp(self):
        enc_module._fernet = None
        self.client = Client()

        self.admin = User.objects.create_user(
            username="admin", password="testpass123", display_name="Admin"
        )
        self.admin.is_admin = True
        self.admin.save()

        self.program = Program.objects.create(name="Timed Program", status="active")

    def tearDown(self):
        enc_module._fernet = None

    def test_closes_after_deadline(self):
        """Registration should close after deadline passes."""
        # Create registration with deadline in the past
        past_deadline = timezone.now() - timezone.timedelta(hours=1)
        registration_link = RegistrationLink.objects.create(
            program=self.program,
            title="Expired Registration",
            is_active=True,
            closes_at=past_deadline,
            created_by=self.admin,
        )

        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registration Closed")
        self.assertContains(response, "deadline")

    def test_open_before_deadline(self):
        """Registration should be open before deadline."""
        future_deadline = timezone.now() + timezone.timedelta(days=7)
        registration_link = RegistrationLink.objects.create(
            program=self.program,
            title="Future Registration",
            is_active=True,
            closes_at=future_deadline,
            created_by=self.admin,
        )

        url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submit Registration")
        self.assertContains(response, "Registration closes")


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class RegistrationSubmittedViewTest(TestCase):
    """Tests for the registration submitted confirmation view."""

    def setUp(self):
        enc_module._fernet = None
        self.client = Client()

        self.admin = User.objects.create_user(
            username="admin", password="testpass123", display_name="Admin"
        )
        self.admin.is_admin = True
        self.admin.save()

        self.program = Program.objects.create(name="Test Program", status="active")
        self.registration_link = RegistrationLink.objects.create(
            program=self.program,
            title="Test Registration",
            is_active=True,
            created_by=self.admin,
        )

    def tearDown(self):
        enc_module._fernet = None

    def test_submitted_page_loads(self):
        """Submitted confirmation page should load."""
        # First submit a registration to set session data
        form_url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )
        self.client.post(form_url, {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "consent": "on",
        })

        # Now check the submitted page
        url = reverse(
            "registration:registration_submitted",
            kwargs={"slug": self.registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank You")
        self.assertContains(response, "REG-")  # Reference number

    def test_submitted_page_without_session_data(self):
        """Submitted page should still load without session data."""
        url = reverse(
            "registration:registration_submitted",
            kwargs={"slug": self.registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank You")

    def test_auto_approved_message(self):
        """Auto-approved submission should show different message."""
        self.registration_link.auto_approve = True
        self.registration_link.save()

        form_url = reverse(
            "registration:public_registration_form",
            kwargs={"slug": self.registration_link.slug}
        )
        self.client.post(form_url, {
            "first_name": "Auto",
            "last_name": "Approved",
            "email": "auto@example.com",
            "consent": "on",
        })

        url = reverse(
            "registration:registration_submitted",
            kwargs={"slug": self.registration_link.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registered")
