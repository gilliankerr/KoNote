# AI-Powered Translation Implementation (I18N1)

## Overview

Implement automated French translation for KoNote using Claude API. Translations update automatically when app strings change—no human translators required.

## Why This Approach

- **Open-source friendly**: Nonprofits can deploy without translation expertise
- **Stays current**: New strings translate automatically
- **Context-aware**: Claude understands Canadian nonprofit vocabulary
- **Reversible**: Humans can still override specific translations in the .po file

## Implementation Steps

### Step 1: Add Dependencies

Add to `requirements.txt`:
```
anthropic>=0.39.0
polib>=1.2.0
```

- `anthropic`: Claude API client
- `polib`: Parse and modify .po translation files

### Step 2: Create Management Command

Create `apps/core/management/commands/translate_strings.py`:

```python
"""
AI-powered translation using Claude API.

Usage:
    python manage.py translate_strings
    python manage.py translate_strings --dry-run
    python manage.py translate_strings --retranslate "Sign In"
"""
```

**Command behaviour:**
1. Load `locale/fr/LC_MESSAGES/django.po`
2. Find entries with empty `msgstr` (untranslated)
3. Batch strings (10-20 at a time) and send to Claude
4. Update .po file with translations
5. Run `compilemessages` to create .mo file

### Step 3: Claude API Integration

**System prompt for translation:**
```
You are a translator for a Canadian nonprofit client management system.

Context:
- Translate English to Canadian French
- Use formal "vous" (not "tu")
- Canadian nonprofit terminology (organisme, bénéficiaire, intervenant)
- Keep UI text concise—space is limited
- Preserve placeholders like %(name)s and {count} exactly

For each English string, provide ONLY the French translation.
```

**API call structure:**
```python
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-haiku-3-5-sonnet-20241022",
    max_tokens=1024,
    system=TRANSLATION_SYSTEM_PROMPT,
    messages=[{
        "role": "user",
        "content": f"Translate to French:\n{batch_of_strings}"
    }]
)
```

### Step 4: Update Settings

Re-enable French in `konote/settings/base.py`:

```python
LANGUAGES = [
    ("en", "English"),
    ("fr", "Français"),
]
```

### Step 5: Update .gitignore

Remove `*.mo` from `.gitignore` so compiled translations are committed. This ensures deployments include working translations without needing gettext installed.

### Step 6: Update Dockerfile (if needed)

The current Dockerfile is already simplified—no gettext, no compilemessages during build. Translations will be pre-compiled and committed.

## Command Options

```bash
# Translate all untranslated strings
python manage.py translate_strings

# Preview what would be translated (no changes)
python manage.py translate_strings --dry-run

# Re-translate a specific string (override existing)
python manage.py translate_strings --retranslate "Sign In"

# Re-translate all strings (full refresh)
python manage.py translate_strings --all
```

## Developer Workflow

1. **After adding new UI strings:**
   ```bash
   python manage.py makemessages -l fr
   python manage.py translate_strings
   git add locale/
   git commit -m "Update French translations"
   ```

2. **Before deployment:**
   - Ensure translations are committed (including .mo files)
   - No translation steps needed at build time

## Cost Estimate

- ~2000 strings in current .po file
- Haiku: ~$0.01 per batch of 20 strings
- Full translation: ~$1.00 one-time
- Incremental updates: pennies per deployment

## Error Handling

- If Claude API fails, log error and skip (don't crash build)
- SafeLocaleMiddleware falls back to English if .mo is missing
- Keep existing translations if API returns garbage

## Testing

1. Run `translate_strings --dry-run` to preview
2. Spot-check French translations in the UI
3. Test with browser set to French (`Accept-Language: fr`)
4. Verify SafeLocaleMiddleware falls back gracefully

## Files to Create/Modify

| File | Action |
|------|--------|
| `apps/core/management/commands/translate_strings.py` | Create |
| `requirements.txt` | Add anthropic, polib |
| `konote/settings/base.py` | Re-enable French in LANGUAGES |
| `.gitignore` | Remove *.mo exclusion |
| `locale/fr/LC_MESSAGES/django.po` | Modified by command |
| `locale/fr/LC_MESSAGES/django.mo` | Created by command |

## Environment Variable

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

Only needed for development when running `translate_strings`. Not needed at runtime—translations are pre-compiled.
