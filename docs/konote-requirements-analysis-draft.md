# KoNote
## Requirements Analysis & Platform Comparison
**February 2026**
**Gillian Kerr and Sophie Llewelyn**

---

# 1. Understanding Your Needs

We listened carefully to your feedback and translated your notes into a structured requirements analysis. This document maps each requirement to KoNote's current or planned capabilities and compares KoNote to Monday.com as an alternative platform.

| # | Requirement | Priority | KoNote Status |
|---|-------------|----------|---------------|
| 1 | **Simplified workflow for coaches -- less clicking, less bureaucratic feel** | **Core** | Available now -- redesigned participant page with single Actions menu, Quick Notes for fast contact logging, streamlined navigation with History tab |
| 2 | **Longitudinal outcome data -- number of sessions, changes since session X, trends over time** | **Core** | Available now -- outcome tracking with Chart.js visualisation is KoNote's core feature |
| 3 | **Coach planning and goal-setting space -- somewhere to capture plans collaboratively with participants** | **Core** | Available now -- outcomes with measurable indicators, progress notes with narrative |
| 4 | **Referral source tracking -- where the person came from** | **Core** | Available now -- referral source field on client intake |
| 5 | **Appointment and visit tracking -- future visits saved in the database** | **Core** | Available now -- native meeting model with status tracking (scheduled, completed, cancelled, no-show), accessible date/time picker, calendar feed for Outlook/Google |
| 6 | **Usable reporting out of the box -- no Power BI needed** | **Core** | Available now -- built-in outcome visualisation, funder reporting templates with preview, contact outcome breakdowns, exportable data with clear privacy notices |
| 7 | **Data sovereignty -- all data stays in Canada** | **Core** | Available now -- self-hosted on Canadian infrastructure (Fullhost.com or equivalent). You control where your data lives. |
| 8 | **Two-way email within the progress timeline** | **High** | In development -- coaches can compose and send email from within KoNote with CASL consent enforcement, preview step, and audit logging. Inbound email capture is planned. |
| 9 | **Participant portal -- clients can input their own data** | **Medium** | Available now -- separate secure login with MFA, goal and progress views, private journal, messaging to staff, pre-session discussion prompts, correction requests (PIPEDA), emergency logout, and consent onboarding flow |
| 10 | **SMS communication -- send and receive texts with participants** | **Medium** | Planned module -- appointment reminders and notifications. Canadian provider option available (Swift SMS Gateway). |
| 11 | **Surveys -- collect structured feedback from participants** | **Medium** | Future consideration -- could be built as lightweight forms or integrated with an external survey tool |
| 12 | **Financial coaching workflow** | **Nice-to-have** | KoNote's outcome and progress note system is flexible enough to support financial coaching workflows without custom development |
| 13 | **Affordable to maintain and update** | **Implicit** | Open source, no per-seat licensing, no vendor lock-in. Hosting cost only. |

9 of 13 requirements are available today. 1 is in active development. The remaining 3 are planned modules or future considerations -- none require fundamental changes to KoNote's architecture.

# 2. Key Platform Features

This section describes what KoNote does today, so you can assess whether it fits your needs.

## Participant Page Design

Each participant has a single page with everything a coach needs:

- **Single Actions menu** -- all actions (Quick Note, Detailed Note, Record Event, New Alert, Schedule Meeting) are accessible from one "+ New" dropdown
- **History tab** -- a chronological read-only review of all interactions (notes, contacts, meetings, alerts) in one place
- **Expandable note preview** -- coaches can preview note content directly in the History tab without navigating away
- **Mobile-friendly navigation** -- filled active-tab indicators, sticky tabs on mobile, and auto-scroll to the active tab

## Contact Logging with Outcome Tracking

Phone calls, texts, and visits are logged as Quick Notes with contact outcome tracking (Reached, Left Message, No Answer, Voicemail, Wrong Number). Contact outcomes feed directly into funder reports, so day-to-day recording and reporting requirements are handled in a single workflow.

