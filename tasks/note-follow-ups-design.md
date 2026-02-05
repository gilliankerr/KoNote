# Note Follow-ups Feature Design

## Overview

Add optional follow-up dates to progress notes. When staff record a note, they can set a follow-up date. The home page shows notes needing follow-up, helping staff remember to check in with clients.

## Design Principles

1. **Minimal model changes**: Two fields on existing model, no new models
2. **Notes are the source of truth**: Follow-ups are attached to notes, not separate tasks
3. **No calendar creep**: This is a reminder list, not a scheduling system
4. **Personal workflow**: Each staff member sees their own follow-ups

## User Stories

1. **Staff records session note**: After a counselling session, staff adds "Discussed housing application — follow up in 2 weeks" with follow-up date set
2. **Staff checks home page**: Sees "Follow-ups Due" section showing notes past their follow-up date
3. **Staff follows up**: Clicks through to client, records new note, old follow-up is marked complete
4. **Quick reminder**: Staff records quick note "Court date March 15" with follow-up date, creating both documentation and reminder

## Data Model Changes

### ProgressNote (existing model — add 2 fields)

```python
# In apps/notes/models.py, add to ProgressNote class:

follow_up_date = models.DateField(
    null=True,
    blank=True,
    help_text="Optional date to follow up on this note."
)
follow_up_completed_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text="When the follow-up was completed (new note recorded)."
)
```

No new models required.

## Implementation Steps

### Step 1: Model Migration

1. Add `follow_up_date` and `follow_up_completed_at` fields to `ProgressNote` model
2. Run `makemigrations notes` and `migrate`

### Step 2: Update Note Forms

**Quick Note Form** ([apps/notes/forms.py](apps/notes/forms.py)):
- Add optional `follow_up_date` field (date picker)
- Label: "Follow up by" with "(optional)" hint

**Full Note Form**:
- Same addition at the bottom of the form

### Step 3: Update Note Views

**note_create view** ([apps/notes/views.py](apps/notes/views.py)):
- Save `follow_up_date` from form if provided
- No changes to existing logic

**When creating a new note for a client**:
- Check if client has pending follow-ups from this author
- If yes, auto-complete them (set `follow_up_completed_at = now()`)
- This creates natural "note → follow-up → note" chains

### Step 4: Home Page Follow-ups Section

**Home view** ([apps/clients/urls_home.py](apps/clients/urls_home.py)):

Add query for pending follow-ups:
```python
from apps.notes.models import ProgressNote
from django.utils import timezone

# Notes by this user with follow-up date <= today and not completed
pending_follow_ups = ProgressNote.objects.filter(
    author=request.user,
    follow_up_date__lte=timezone.now().date(),
    follow_up_completed_at__isnull=True,
    status="default",  # Not cancelled
).select_related("client_file").order_by("follow_up_date")[:10]
```

**Home template** ([templates/clients/home.html](templates/clients/home.html)):

Add new section in Priority Items card (or as separate card):
```html
{% if pending_follow_ups %}
<div class="priority-section">
    <h4 class="priority-label">{% trans "Follow-ups Due" %}</h4>
    <ul class="card-list">
        {% for note in pending_follow_ups %}
        <li class="priority-item">
            <a href="{% url 'clients:client_detail' client_id=note.client_file.pk %}">
                {{ note.client_file.first_name }} {{ note.client_file.last_name }}
            </a>
            <span class="priority-detail">{{ note.notes_text|truncatechars:40 }}</span>
            <small class="secondary">{{ note.follow_up_date|date:"M j" }}</small>
        </li>
        {% endfor %}
    </ul>
</div>
{% endif %}
```

### Step 5: Stats Card

Add follow-up count to stats row:
```html
<dl class="stat-card{% if follow_up_count > 0 %} stat-card-warning{% endif %}">
    <dt>{% trans "Follow-ups Due" %}</dt>
    <dd class="stat-value">{{ follow_up_count }}</dd>
    <dd class="stat-subtext">{% trans "need your attention" %}</dd>
</dl>
```

### Step 6: Client Detail Enhancement (Optional)

On client detail page, show pending follow-ups for this client:
- Small indicator if there's an incomplete follow-up
- "You have a follow-up due for this client" banner

## Auto-Complete Logic

When staff records a **new note** for a client:

```python
# In note_create view, after saving the new note:
# Auto-complete any pending follow-ups from this author for this client

ProgressNote.objects.filter(
    client_file=client,
    author=request.user,
    follow_up_date__isnull=False,
    follow_up_completed_at__isnull=True,
    status="default",
).update(follow_up_completed_at=timezone.now())
```

This creates a natural workflow:
1. Record note with follow-up date
2. Follow-up date arrives, appears on home page
3. Staff records new note for client
4. Old follow-up auto-completes

## What We're NOT Building

- **Standalone tasks**: No separate Task model
- **Client assignments**: No "assigned to" field on clients
- **Calendar views**: No week/month calendar display
- **Notifications**: No email/push reminders (use home page)
- **Task assignment to others**: Personal follow-ups only
- **Recurring follow-ups**: One-time only

## UI/UX Notes

### Follow-up Date Field

- Use HTML5 `<input type="date">` for browser native picker
- Position after note content, before save button
- Label: "Follow up by" with helper text "(optional — adds to your home page reminders)"

### Follow-ups Due Section

- Show in Priority Items card alongside Alerts and Needs Attention
- Sort by follow-up date (oldest first)
- Show client name, truncated note text, and date
- Link clicks through to client detail page

### Visual Indicators

- Overdue follow-ups (past date): subtle warning styling
- Due today: normal styling
- Consider showing days overdue: "3 days overdue"

## Testing Checklist

1. [ ] Can create note without follow-up date (existing behaviour preserved)
2. [ ] Can create note with follow-up date
3. [ ] Follow-up appears on home page when date arrives
4. [ ] Follow-up auto-completes when new note recorded for client
5. [ ] Cancelled notes don't show as pending follow-ups
6. [ ] Only author's follow-ups show (not other staff)
7. [ ] Follow-up count accurate in stats card
8. [ ] Date picker works on mobile

## Migration Notes

- Migration is additive (new nullable fields)
- No data migration needed
- Existing notes will have `follow_up_date = NULL` (no follow-up)
- Safe to deploy without downtime

## Future Enhancements (Not This Phase)

If users request more functionality later:
- Manual "mark complete" button (without recording new note)
- View completed follow-ups history
- Filter notes by "has follow-up"
- Follow-up date on client timeline
