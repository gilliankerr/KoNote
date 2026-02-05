# Project Tasks

## Flagged

_Nothing flagged._

## Active Work

### Finish French Experience (v1.0 Requirement)

French-speaking users must feel first-class. See `tasks/multilingual-strategy.md`. System UI, bilingual login, and language switcher are done (Phases 1A–1C).

**Terminology + UX Audit**
- [ ] Complete French defaults for all 24 terminology terms (I18N3)
- [ ] Audit empty states, errors, dates, placeholders for French (I18N4a)
- [ ] Test complete user journey in French (I18N4b)

**Canadian Localization**
- [ ] Postal code accepts both "A1A 1A1" and "A1A1A1" — normalize on save (I18N5)
- [ ] Address labels use "Province or Territory" not "State" (I18N5a)
- [ ] Phone fields accept multiple Canadian formats (I18N5b)
- [ ] Verify date/currency formatting respects language locale (I18N5c)

**i18n Reliability Hardening** — See `tasks/i18n-reliability-plan.md`

_Immediate — DONE:_
- [x] Add `*.mo` to railway.json watchPatterns — 2026-02-05 (I18N-R1)
- [x] Fix SafeLocaleMiddleware canary — now tests "Funder Report Export" — 2026-02-05 (I18N-R2)

_Short-term:_
- [ ] Create `check_translations` management command — verify French at startup/CI (I18N-R3)
- [ ] Add git pre-commit hook — block commits where .po is newer than .mo (I18N-R4)

_Medium-term:_
- [ ] Build template string extraction script — detect untranslated `{% trans %}` strings (I18N-R5)
- [ ] Create `update_translations` wrapper — extract, validate, compile, commit in one step (I18N-R6)

### Individual Client Export — PIPEDA Data Portability

Clients have a legal right to their own data under PIPEDA. Higher priority than elevated export controls.

- [ ] Create single-client export view (EXP2x)
- [ ] Include all client data: info, notes, plans, metrics (EXP2y)
- [ ] Generate PDF format option (EXP2z)
- [ ] Add export button to client detail page (EXP2aa)

### Export Documentation + Cleanup

- [ ] Document SecureExportLink lifecycle — how links are created, expire, get cleaned up (DOC-EXP1)
- [ ] Create export runbook — troubleshooting, cron setup, common issues (DOC-EXP2)
- [ ] Fix `{% trans %}` with HTML in `pdf_unavailable.html` (I18N-EXP2)
- [ ] Wrap `ExportRecipientMixin` strings in `gettext_lazy()` for French (I18N-EXP3)
- [ ] Extract `<strong>` from `{% blocktrans %}` in export/CMT templates (I18N-EXP4)

## Coming Up

### Export Monitoring

Weekly accountability reports for admins. Requires working email configuration.

- [ ] Create weekly export summary email command (EXP2u)
- [ ] Document cron/scheduled task setup in runbook (EXP2w)

### Pre-Launch Checklist

- [ ] Verify email is configured — needed for export notifications and password resets (OPS3)
- [ ] Run full integration test pass — every role, every workflow (TEST3)
- [ ] Test backup restore from a real database dump (OPS4)
- [ ] Verify Railway deployment end-to-end with production-like config (OPS5)

## Roadmap — Future Extensions

### Phase G: Agency Content Translation

Build when agencies have custom programs/metrics they need in multiple languages. See `tasks/multilingual-strategy.md`.

**G.1: Translation Infrastructure**
- [ ] Create TranslatableMixin with `translations` JSONField (I18N10)
- [ ] Add mixin to Program, MetricDefinition, PlanTemplate (I18N11)
- [ ] Create Settings → Translations admin page (I18N12)
- [ ] Update templates to display translated content (I18N13)

**G.2: AI Translation Integration**
- [ ] Create Settings → Integrations page for API keys (I18N14)
- [ ] Add "Suggest translation" button with AI (I18N15)

**G.3: Self-Service Languages**
- [ ] Create Settings → Languages management page (I18N16)
- [ ] Extend translation command for any target language (I18N17)

### Bulk Import

