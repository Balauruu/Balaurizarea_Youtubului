"""Source tier constants and domain classification for the researcher skill.

Three tiers control fetch behavior:
  Tier 1 — reliable/authoritative: 3 retries
  Tier 2 — general sources / unknown: 1 retry (default for unknown domains)
  Tier 3 — social/anti-bot: skip entirely, log as skipped_tier3
"""
from urllib.parse import urlparse

TIER_1_DOMAINS: frozenset[str] = frozenset({
    "archive.org",
    "loc.gov",
    "archives.gov",
    "commons.wikimedia.org",
    "en.wikipedia.org",
    "images.nasa.gov",
    "nps.gov",
    "nationalarchives.gov.uk",
    "publicdomainreview.org",
})

TIER_2_DOMAINS: frozenset[str] = frozenset({
    "britannica.com",
    "bbc.com",
    "theguardian.com",
    "nytimes.com",
    "reuters.com",
    "apnews.com",
    "html.duckduckgo.com",
    "duckduckgo.com",
    # reddit.com reclassified from Tier 3 to Tier 2 — Phase 8 decision
    "reddit.com",
    "old.reddit.com",
})

TIER_3_DOMAINS: frozenset[str] = frozenset({
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "pinterest.com",
})

# Retry count per tier. Tier 3 = 0 means skip entirely.
TIER_RETRY_MAP: dict[int, int] = {1: 3, 2: 1, 3: 0}


def classify_domain(url: str) -> int:
    """Return tier (1, 2, or 3) for a URL. Unknown domains default to Tier 2.

    Args:
        url: A full URL string including scheme.

    Returns:
        1 for Tier 1 (authoritative), 2 for Tier 2 (general/unknown),
        3 for Tier 3 (social/do-not-fetch).
    """
    host = urlparse(url).hostname or ""
    # Strip www. prefix so www.en.wikipedia.org matches en.wikipedia.org
    host = host.removeprefix("www.")
    if host in TIER_1_DOMAINS:
        return 1
    if host in TIER_3_DOMAINS:
        return 3
    return 2  # Unknown domains default to Tier 2 (user decision)
