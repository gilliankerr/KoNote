# Progress Note Encryption (SEC1)

**Status:** Revised after expert panel critical review (2026-02-05)

## Overview

Encrypt clinical content (progress notes, participant reflections, target notes) at the application level using Fernet (AES-128), the same encryption used for client PII.

## Why This Matters

- **Defence in depth**: Database-level encryption (at rest) protects against physical theft; application-level encryption protects against database access by hosting providers, backup exposure, or SQL injection
- **Reduced blast radius**: If database credentials leak, clinical content remains encrypted
- **Regulatory alignment**: Demonstrates technical safeguards for PIPEDA/PHIPA compliance

### CLOUD Act — Important Limitation

The CLOUD Act compels US-based providers to produce data they control. If the encryption key is stored in an environment variable on the hosting platform, the provider *does* have access to it.

**For true CLOUD Act protection:**
- Agency must use external key management (Azure Key Vault, AWS KMS with customer-managed keys)
- Or agency must self-host

**What this implementation provides:**
- Protection against database breaches (attacker gets ciphertext, not plaintext)
- Protection against backup exposure
- Defence in depth alongside infrastructure encryption

It does NOT provide cryptographic immunity from legal compulsion if the hosting provider holds the key.

## Key Management — Critical Tradeoff

### The Risk You Must Understand

**If the encryption key is lost, all encrypted data is permanently unrecoverable.**

This includes:
- Client names and birth dates
- Progress notes and clinical content
- Any custom fields marked "sensitive"

There is no backdoor, no recovery option, no "forgot password" flow. The data is gone.

### Why This Matters for Nonprofits

Small nonprofits typically have:
- High staff turnover
- Limited IT expertise
- No documented key management procedures
- A "bus factor" of 1 (one person knows everything)

**For most small nonprofits, the risk of losing the encryption key is higher than the risk of a sophisticated database breach.**

This is not a reason to skip encryption — it's a reason to plan for key management.

### Setup Decision: Protection Level

During first-run setup, agencies must choose their protection level:

#### Option 1: Standard Protection (Recommended for most agencies)

**How it works:** Encryption key stored in hosting platform's environment variables.

**Protects against:**
- Database breaches (attacker gets ciphertext)
- Backup exposure
- Casual access by unauthorized staff

**Does NOT protect against:**
- Hosting provider with legal compulsion (CLOUD Act)
- Hosting provider staff with malicious intent

**Key recovery:** Hosting provider can help recover if account access is maintained.

**Choose this if:** You trust your hosting provider and want protection without key management burden.

#### Option 2: Enhanced Protection

**How it works:** Encryption key stored separately from hosting platform (external key vault, or agency-managed secret).

