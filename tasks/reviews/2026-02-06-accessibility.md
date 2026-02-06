# Accessibility Review Report: KoNote2

**Date:** 2026-02-06
**Reviewer:** Jules (WCAG 2.2 AA Specialist)
**Scope:** Templates, CSS, and JS for KoNote2 Application
**Standard:** WCAG 2.2 Level AA

---

### Summary

| Category | Issues Found | Critical | High | Medium | Low |
|----------|-------------|----------|------|--------|-----|
| Perceivable | 2 | 1 | 0 | 1 | 0 |
| Operable | 2 | 0 | 1 | 1 | 0 |
| Understandable | 2 | 0 | 0 | 1 | 1 |
| Robust | 1 | 0 | 0 | 0 | 1 |
| **Total** | **7** | **1** | **1** | **3** | **2** |

**WCAG 2.2 AA Compliant:** **With Fixes**

The application has a strong accessibility foundation with semantic HTML, visible focus indicators, and skip links. However, critical issues exist in dynamic content (charts) and time-based events (session timeout).

---

### Findings

#### **[CRITICAL-001] Missing Text Alternative for Charts**
- **WCAG Criterion:** 1.1.1 Non-text Content (Level A)
- **Location:** `templates/reports/_tab_analysis.html` (Chart.js implementation)
- **Issue:** The outcome analysis charts use a `<canvas>` element with an `aria-label` that summarizes the chart (e.g., "Line chart showing..."). However, the actual data points and trends are not available to screen reader users. The `aria-label` alone is insufficient for complex data.
- **Impact:** Blind users cannot access the client progress data contained in the charts.
- **Fix:** Add a visually hidden `<table>` (using `class="visually-hidden-focusable"` or similar) or a visible `details` element containing the raw data points (date and value) for each chart.
- **Test:** Use a screen reader to verify that data points can be navigated, or inspect the DOM to ensure a data table exists.

#### **[HIGH-001] Session Timeout Warning is Visual Only**
- **WCAG Criterion:** 2.2.1 Timing Adjustable (Level A) / 4.1.3 Status Messages (Level AA)
- **Location:** `static/js/app.js` (Session Timer section)
- **Issue:** The session timer updates a visual counter and adds CSS classes (`warning`, `critical`). It does not announce the impending timeout to screen readers via `aria-live` regions, nor does it offer a mechanism to extend the session via the keyboard before logout.
- **Impact:** Screen reader users may be unexpectedly logged out while working on long notes, losing data.
- **Fix:**
    1. Wrap the countdown text in an `aria-live="polite"` region (switching to "assertive" when critical).
    2. Implement a modal dialog that appears 2 minutes before timeout, trapping focus and offering an "Extend Session" button.
- **Test:** Wait for the timeout threshold and verify screen reader announcement.

#### **[MEDIUM-001] Incorrect ARIA Role on Data Table**
- **WCAG Criterion:** 4.1.2 Name, Role, Value (Level A)
- **Location:** `templates/clients/_client_list_table.html`
- **Issue:** The client list table uses `role="grid"`. In ARIA, a grid implies an interactive widget with two-dimensional keyboard navigation (arrow keys moving focus between cells). The current implementation is a static table.
- **Impact:** Screen reader users may expect keyboard interactivity that doesn't exist, or their navigation shortcuts for standard tables may be intercepted.
- **Fix:** Remove `role="grid"` and allow the native `<table>` semantics to function. If a role is needed for styling hooks, use `role="table"`.
- **Test:** Inspect HTML or use Accessibility Tree viewer.

#### **[MEDIUM-002] Form Errors Lack Programmatic Association**
- **WCAG Criterion:** 1.3.1 Info and Relationships (Level A) / 3.3.1 Error Identification (Level A)
- **Location:** `templates/notes/note_form.html` (and other forms)
- **Issue:** While error messages use `role="alert"`, the input fields are not explicitly associated with their error messages using `aria-describedby`.
- **Impact:** A screen reader user navigating to an input field might not hear the associated error message immediately.
- **Fix:** Ensure that when a form field has an error, the input tag includes `aria-describedby="id-of-error-element"`.
- **Test:** Inspect HTML on a form with validation errors.

#### **[MEDIUM-003] Auto-Dismissing Success Messages**
- **WCAG Criterion:** 2.2.1 Timing Adjustable (Level A)
- **Location:** `static/js/app.js` (`AUTO_DISMISS_DELAY = 3000`)
- **Issue:** Success notifications automatically disappear after 3 seconds.
- **Impact:** Users with reading disabilities or those using screen magnification may miss the message before it vanishes.
- **Fix:** Increase the delay (e.g., to 10 seconds) or remove the auto-dismiss behavior entirely, requiring the user to manually close the notification.
- **Test:** Trigger a success message and time its visibility.

#### **[LOW-001] Missing Consistency in Error Pages**
- **WCAG Criterion:** 3.2.3 Consistent Navigation (Level AA)
- **Location:** `templates/`
- **Issue:** `404.html` (Not Found) and `500.html` (Server Error) templates are missing. The application will fall back to default Django error pages, which likely lack the site's navigation and styling.
- **Impact:** Users encountering errors lose the navigation context and site identity.
- **Fix:** Create `404.html` and `500.html` extending `base.html`.
- **Test:** Force a 404 error and observe the page.

#### **[LOW-002] Autofocus on Login**
- **WCAG Criterion:** 2.4.3 Focus Order (Level A)
- **Location:** `templates/auth/login.html`
- **Issue:** The username field has `autofocus`.
- **Impact:** When the page loads, focus jumps to the input, potentially bypassing the page title and header content for screen reader users.
- **Fix:** Consider removing `autofocus` to respect the natural reading order.
- **Test:** Load the login page and observe initial focus placement.

---

### Testing Notes

**Tools Used:**
- Manual Code Review
- Analysis of Django Templates and JavaScript logic

**Recommended Verification:**
- **axe DevTools:** Run on the "Client Analysis" tab to confirm chart accessibility fixes.
- **Screen Reader:** Test the session timeout workflow with NVDA or VoiceOver.
- **Keyboard:** Verify tab order on the "Note Form" (specifically the participant reflection and sticky footer).
- **High Contrast:** Enable Windows High Contrast Mode to ensure chart data remains visible (since it currently relies on colour for min/max lines).

### Recommendations

1.  **Enhance Keyboard Support for HTMX:** Ensure that when HTMX replaces large chunks of content (like the client list filters), focus is managed appropriately if the user's focus was lost.
2.  **Breadcrumb Accessibility:** In `templates/_breadcrumbs.html`, ensure the visual separator (if any) is hidden from screen readers to reduce noise.
3.  **Language Switching:** The language switcher uses a POST form, which is good for state, but ensure the resulting page load respects the user's focus position if possible.
