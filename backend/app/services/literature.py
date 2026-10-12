"""
Live literature search.
Primary: OpenAlex (free, no key, broad coverage, returns DOIs).
Fallback: Crossref (free, no key, authoritative DOI metadata).
Every result carries its DOI and the service it came from.
"""
from app.core.config import get_settings
from app.services.http_utils import UpstreamError, get_json

settings = get_settings()


def _openalex_abstract(inverted: dict | None) -> str | None:
    """OpenAlex stores abstracts as {word: [positions]}. Rebuild the sentence."""
    if not inverted:
        return None
    words = {}
    for word, positions in inverted.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words)) or None


def _from_openalex(query: str, limit: int) -> list[dict]:
    params = {
        "search": query,
        "per-page": limit,
        "select": "doi,title,publication_year,authorships,primary_location,cited_by_count,abstract_inverted_index",
    }
    if settings.CONTACT_EMAIL:
        params["mailto"] = settings.CONTACT_EMAIL
    data = get_json(settings.OPENALEX_BASE_URL, params=params, service="the OpenAlex literature index")
    out = []
    for w in data.get("results", []):
        doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
        source = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        authors = [
            a["author"]["display_name"]
            for a in w.get("authorships", [])
            if (a.get("author") or {}).get("display_name")
        ]
        out.append({
            "title": w.get("title") or "Untitled",
            "authors": authors,
            "year": w.get("publication_year"),
            "venue": source,
            "doi": doi,
            "url": f"https://doi.org/{doi}" if doi else None,
            "citations": w.get("cited_by_count") or 0,
            "abstract": _openalex_abstract(w.get("abstract_inverted_index")),
            "source": "OpenAlex",
        })
    return out


def _from_crossref(query: str, limit: int) -> list[dict]:
    params = {
        "query": query,
        "rows": limit,
        "select": "DOI,title,author,issued,container-title,is-referenced-by-count",
    }
    if settings.CONTACT_EMAIL:
        params["mailto"] = settings.CONTACT_EMAIL
    data = get_json(settings.CROSSREF_BASE_URL, params=params, service="the Crossref DOI registry")
    out = []
    for it in data.get("message", {}).get("items", []):
        titles = it.get("title") or ["Untitled"]
        authors = [" ".join(p for p in [a.get("given"), a.get("family")] if p) for a in it.get("author", [])]
        parts = (it.get("issued") or {}).get("date-parts") or [[None]]
        year = parts[0][0] if parts and parts[0] else None
        venue = (it.get("container-title") or [None])[0]
        doi = it.get("DOI")
        out.append({
            "title": titles[0],
            "authors": authors,
            "year": year,
            "venue": venue,
            "doi": doi,
            "url": f"https://doi.org/{doi}" if doi else None,
            "citations": it.get("is-referenced-by-count") or 0,
            "abstract": None,
            "source": "Crossref",
        })
    return out


def search_literature(query: str, limit: int = 10) -> list[dict]:
    problems = []
    for fn in (_from_openalex, _from_crossref):
        try:
            results = fn(query, limit)
        except UpstreamError as exc:
            problems.append(str(exc))
            continue
        if results:
            return results
    if len(problems) == 2:
        raise UpstreamError("Neither literature service answered: " + "; ".join(problems))
    return []