**Protects against:**
- All of Standard, plus:
- Hosting provider access (they don't have the key)

**Key recovery:** Agency is solely responsible. If key is lost, data is unrecoverable.

**Choose this if:** You have IT support, documented procedures, and a specific need for CLOUD Act protection.

### Key Backup Requirements

**For Standard Protection:**
- Document that the key is in the hosting platform's environment variables
- Ensure at least two people have access to the hosting account
- Record the hosting provider and account in your succession documentation

**For Enhanced Protection:**
- Store a paper copy of the key in a fireproof safe or safety deposit box
- Document the key location in your succession plan (but not the key itself)
- Test key recovery annually: can you retrieve it?
- Consider giving a sealed copy to your accountant or lawyer

### What to Document During Setup

Create a "KoNote Security Configuration" document (store securely, not in KoNote itself):

```
KoNote Security Configuration
==============================
Date configured: ____________
Configured by: ____________

Protection level: [ ] Standard  [ ] Enhanced

Encryption key location:
  [ ] Hosting platform environment variables (Standard)
  [ ] External location: ____________ (Enhanced)

Key backup location (Enhanced only):
  Primary: ____________
  Secondary: ____________

People with access to key/hosting:
  1. ____________
  2. ____________

Annual review date: ____________
```

### What Happens If Key Is Lost

1. All encrypted fields display `[decryption error]`
2. Client names, notes, and sensitive fields are permanently unreadable
3. You may need to rebuild client records from paper files or external sources
4. This may constitute a PIPEDA compliance issue (failure to maintain records)

**Prevention is the only cure.**

### Recommendation

**Most agencies should choose Standard Protection** unless they have:
- A specific regulatory requirement for external key management
- IT staff or consultants who can maintain key backup procedures
- A documented succession plan that includes key recovery

The goal is protection that will actually be maintained, not theoretical maximum security that fails in practice.

## Encryption Scope

| Data | Encrypted? | After SEC1 |
|------|------------|------------|
| Client name, birth date | Yes | Yes |
| Custom fields marked "sensitive" | Yes | Yes |
| Progress note content (`notes_text`, `summary`) | **No** | **Yes** |
| Participant reflection | **No** | **Yes** |
| Target notes within progress notes | **No** | **Yes** |
| Metric values | **No** | **No** |

### Decision: Metric Values

**Metric values will NOT be encrypted.**

Rationale:
- Metrics are numeric/categorical (e.g., "3", "improved", "yes/no")
- Without client identity, metric values are not PII
- Client identity is already encrypted
- Encrypting metrics would break reporting aggregation queries

If an agency uses free-text metrics containing clinical content, they should use custom fields marked "sensitive" instead.

## Prerequisites

### 1. Add Logging to Decryption Errors

Update `konote/encryption.py` to log failures:

```python
import logging
logger = logging.getLogger(__name__)

def decrypt_field(ciphertext):
    # ... existing code ...
    except InvalidToken:
        logger.error("Decryption failed — possible key mismatch or data corruption")
        return "[decryption error]"
```

### 2. Verify Audit Logs Don't Contain Note Content

Check `apps/audit/` to ensure note text isn't logged in plaintext.

### 3. Coordinate with EXP2

Export audit logging (EXP2a-d) should ship with or before SEC1.

## Implementation Plan

Since there's no production data, we can implement directly without migration complexity.

### Step 1: Update ProgressNote Model

Replace plain text fields with encrypted fields and property accessors:

```python
# apps/notes/models.py

from konote.encryption import encrypt_field, decrypt_field

class ProgressNote(models.Model):
    # ... existing fields (client_file, note_type, status, etc.) ...

    # Encrypted fields (replace existing TextField definitions)
    _notes_text_encrypted = models.BinaryField(default=b"", blank=True)
    _summary_encrypted = models.BinaryField(default=b"", blank=True)
    _participant_reflection_encrypted = models.BinaryField(default=b"", blank=True)

    @property
    def notes_text(self):
        return decrypt_field(self._notes_text_encrypted)

    @notes_text.setter
    def notes_text(self, value):
        self._notes_text_encrypted = encrypt_field(value)

    @property
    def summary(self):
        return decrypt_field(self._summary_encrypted)

    @summary.setter
    def summary(self, value):
        self._summary_encrypted = encrypt_field(value)

    @property
    def participant_reflection(self):
        return decrypt_field(self._participant_reflection_encrypted)

    @participant_reflection.setter
    def participant_reflection(self, value):
        self._participant_reflection_encrypted = encrypt_field(value)
```

### Step 2: Update ProgressNoteTarget Model

```python
class ProgressNoteTarget(models.Model):
    progress_note = models.ForeignKey(ProgressNote, on_delete=models.CASCADE, related_name="target_entries")
    plan_target = models.ForeignKey("plans.PlanTarget", on_delete=models.CASCADE, related_name="note_entries")
    _notes_encrypted = models.BinaryField(default=b"", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def notes(self):
        return decrypt_field(self._notes_encrypted)

    @notes.setter
    def notes(self, value):
        self._notes_encrypted = encrypt_field(value)
```

### Step 3: Create Migration

```bash
python manage.py makemigrations notes
python manage.py migrate
```

This will drop the old TextField columns and add the new BinaryField columns.

### Step 4: Update Key Rotation Registry

```python
# apps/auth_app/management/commands/rotate_encryption_key.py

def _get_encrypted_models():
    from apps.auth_app.models import User
    from apps.clients.models import ClientDetailValue, ClientFile
    from apps.notes.models import ProgressNote, ProgressNoteTarget  # ADD

    return [
        (User, ["_email_encrypted"]),
        (ClientFile, [
            "_first_name_encrypted",
            "_middle_name_encrypted",
            "_last_name_encrypted",
            "_birth_date_encrypted",
        ]),
        (ClientDetailValue, ["_value_encrypted"]),
        (ProgressNote, [  # ADD
            "_notes_text_encrypted",
            "_summary_encrypted",
            "_participant_reflection_encrypted",
        ]),
        (ProgressNoteTarget, ["_notes_encrypted"]),  # ADD
    ]
```

### Step 5: Add Tests

```python
# tests/test_encryption.py

@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class ProgressNoteEncryptionTest(TestCase):
    def setUp(self):
        enc_module._fernet = None

    def tearDown(self):
        enc_module._fernet = None

    def test_progress_note_content_encrypts(self):
        note = ProgressNote(client_file=self.client)
        note.notes_text = "Sensitive clinical content"

        # Raw field should be encrypted bytes
        self.assertIsInstance(note._notes_text_encrypted, bytes)
        self.assertNotIn(b"Sensitive", note._notes_text_encrypted)

        # Property returns plaintext
        self.assertEqual(note.notes_text, "Sensitive clinical content")

    def test_empty_string_handling(self):
        note = ProgressNote(client_file=self.client)
        note.notes_text = ""
        self.assertEqual(note.notes_text, "")
        self.assertEqual(note._notes_text_encrypted, b"")
```

## Files to Modify

| File | Change |
|------|--------|
| `konote/encryption.py` | Add logging to decrypt errors |
| `apps/notes/models.py` | Replace TextFields with encrypted BinaryFields + property accessors |
| `apps/auth_app/management/commands/rotate_encryption_key.py` | Add note fields to registry |
| `tests/test_notes.py` | Update any tests that check raw field values |
| `tests/test_encryption.py` | Add note encryption tests |
| `docs/security-operations.md` | Add key management guidance and backup procedures |
| Setup wizard (SETUP1) | Add protection level choice during first-run |

## Considerations

### Search Impact

Encrypted fields cannot be searched via SQL. Note search would need to load notes into Python and filter in memory. This is acceptable for typical volumes. Document that note content search is not supported.

### Performance

Fernet encryption/decryption is fast. For typical note volumes, impact is negligible.

### `__str__` Method

The `ProgressNote.__str__` method accesses `self.summary` and `self.notes_text`. After encryption, this triggers decryption — acceptable but worth noting for debugging.

## Success Criteria

- [ ] New notes encrypt on write (verify by inspecting database directly)
- [ ] Notes decrypt correctly on read
- [ ] Key rotation includes note fields (`--dry-run` confirms)
- [ ] Tests pass
- [ ] No `[decryption error]` in logs
- [ ] Key management guidance added to `docs/security-operations.md`
- [ ] Setup wizard includes protection level choice (or documented for SETUP1)