## Email with CASL Compliance

Coaches can compose and send email directly from a participant's record. The system enforces CASL (Canada's Anti-Spam Legislation) consent checks before allowing any email to be sent, includes a preview step so coaches can review before sending, and logs every email action in the audit trail. Emails are sent from the coach's real email address through the organisation's existing Microsoft 365 or Google Workspace.

## Accessible Meeting Scheduling

Meeting scheduling uses a custom chip-based date and time picker designed to meet WCAG 2.2 AA standards. Coaches select a date, then pick from time-slot chips rather than typing into small input fields -- significantly easier on mobile devices.

## Program Manager Admin Access

Program Managers have scoped access to administrative features without needing a full administrator account. PMs can manage:

- Team members within their programs
- Plan and note templates
- Event types and metric definitions
- Registration links

All access is scoped to the PM's own programs. An elevation constraint prevents PMs from creating administrator accounts or assigning PM/executive roles, closing a potential privilege escalation path.

## Report Templates

Report templates let managers define which metrics to include in funder reports. Managers can preview what each template contains before selecting one for export. Export pages clearly list exactly which data columns are included and explicitly state that participant names, contact information, addresses, and session notes are never included.

## Participant Portal

Participants have their own secure portal, entirely separate from the staff interface:

- **Secure authentication** -- email and password login with TOTP-based multi-factor authentication, account lockout after failed attempts, and session fixation protection
- **Emergency logout** -- a panic/safety button that instantly clears the session, designed for participants in sensitive situations (e.g., domestic violence)
- **Consent onboarding** -- a multi-screen consent flow (privacy, data use, your rights) with tracked acknowledgements before accessing any data
- **My Goals** -- participants see their active goals and progress charts with plain-language descriptions, using only metrics the agency has marked as portal-visible
- **Milestones** -- a view of completed goals
- **Private journal** -- participants can write journal entries (encrypted at rest), optionally linked to specific goals, with a one-time privacy disclosure explaining who can see them
- **Message to My Worker** -- send general messages or pre-session discussion prompts ("What I want to discuss next time") that appear in the staff interface
- **Correction requests** -- participants can formally request corrections to their recorded information, as required under PIPEDA and PHIPA. Requests go through a soft step encouraging direct conversation first.
- **Bilingual** -- the portal respects the participant's preferred language (English or French)
- **Staff portal notes** -- staff can leave encouragement or updates visible to the participant in the portal
- **Invite system** -- staff generate a secure invite link with an optional verbal verification code for in-person onboarding

All portal data is Fernet-encrypted at rest. Email addresses are additionally HMAC-hashed for constant-time lookup without exposing plaintext. The portal is gated behind a feature toggle so agencies can enable it when they are ready.

## Bilingual Interface (English and French)

The entire KoNote interface is available in both English and French. This includes two layers of translation:

- **System interface** -- all menus, buttons, labels, error messages, and help text are translated. The interface language follows each user's preference setting.
- **Agency-created content** -- when administrators create metric definitions, plan templates, note templates, event types, or terminology overrides, each item has a French translation field. Administrators enter the French version alongside the English, so participants and staff who work in French see translated content throughout -- not just the system chrome, but the actual clinical and program terminology their agency uses.
- **Participant communications** -- emails and portal content are delivered in the participant's preferred language.
- **Customisable terminology** -- agencies can override default terms (e.g., "participant" vs. "client" vs. "member") in both English and French to match their organisational language.

## Alert System

Staff can raise alerts about participants (e.g., safety concerns, missed sessions). The alert creation page shows staff who will read the alert, provides tips for writing effective alerts, and notes that alerts cannot be edited after submission -- they can only be cancelled through a two-person review process. The recommendation review page gives Program Managers clear framing, consequence callouts, and accessible form labels for approving or rejecting alert recommendations.

# 3. KoNote vs. Monday.com

