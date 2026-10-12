"""
Turns backend problems into plain-language messages, and blocks pages
cleanly when the prediction server is off or out of date.
Nothing in this file shows raw HTTP codes, JSON, or tracebacks.
"""
import os

import httpx
import streamlit as st

from theme import friendly_error

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
ROOT_URL = API_BASE_URL.split("/api/v1")[0]

FEATURE_FLAG = {"literature": "has_literature_search", "dataset": "has_dataset_info"}


def connection_problem():
    return (
        "The prediction server could not be reached.",
        "Open the backend window and make sure it is running, then press Refresh.",
    )


def _detail(resp):
    try:
        d = resp.json().get("detail")
    except ValueError:
        return None
    return d if isinstance(d, str) else None


def explain_http_problem(resp) -> tuple[str, str]:
    """Return (why, next_step) for a failed backend response."""
    detail = _detail(resp)
    if resp.status_code == 404 and detail in (None, "Not Found"):
        return (
            "The running prediction server is out of date and is missing this feature.",
            "Close the backend window, start it again with the setup commands, then press Refresh.",
        )
    if resp.status_code == 422:
        return ("Some input was not in the format the server expects.", "Check the values on this page and try again.")
    if resp.status_code == 502:
        return (
            "The online literature service did not answer. " + (detail or ""),
            "Wait a minute and try again. Some campus and hostel networks block these services.",
        )
    if detail:
        return (detail, "Follow the setup steps in the backend window, then try again.")
    return ("The server returned an unexpected response.", "Refresh the page. If it repeats, restart the backend window.")


@st.cache_data(ttl=2, show_spinner=False)
def _health_state():
    try:
        r = httpx.get(f"{ROOT_URL}/health", timeout=5)
    except httpx.ConnectError:
        return "offline", {"detail": "nothing is listening on port 8000"}
    except httpx.HTTPError as exc:
        return "offline", {"detail": f"connection problem: {type(exc).__name__}"}
    if r.status_code != 200:
        return "outdated", {"detail": f"the server answered HTTP {r.status_code}"}
    try:
        data = r.json()
    except ValueError:
        return "outdated", {"detail": "the server did not return JSON"}
    return "ok", data


def _block(why: str, next_step: str):
    friendly_error(what="This page is waiting on the prediction server.", why=why, next_step=next_step)
    if st.button("Refresh", key="refresh_backend", type="primary"):
        _health_state.clear()
        st.rerun()
    st.stop()


def require_backend(*features: str):
    state, info = _health_state()
    if state == "offline":
        _block(
            f"The prediction server is not reachable ({info.get('detail', 'unknown')}).",
            "Open the backend window. If it is closed, start it with the commands below, then press Refresh.",
        )
    if state == "outdated":
        _block(
            f"The prediction server replied, but not as expected ({info.get('detail', 'unknown')}).",
            "Check the backend window for an error. Restart it if needed, then press Refresh.",
        )
    missing = [f for f in features if not info.get(FEATURE_FLAG.get(f, ""), False)]
    if missing:
        _block(
            "The prediction server is running, but it is missing: " + ", ".join(missing) + ".",
            "Stop the backend window (Ctrl+C) and start it again from the project folder.",
        )