/* KoNote Web — minimal vanilla JS for interactions */

// Enable script execution in HTMX 2.0 swapped content (needed for Chart.js in Analysis tab)
// This must be set before any HTMX swaps occur
htmx.config.allowScriptTags = true;

// Tell HTMX to use the loading bar as a global indicator
document.body.setAttribute("hx-indicator", "#loading-bar");

// HTMX configuration
document.body.addEventListener("htmx:configRequest", function (event) {
    // Include CSRF token in HTMX requests
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
    if (csrfToken) {
        event.detail.headers["X-CSRFToken"] = csrfToken.value;
    }
});

// --- Auto-dismiss success messages after 3 seconds ---
// Error messages stay visible until manually dismissed
(function () {
    var AUTO_DISMISS_DELAY = 3000; // 3 seconds
    var FADE_DURATION = 300; // matches CSS animation

    // Check if user prefers reduced motion
    function prefersReducedMotion() {
        return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    // Dismiss a message with fade-out animation
    function dismissMessage(messageEl) {
        if (prefersReducedMotion()) {
            // Immediate removal for reduced motion preference
            messageEl.remove();
        } else {
            // Add fading class, then remove after animation completes
            messageEl.classList.add("fading-out");
            setTimeout(function () {
                messageEl.remove();
            }, FADE_DURATION);
        }
    }

    // Add close button to a message element
    function addCloseButton(messageEl) {
        var closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.className = "message-close";
        closeBtn.setAttribute("aria-label", "Dismiss message");
        closeBtn.innerHTML = "&times;";
        closeBtn.addEventListener("click", function () {
            dismissMessage(messageEl);
        });
        messageEl.style.position = "relative";
        messageEl.appendChild(closeBtn);
    }

    // Set up auto-dismiss for success messages
    function setupAutoDismiss() {
        var messages = document.querySelectorAll("article[aria-label='notification']");
        messages.forEach(function (msg) {
            // Add close button to all messages
            addCloseButton(msg);

            // Check if this is a success message (auto-dismiss)
            // Django message tags: debug, info, success, warning, error
            var isSuccess = msg.classList.contains("success");
            var isError = msg.classList.contains("error") || msg.classList.contains("danger") || msg.classList.contains("warning");

            if (isSuccess && !isError) {
                // Auto-dismiss success messages after delay
                setTimeout(function () {
                    // Only dismiss if still in DOM (user might have manually closed it)
                    if (msg.parentNode) {
                        dismissMessage(msg);
                    }
                }, AUTO_DISMISS_DELAY);
            }
            // Error/warning messages stay until manually dismissed
        });
    }

    // Run on page load
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setupAutoDismiss);
    } else {
        setupAutoDismiss();
    }

    // Also run after HTMX swaps (in case messages are loaded dynamically)
    document.body.addEventListener("htmx:afterSwap", function (event) {
        // Only process if the swapped content might contain messages
        var newMessages = event.detail.target.querySelectorAll("article[aria-label='notification']");
        if (newMessages.length > 0) {
            setupAutoDismiss();
        }
    });
})();

// --- Toast helper ---
function showToast(message, isError) {
    var toast = document.getElementById("htmx-error-toast");
    if (toast) {
        var msgEl = document.getElementById("htmx-error-toast-message");
        if (msgEl) {
            msgEl.textContent = message;
        } else {
            toast.textContent = message;
        }
        toast.hidden = false;
        // Only auto-dismiss non-error messages
        if (!isError) {
            setTimeout(function () { toast.hidden = true; }, 3000);
        }
    } else {
        alert(message);
    }
}

// Close button on toast
document.addEventListener("click", function (event) {
    if (event.target && event.target.id === "htmx-error-toast-close") {
        var toast = document.getElementById("htmx-error-toast");
        if (toast) { toast.hidden = true; }
    }
});

// Global HTMX error handler — show user-friendly message on network/server errors
document.body.addEventListener("htmx:responseError", function (event) {
    var status = event.detail.xhr ? event.detail.xhr.status : 0;
    var message = "Something went wrong. Please try again.";
    if (status === 403) {
        message = "You don't have permission to do that.";
    } else if (status === 404) {
        message = "The requested item was not found.";
    } else if (status >= 500) {
        message = "A server error occurred. Please try again later.";
    } else if (status === 0) {
        message = "Could not connect to the server. Check your internet connection.";
    }
    showToast(message, true);
});