Monday.com is a general-purpose work management platform designed for project tracking, automations, and team collaboration. KoNote is a purpose-built participant outcome management system. They solve different problems, and the right choice depends on what the organisation actually needs.

| Dimension | KoNote | Monday.com |
|-----------|--------|------------|
| **Purpose** | Participant outcome management for nonprofits | General work management adapted to any use case |
| **Data sovereignty** | Self-hosted in Canada -- you choose the hosting provider | US-based company. Canadian data residency requires Enterprise tier and does not cover all data types. |
| **PII security** | Field-level Fernet (AES) encryption, separate audit database, PIPEDA-aware design | Standard SaaS encryption. No field-level encryption. |
| **Cost** | Hosting only -- approximately $20-50 CAD/month. No per-seat licensing. | $16-32 CAD/seat/month. Ten coaches = $160-320/month. Enterprise features cost more. |
| **Simplicity** | Fewer features, purpose-built interface. Less to learn, but also less to work with if needs expand. | Feature-rich -- boards, automations, integrations, views. More training needed, but more flexible for general use. |
| **Reporting** | Built-in outcome visualisation, funder report templates, contact outcome breakdowns. No Power BI needed. | Would require custom dashboard configuration or export to Power BI. |
| **Customisation** | Source code available -- any feature can be changed, but requires a developer. PMs can configure templates and metrics within the interface. | No-code configuration through the interface and marketplace. Much easier for non-technical staff to customise. |
| **Coach experience** | Designed around coach-participant relationships -- notes, outcomes, contact logging, meetings | Designed around project management. Case management would use boards or tables. |
| **Participant portal** | Available -- separate secure login with MFA, goals, journal, messaging, correction requests | Not a core feature. Monday.com is designed for internal teams. |
| **Email integration** | In development -- compose email with CASL consent enforcement and audit logging. Inbound capture not yet built. | Has email integrations tied to board items. |
| **Bilingual support** | Full English/French interface including agency-created content. | Interface available in French. No built-in bilingual communication workflows. |
| **Accessibility** | WCAG 2.2 AA target. Custom accessible components. | Monday.com's VPAT indicates partial WCAG 2.1 AA conformance with known gaps. |
| **Ecosystem** | No marketplace. Integrations require development work. | Large marketplace with hundreds of integrations (Slack, Zoom, Google, etc.). |
| **Mobile** | Responsive web app -- works on phones but no native app. | Native iOS and Android apps. |
| **Support** | Small team. No SLA. Community and developer support. | Paid support team, documentation, community forums. |
| **Track record** | Early-stage product, limited production deployments. | Publicly traded company, millions of users, established since 2012. |

# 4. KoNote Limitations and Trade-offs

It is worth being direct about where KoNote is not the stronger option.

- **Small team.** KoNote is maintained by a small team, not a company with dedicated support staff. There is no SLA, no 24/7 help desk, and no account manager. If something breaks on a Friday evening, you are relying on the developers' availability.
- **Self-hosting means self-management.** Someone at (or contracted by) the agency needs to manage hosting, apply updates, run backups, and handle SSL certificates. This is not difficult with Docker, but it is a responsibility that Monday.com handles for you.
- **No marketplace or integrations ecosystem.** Monday.com has hundreds of pre-built integrations (Slack, Zoom, Google Workspace, etc.). KoNote has none. Any integration requires development work.
- **No native mobile app.** KoNote is a responsive web app that works on phones, but it does not have a native iOS or Android app. Monday.com does.
- **Encrypted fields cannot be searched in SQL.** Client search loads accessible records into Python and filters in memory. This works well up to approximately 2,000 clients. Beyond that, a different approach would be needed.
- **Early-stage product.** KoNote has limited production deployments. Monday.com has been running since 2012 with millions of users. That matters for risk assessment.
- **Customisation requires a developer.** Monday.com lets non-technical staff customise boards, automations, and workflows through the interface. KoNote's admin interface covers templates and metrics, but deeper changes require someone comfortable with code.
- **No workflow automation.** Monday.com can trigger actions automatically (e.g., "when status changes, send a notification"). KoNote does not have a general automation engine.

