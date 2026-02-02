/* KoNote Web — minimal vanilla JS for interactions */

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
    // Show error in a toast-style banner if one exists, otherwise alert
    var toast = document.getElementById("htmx-error-toast");
    if (toast) {
        toast.textContent = message;
        toast.hidden = false;
        setTimeout(function () { toast.hidden = true; }, 6000);
    } else {
        alert(message);
    }
});

// Handle HTMX send errors (network failures before response)
document.body.addEventListener("htmx:sendError", function () {
    var toast = document.getElementById("htmx-error-toast");
    var message = "Could not connect to the server. Check your internet connection.";
    if (toast) {
        toast.textContent = message;
        toast.hidden = false;
        setTimeout(function () { toast.hidden = true; }, 6000);
    } else {
        alert(message);
    }
});