// Handle HTMX send errors (network failures before response)
document.body.addEventListener("htmx:sendError", function () {
    showToast("Could not connect to the server. Check your internet connection.", true);
});

// --- Select All / Deselect All for metric checkboxes (export form) ---
document.addEventListener("click", function (event) {
    var target = event.target;
    if (target.id === "select-all-metrics" || target.id === "deselect-all-metrics") {
        event.preventDefault();
        var checked = target.id === "select-all-metrics";
        var fieldset = target.closest("fieldset");
        if (fieldset) {
            var checkboxes = fieldset.querySelectorAll("input[type='checkbox']");
            checkboxes.forEach(function (cb) { cb.checked = checked; });
        }
    }
});

// --- Mobile navigation toggle ---
(function () {
    function setupMobileNav() {
        var navToggle = document.getElementById("nav-toggle");
        var navMenu = document.getElementById("nav-menu");

        if (!navToggle || !navMenu) return;

        navToggle.addEventListener("click", function () {
            var isOpen = navMenu.classList.toggle("nav-open");
            navToggle.setAttribute("aria-expanded", isOpen);
        });

        // Close menu when clicking outside
        document.addEventListener("click", function (event) {
            var nav = document.querySelector("body > nav");
            if (nav && !nav.contains(event.target) && navMenu.classList.contains("nav-open")) {
                navMenu.classList.remove("nav-open");
                navToggle.setAttribute("aria-expanded", "false");
            }
        });

        // Close menu when window is resized above mobile breakpoint
        window.addEventListener("resize", function () {
            if (window.innerWidth > 768 && navMenu.classList.contains("nav-open")) {
                navMenu.classList.remove("nav-open");
                navToggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setupMobileNav);
    } else {
        setupMobileNav();
    }
})();

// --- Note Auto-Save / Draft Recovery ---
// Saves form data to localStorage as user types, restores on page load
(function () {
    var AUTOSAVE_DELAY = 1000; // Save 1 second after user stops typing
    var STORAGE_PREFIX = "konote_draft_";

    // Debounce helper
    function debounce(fn, delay) {
        var timer = null;
        return function () {
            var context = this;
            var args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () {
                fn.apply(context, args);
            }, delay);
        };
    }

    // Get storage key for a form
    function getStorageKey(form) {
        var clientId = form.getAttribute("data-client-id");
        var formType = form.getAttribute("data-form-type") || "note";
        if (!clientId) return null;
        return STORAGE_PREFIX + formType + "_" + clientId;
    }

    // Collect form data into an object
    function collectFormData(form) {
        var data = {};
        var inputs = form.querySelectorAll("input, textarea, select");
        inputs.forEach(function (el) {
            // Skip CSRF token, submit buttons, and consent checkbox
            if (el.name === "csrfmiddlewaretoken" || el.type === "submit") return;
            if (el.name === "consent_confirmed") return; // Don't save consent - must be re-confirmed

            if (el.type === "checkbox") {
                // For checkboxes, store checked state with unique key
                var key = el.name || el.getAttribute("data-target-id");
                if (el.classList.contains("target-selector")) {
                    key = "target_selector_" + el.getAttribute("data-target-id");
                }
                data[key] = el.checked;
            } else if (el.type === "radio") {
                if (el.checked) {
                    data[el.name] = el.value;
                }
            } else {
                data[el.name] = el.value;
            }
        });
        return data;
    }

    // Restore form data from saved object
    function restoreFormData(form, data) {
        var inputs = form.querySelectorAll("input, textarea, select");
        inputs.forEach(function (el) {
            if (el.name === "csrfmiddlewaretoken" || el.type === "submit") return;
            if (el.name === "consent_confirmed") return;

            if (el.type === "checkbox") {
                var key = el.name || el.getAttribute("data-target-id");
                if (el.classList.contains("target-selector")) {
                    key = "target_selector_" + el.getAttribute("data-target-id");
                }
                if (data.hasOwnProperty(key)) {
                    el.checked = data[key];
                    // Trigger change event for target selectors to show/hide details
                    if (el.classList.contains("target-selector")) {
                        el.dispatchEvent(new Event("change"));
                    }
                }
            } else if (el.type === "radio") {
                if (data[el.name] === el.value) {
                    el.checked = true;
                }
            } else if (data.hasOwnProperty(el.name)) {
                el.value = data[el.name];
            }
        });
    }

    // Check if form data has meaningful content worth saving
    function hasContent(data) {
        for (var key in data) {
            if (!data.hasOwnProperty(key)) continue;
            var val = data[key];
            // Check for non-empty text values (ignore dates/dropdowns set to defaults)
            if (typeof val === "string" && val.trim() !== "" && key !== "session_date" && key !== "template") {
                return true;
            }
            // Check for checked target selectors
            if (key.startsWith("target_selector_") && val === true) {
                return true;
            }
        }
        return false;
    }

    // Save draft to localStorage
    function saveDraft(form) {
        var key = getStorageKey(form);
        if (!key) return;

        var data = collectFormData(form);
        if (hasContent(data)) {
            data._savedAt = new Date().toISOString();
            try {
                localStorage.setItem(key, JSON.stringify(data));
            } catch (e) {
                // localStorage might be full or disabled - fail silently
                console.warn("Could not save draft:", e);
            }
        }
    }

    // Load draft from localStorage
    function loadDraft(form) {
        var key = getStorageKey(form);
        if (!key) return null;

        try {
            var stored = localStorage.getItem(key);
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (e) {
            console.warn("Could not load draft:", e);
        }
        return null;
    }

    // Clear draft from localStorage
    function clearDraft(form) {
        var key = getStorageKey(form);
        if (!key) return;
        try {
            localStorage.removeItem(key);
        } catch (e) {
            // Ignore errors
        }
    }

    // Format saved time for display
    function formatSavedTime(isoString) {
        try {
            var date = new Date(isoString);
            var now = new Date();
            var diffMs = now - date;
            var diffMins = Math.floor(diffMs / 60000);

            if (diffMins < 1) return "just now";
            if (diffMins === 1) return "1 minute ago";
            if (diffMins < 60) return diffMins + " minutes ago";

            var diffHours = Math.floor(diffMins / 60);
            if (diffHours === 1) return "1 hour ago";
            if (diffHours < 24) return diffHours + " hours ago";

            // Show date for older drafts
            return date.toLocaleDateString();
        } catch (e) {
            return "earlier";
        }
    }

    // Create and show the draft recovery banner
    function showRecoveryBanner(form, draft) {
        var savedTime = draft._savedAt ? formatSavedTime(draft._savedAt) : "earlier";

        var banner = document.createElement("article");
        banner.className = "draft-recovery-banner";
        banner.setAttribute("role", "alert");
        banner.innerHTML =
            '<p><strong>Draft found</strong> — You have unsaved work from ' + savedTime + '.</p>' +
            '<div role="group">' +
            '<button type="button" class="draft-restore">Restore draft</button>' +
            '<button type="button" class="draft-discard outline secondary">Discard</button>' +
            '</div>';

        // Insert banner before the form
        form.parentNode.insertBefore(banner, form);

        // Handle restore
        banner.querySelector(".draft-restore").addEventListener("click", function () {
            restoreFormData(form, draft);
            banner.remove();
            showToast("Draft restored", false);
        });

        // Handle discard
        banner.querySelector(".draft-discard").addEventListener("click", function () {
            clearDraft(form);
            banner.remove();
        });
    }

    // Initialize auto-save on a form
    function initAutoSave(form) {
        var key = getStorageKey(form);
        if (!key) return; // Form doesn't have required data attributes

        // Check for existing draft and show recovery banner
        var draft = loadDraft(form);
        if (draft && hasContent(draft)) {
            showRecoveryBanner(form, draft);
        }

        // Set up auto-save on input
        var debouncedSave = debounce(function () {
            saveDraft(form);
        }, AUTOSAVE_DELAY);

        form.addEventListener("input", debouncedSave);
        form.addEventListener("change", debouncedSave);

        // Clear draft on successful form submission
        form.addEventListener("submit", function () {
            clearDraft(form);
        });
    }

    // Find and initialize all auto-save forms
    function setupAutoSave() {
        var forms = document.querySelectorAll("form[data-autosave]");
        forms.forEach(initAutoSave);
    }

    // Run on page load
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setupAutoSave);
    } else {
        setupAutoSave();
    }
})();