If your organisation needs strong project management features alongside case management, or if staff need to customise workflows without developer involvement, Monday.com may be a better fit. KoNote's advantage is narrow and specific: it is built for the coach-participant relationship, with privacy and accessibility as primary concerns rather than afterthoughts.

# 5. Data Sovereignty

Data sovereignty means your organisation controls where participant data is stored and who can access it. For nonprofits serving vulnerable populations, this is a legal and ethical obligation under PIPEDA and Ontario's privacy framework.

## KoNote

KoNote is self-hosted using Docker containers. You choose the hosting provider. For Canadian data sovereignty, we recommend Fullhost.com (based in Ontario) or any PIPEDA-compliant Canadian hosting provider. Your data never leaves Canadian infrastructure. You hold the encryption keys.

The trade-off is that self-hosting places the operational responsibility on the agency (see Limitations above).

## Monday.com

Monday.com is a US-based SaaS platform (publicly traded on NASDAQ). They offer data residency options, but these are limited to Enterprise-tier pricing and do not cover all data types. Metadata, search indexes, and AI features may process data outside Canada.

Under the US CLOUD Act, US authorities can compel disclosure of data held by US companies regardless of where the data is physically stored. For organisations serving participants in sensitive situations (mental health, addiction, domestic violence, immigration), this is worth discussing with your privacy officer. Whether it is an acceptable risk depends on your context.

## Email and SMS Considerations

When KoNote sends an email through Microsoft 365 or Google Workspace, the email travels through your existing email infrastructure -- the same system your staff already uses daily. For Canadian Microsoft 365 and Google Workspace tenants, data residency is honoured within Canada.

SMS is different. Text messages travel through telecom carrier networks and are stored by the SMS provider. Currently, most SMS API providers (including Twilio, the industry standard) are US-based. There is one Canadian option -- Swift SMS Gateway, based in Canada with data stored in Canadian data centres. KoNote can integrate with either. We recommend discussing SMS data sovereignty requirements with your privacy officer before enabling SMS features.

# 6. Communication Modules

Each communication channel (email, appointments, SMS) is an optional module that can be enabled independently. This section describes each one, including costs and confidentiality implications.

| Module | External Dependency | Cost to Agency | Confidentiality Risk |
|--------|-------------------|----------------|---------------------|
| **Email Integration** | Your existing Microsoft 365 or Google Workspace | $0 (uses existing subscription) | Low -- encrypted in transit, stays in your email system |
| **Appointment Tracking** | None | $0 | None -- data stays entirely within KoNote |
| **SMS Notifications** | Swift SMS Gateway (Canadian) or Twilio (US-based) | $15-50 CAD/month | High -- unencrypted in transit, visible on device |

## Email Integration

This module connects KoNote to your existing Microsoft 365 or Google Workspace account. Coaches can compose and send emails from within KoNote with a preview step, and all correspondence appears in the participant's History tab alongside progress notes and outcome measurements. The system enforces CASL consent before any email is sent and logs every action in the audit trail.

Emails are sent from the coach's real email address (or a shared mailbox like reminders@yourorg.ca). Inbound email capture -- where replies from participants are automatically linked to their record -- is planned for a future release. The coach's Outlook or Gmail also retains a copy -- there is no shadow communication channel.

- Technical requirements: your Microsoft 365 or Google Workspace administrator grants KoNote permission to send email on behalf of designated accounts. This is a one-time setup.
- Cost: no additional cost -- uses your existing email subscription.
- Confidentiality: emails travel through your existing email infrastructure and are encrypted in transit by your email provider.
- Data sovereignty: same as your current email -- for Canadian tenants, data stays in Canada.

## Appointment Tracking

