"""
OpenRouter AI integration — PII-free helper functions.

These functions only receive metadata (metric definitions, target descriptions,
program names, aggregate stats). Client PII never reaches this module.
"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_SECONDS = 30

# Shared safety instruction appended to all system prompts
_SAFETY_FOOTER = (
    "\n\nIMPORTANT: You are a nonprofit outcome-tracking assistant. "
    "Never ask for, guess, or reference any client identifying information "
    "(names, dates of birth, addresses, or record IDs). "
    "Work only with the programme context and metrics provided."
)


def is_ai_available():
    """Return True if the OpenRouter API key is configured."""
    return bool(getattr(settings, "OPENROUTER_API_KEY", ""))


def _call_openrouter(system_prompt, user_message, max_tokens=1024):
    """
    Low-level POST to OpenRouter.  Returns the response text, or None on
    any failure (network, auth, timeout, malformed response).
    """
    if not is_ai_available():
        return None

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": getattr(settings, "OPENROUTER_SITE_URL", ""),
                "X-Title": "KoNote",
            },
            json={
                "model": getattr(settings, "OPENROUTER_MODEL", "anthropic/claude-sonnet-4-20250514"),
                "messages": [
                    {"role": "system", "content": system_prompt + _SAFETY_FOOTER},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": max_tokens,
            },
            timeout=TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        logger.exception("OpenRouter API call failed")
        return None


# ── Public functions ────────────────────────────────────────────────


def suggest_metrics(target_description, metric_catalogue):
    """
    Given a plan target description and the full metric catalogue,
    return a ranked list of suggested metrics.

    Args:
        target_description: str — the staff-written target/goal text
        metric_catalogue: list of dicts with keys id, name, definition, category

    Returns:
        list of dicts {metric_id, name, reason} or None on failure
    """
    system = (
        "You help nonprofit workers choose outcome metrics for client plan targets. "
        "You will receive a target description and a catalogue of available metrics. "
        "Return a JSON array of the 3–5 most relevant metrics, ranked by relevance. "
        "Each item: {\"metric_id\": <int>, \"name\": \"<name>\", \"reason\": \"<1 sentence>\"}. "
        "Return ONLY the JSON array, no other text."
    )
    user_msg = (
        f"Target description: {target_description}\n\n"
        f"Available metrics:\n{json.dumps(metric_catalogue, indent=2)}"
    )
    result = _call_openrouter(system, user_msg)
    if result is None:
        return None
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Could not parse metric suggestions: %s", result[:200])
        return None


def improve_outcome(draft_text):
    """
    Improve a rough outcome statement into a clear, measurable one.

    Args:
        draft_text: str — the staff-written draft outcome

    Returns:
        str — improved outcome text, or None on failure
    """
    system = (
        "You help nonprofit workers write clear, measurable outcome statements "
        "using the SMART framework (Specific, Measurable, Achievable, Relevant, "
        "Time-bound). Rewrite the draft into a professional outcome statement. "
        "Return only the improved text, no explanation."
    )
    return _call_openrouter(system, f"Draft outcome: {draft_text}")


def generate_narrative(program_name, date_range, aggregate_stats):
    """
    Turn aggregate programme metrics into a funder-ready narrative paragraph.

    Args:
        program_name: str
        date_range: str — e.g. "January 2026 – March 2026"
        aggregate_stats: list of dicts {metric_name, average, count, unit}

    Returns:
        str — narrative paragraph, or None on failure
    """
    system = (
        "You write concise, professional funder reports for Canadian nonprofits. "
        "Given a programme name, date range, and aggregated metric data, write a "
        "single paragraph (3–5 sentences) summarising client outcomes. "
        "Use Canadian English spelling (programme, colour, centre). "
        "Do not invent data — only reference the numbers provided."
    )
    user_msg = (
        f"Programme: {program_name}\n"
        f"Period: {date_range}\n\n"
        f"Aggregate metrics:\n{json.dumps(aggregate_stats, indent=2)}"
    )
    return _call_openrouter(system, user_msg, max_tokens=512)


def suggest_note_structure(target_name, target_description, metric_names):
    """
    Suggest a progress note structure for a given plan target.

    Args:
        target_name: str
        target_description: str
        metric_names: list of str — names of metrics assigned to the target

    Returns:
        list of dicts {section, prompt} or None on failure
    """
    system = (
        "You help nonprofit workers write structured progress notes. "
        "Given a plan target and its metrics, suggest 3–5 note sections. "
        "Each section has a title and a one-sentence prompt for what to write. "
        "Return a JSON array: [{\"section\": \"<title>\", \"prompt\": \"<guidance>\"}]. "
        "Return ONLY the JSON array, no other text."
    )
    user_msg = (
        f"Target: {target_name}\n"
        f"Description: {target_description}\n"
        f"Metrics: {', '.join(metric_names)}"
    )
    result = _call_openrouter(system, user_msg)
    if result is None:
        return None
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Could not parse note structure: %s", result[:200])
        return None
