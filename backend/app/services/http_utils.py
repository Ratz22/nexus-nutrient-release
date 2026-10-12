"""
Shared HTTP client for public data services (SoilGrids, NASA POWER,
OpenAlex, Crossref). Retries transient failures and turns every failure
into an UpstreamError whose message is written for a researcher.
"""
import time

import httpx

from app.core.config import get_settings

settings = get_settings()


class UpstreamError(Exception):
    """A public data service could not supply what was asked. The message is safe to show to users."""


def get_json(url: str, params: dict | None = None, service: str = "the online service") -> dict:
    last_problem = f"{service} did not respond"
    for attempt in range(settings.HTTP_RETRIES + 1):
        try:
            with httpx.Client(
                timeout=settings.HTTP_TIMEOUT_S,
                follow_redirects=True,
                headers={"User-Agent": "NEXUS-research-tool/0.1"},
            ) as client:
                resp = client.get(url, params=params)
        except httpx.TimeoutException:
            last_problem = f"{service} took longer than {int(settings.HTTP_TIMEOUT_S)} seconds to answer"
        except httpx.HTTPError:
            last_problem = f"the connection to {service} failed. Check your internet access"
        else:
            if resp.status_code == 429:
                last_problem = f"{service} is limiting requests right now. Wait a minute and try again"
            elif resp.status_code >= 500:
                last_problem = f"{service} is temporarily unavailable"
            elif resp.status_code >= 400:
                raise UpstreamError(f"{service} did not accept this request (code {resp.status_code})")
            else:
                try:
                    return resp.json()
                except ValueError as exc:
                    raise UpstreamError(f"{service} returned a response in an unexpected format") from exc
        if attempt < settings.HTTP_RETRIES:
            time.sleep(1.5 * (attempt + 1))
    raise UpstreamError(last_problem)