This module adds meeting records to each participant: date, time, location, status (scheduled, completed, cancelled, no-show), and which coach is assigned. Scheduling uses an accessible chip-based date and time picker designed for ease of use on both desktop and mobile devices.

Coaches can see their upcoming appointments on a dashboard and on each participant's page. An "Add to Calendar" button generates a standard .ics file that can be opened in Outlook, Google Calendar, or Apple Calendar. Optionally, KoNote can provide a private calendar feed URL that syncs meetings to the coach's calendar automatically (read-only, refreshed periodically, containing initials and record IDs only -- no personally identifiable information).

- Cost: no additional cost. No external service required.
- Confidentiality: appointment data stays entirely within KoNote. Calendar feeds contain only initials and record identifiers, never names or contact information.

## SMS Notifications

This module enables outbound text message reminders for appointments. Messages are short, contain no personally identifiable information, and include an opt-out instruction as required by CASL (Canada's Anti-Spam Legislation).

Requires a third-party SMS provider:

- **Canadian option:** Swift SMS Gateway -- data stays in Canada.
- **US-based option:** Twilio -- industry standard, lower cost, but data transits US infrastructure.
- **Estimated cost:** $15-50 CAD/month depending on volume. Per-message cost is approximately 1-5 cents.

**Confidentiality considerations:** SMS messages are not encrypted in transit -- the telecom carrier and SMS provider can read them. Messages appear on the participant's phone lock screen and are visible to anyone with physical access to the device. If a participant shares a phone (common in low-income households), other household members will see the messages. The sender display name should be generic (e.g., "Appt Reminder") rather than the organisation name for agencies providing sensitive services.

**Consent:** KoNote enforces explicit consent before sending any SMS. Consent is tracked with dates and audit logging for CASL compliance.

# 7. Scope

KoNote is a participant outcome management system. It is not a CRM, not a project management tool, not a full calendaring system, and not a communication platform.

The communication modules described above exist to reduce the number of tools a coach has open at once and to create a single record of the coach-participant relationship. If your organisation needs marketing automation, complex project workflows, or enterprise resource planning, those are separate tools -- KoNote can coexist alongside them.

# 8. Security Summary

| Feature | Detail |
|---------|--------|
| **Field-level encryption** | All personally identifiable information (names, phone numbers, email addresses, notes) encrypted with Fernet (AES-128) at rest |
| **Separate audit database** | Every access and change is logged to an isolated database that cannot be tampered with from the main application |
| **Role-based access control** | Four roles with scoped permissions: Staff see only participants in their assigned programs. Program Managers see their programs and can configure templates, metrics, and team members within their scope. Administrators see everything. Front Desk staff see contact information only. Elevation constraints prevent privilege escalation. |
| **Authentication** | Azure AD single sign-on (primary) or local accounts with Argon2 password hashing. Multi-factor authentication planned. |
| **CASL compliance** | Email sending enforces explicit consent checks with audit-logged consent dates. SMS consent tracked separately. |
| **Data erasure** | PIPEDA-compliant data erasure workflow with tiered approach (immediate, scheduled, complete) and audit trail |
| **Export privacy** | Report exports clearly list included columns and explicitly exclude PII. Confirmation dialogs for sensitive exports. |
| **Session security** | Secure cookies, CSRF protection, session timeout, concurrent session management |
| **Canadian hosting** | Self-hosted on Canadian infrastructure. You hold the encryption keys. |
| **Open source** | Full source code available for security review by your IT advisor or privacy officer |

# 9. Next Steps

1. Review this document and let us know if we have captured your requirements accurately.
2. If you would like to see KoNote in action, we can arrange a walkthrough of the current features.
3. If KoNote looks like a fit, we can discuss hosting options and timeline.
4. If Monday.com looks like a better fit for your needs, that is a perfectly reasonable conclusion -- and we are happy to help you think through the data sovereignty and privacy implications of that choice.