Build after secure export is stable. See `tasks/secure-export-import-plan.md` for design.

- [ ] Create ImportBatch model for tracking (IMP1a)
- [ ] Add import_batch FK to ClientFile model (IMP1b)
- [ ] Create CSV upload form with validation (IMP1c)
- [ ] Implement formula injection sanitisation (IMP1d)
- [ ] Implement duplicate detection (IMP1e)
- [ ] Create preview page showing what will be created (IMP1f)
- [ ] Implement batch import with transaction wrapping (IMP1g)
- [ ] Create rollback functionality — creations only, not updates (IMP1h)
- [ ] Add audit logging for imports (IMP1i)
- [ ] Create import history page for admins (IMP1j)
- [ ] Document import validation rules (DOC-IMP1)

### Other Planned Extensions

- [ ] Field data collection integrations — KoBoToolbox, Forms, or other tools (FIELD1)

### Explicitly Out of Scope

- ~~Calendar/scheduling~~ → Recommend Calendly, Google Calendar, Microsoft Bookings
- ~~Full document storage~~ → Recommend Google Drive, SharePoint, Dropbox
- ~~Offline PWA~~ → Paper forms acceptable; integrations available when needed
- ~~Multi-tenancy~~ → Fork required for coalition implementations

## Parking Lot

### Deployment Workflow Enhancements

- [ ] Create Demo Account Directory page in admin settings (DEMO9)
- [ ] Add `is_demo_context` to audit log entries (DEMO12)

See [deployment workflow design](docs/plans/2026-02-05-deployment-workflow-design.md) for full details.

### Privacy & Security

- [ ] First-run setup wizard — guided initial configuration (SETUP1)
- [ ] GDPR right to erasure UI — note: audit logs must be retained by design (GDPR1)
- [ ] Encrypted search optimisation (search hash field) for 2000+ client lists (PERF1)
- [ ] Bulk operations for discharge, assign (UX17)

## Recently Done

- [x] i18n reliability flags — watchPatterns for .mo files, canary tests project string — 2026-02-05 (I18N-R1, I18N-R2)
- [x] Phase 4: Elevated export controls — is_elevated flag, 10-min delay, admin email notifications, pending revocation — 2026-02-05 (EXP2q-t)
- [x] Fix French translations not loading — add missing LOCALE_PATHS + fix EN/FR switcher styling — 2026-02-05 (I18N-FIX1)
- [x] Export permission alignment — PM scoped exports, creator downloads, 35 tests, role matrix docs — 2026-02-05 (PERM1-10)
- [x] Secure export foundation complete — security bug fix, audit logging, warnings, secure links, revocation — 2026-02-05 (EXP0a-p)
- [x] Multilingual Phases 1A–1C — 636 French translations, bilingual login, [EN|FR] toggle — 2026-02-05 (I18N1-2b)
- [x] Harden seed system — remove fragile guard, deduplicate data, add warnings — 2026-02-05 (SEED1)
- [x] Progress note encryption + MFA documentation — 2026-02-05 (SEC1, SEC2)
- [x] Deployment Workflow Phase 1 — demo/real data separation — 2026-02-05 (DEMO1-8)

_Older completed tasks moved to [tasks/ARCHIVE.md](tasks/ARCHIVE.md)._

---

## What's Been Built (Reference)

For detailed history, see `tasks/ARCHIVE.md`. Summary of completed work:

| Area | What's Done |
|------|-------------|
| **Core app (Phases 1–8)** | Clients, plans, notes, events, charts, admin, security, UX |
| **Secure export** | Bug fix, audit logging, warnings, secure links, permission alignment |
| **French** | 636 system strings translated, bilingual login, language switcher |
| **Reporting** | Funder reports, aggregation, demographics, fiscal year, PDF exports |
| **Documentation** | Getting started, security ops, deployment guides (Azure, Railway, Elest.io) |
| **Registration** | Self-service public forms with duplicate detection and capacity limits |
| **Accessibility** | WCAG 2.2 AA — semantic HTML, colour contrast, aria attributes |
| **Roadmap A–F** | Market access, funder reporting, docs, registration, staff productivity — all complete |
