"""Client file and custom field models."""
from django.db import models

from KoNote2.encryption import decrypt_field, encrypt_field


class ClientFile(models.Model):
    """A client record with encrypted PII fields."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("discharged", "Discharged"),
    ]

    # Encrypted PII
    _first_name_encrypted = models.BinaryField(default=b"")
    _middle_name_encrypted = models.BinaryField(default=b"", blank=True)
    _last_name_encrypted = models.BinaryField(default=b"")
    _birth_date_encrypted = models.BinaryField(default=b"", blank=True)

    record_id = models.CharField(max_length=100, default="", blank=True)
    status = models.CharField(max_length=20, default="active", choices=STATUS_CHOICES)
    status_reason = models.TextField(default="", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # GDPR readiness
    consent_given_at = models.DateTimeField(null=True, blank=True)
    consent_type = models.CharField(max_length=50, default="", blank=True)
    retention_expires = models.DateField(null=True, blank=True)
    erasure_requested = models.BooleanField(default=False)
    erasure_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "clients"
        db_table = "client_files"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else f"Client #{self.pk}"

    # Encrypted property accessors
    @property
    def first_name(self):
        return decrypt_field(self._first_name_encrypted)

    @first_name.setter
    def first_name(self, value):
        self._first_name_encrypted = encrypt_field(value)

    @property
    def middle_name(self):
        return decrypt_field(self._middle_name_encrypted)

    @middle_name.setter
    def middle_name(self, value):
        self._middle_name_encrypted = encrypt_field(value)

    @property
    def last_name(self):
        return decrypt_field(self._last_name_encrypted)

    @last_name.setter
    def last_name(self, value):
        self._last_name_encrypted = encrypt_field(value)

    @property
    def birth_date(self):
        val = decrypt_field(self._birth_date_encrypted)
        return val if val else None

    @birth_date.setter
    def birth_date(self, value):
        self._birth_date_encrypted = encrypt_field(str(value) if value else "")


class ClientProgramEnrolment(models.Model):
    """Links a client to a program."""

    STATUS_CHOICES = [
        ("enrolled", "Enrolled"),
        ("unenrolled", "Unenrolled"),
    ]

    client_file = models.ForeignKey(ClientFile, on_delete=models.CASCADE, related_name="enrolments")
    program = models.ForeignKey("programs.Program", on_delete=models.CASCADE, related_name="client_enrolments")
    status = models.CharField(max_length=20, default="enrolled", choices=STATUS_CHOICES)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    unenrolled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "clients"
        db_table = "client_program_enrolments"

    def __str__(self):
        return f"{self.client_file} → {self.program}"


class CustomFieldGroup(models.Model):
    """A group of custom fields (e.g., 'Contact Information', 'Demographics')."""

    title = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20, default="active",
        choices=[("active", "Active"), ("archived", "Archived")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "clients"
        db_table = "custom_field_groups"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title


class CustomFieldDefinition(models.Model):
    """A single custom field definition within a group."""

    INPUT_TYPE_CHOICES = [
        ("text", "Text"),
        ("textarea", "Text Area"),
        ("select", "Dropdown"),
        ("date", "Date"),
        ("number", "Number"),
    ]

    group = models.ForeignKey(CustomFieldGroup, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=255)
    input_type = models.CharField(max_length=20, choices=INPUT_TYPE_CHOICES, default="text")
    placeholder = models.CharField(max_length=255, default="", blank=True)
    is_required = models.BooleanField(default=False)
    is_sensitive = models.BooleanField(default=False, help_text="Encrypt this field's values.")
    receptionist_access = models.CharField(
        max_length=10,
        default="none",
        choices=[
            ("none", "Hidden"),
            ("view", "View only"),
            ("edit", "View and edit"),
        ],
        help_text="What access receptionists have to this field.",
    )
    options_json = models.JSONField(default=list, blank=True, help_text="Options for select fields.")
    sort_order = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20, default="active",
        choices=[("active", "Active"), ("archived", "Archived")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "clients"
        db_table = "custom_field_definitions"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


class ClientDetailValue(models.Model):
    """A custom field value for a specific client (EAV pattern)."""

    client_file = models.ForeignKey(ClientFile, on_delete=models.CASCADE, related_name="detail_values")
    field_def = models.ForeignKey(CustomFieldDefinition, on_delete=models.CASCADE)
    value = models.TextField(default="", blank=True)
    _value_encrypted = models.BinaryField(default=b"", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "clients"
        db_table = "client_detail_values"
        unique_together = ["client_file", "field_def"]

    def get_value(self):
        """Return decrypted value if field is sensitive, plain value otherwise."""
        if self.field_def.is_sensitive:
            return decrypt_field(self._value_encrypted)
        return self.value

    def set_value(self, val):
        """Store encrypted or plain based on field sensitivity."""
        if self.field_def.is_sensitive:
            self._value_encrypted = encrypt_field(val)
            self.value = ""
        else:
            self.value = val
            self._value_encrypted = b""
