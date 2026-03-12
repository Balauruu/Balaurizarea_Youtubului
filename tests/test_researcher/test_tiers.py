"""Tests for researcher.tiers module — source tier classification."""
import pytest
from researcher.tiers import (
    TIER_1_DOMAINS,
    TIER_2_DOMAINS,
    TIER_3_DOMAINS,
    TIER_RETRY_MAP,
    classify_domain,
)


def test_tier_retry_map_values():
    assert TIER_RETRY_MAP[1] == 3
    assert TIER_RETRY_MAP[2] == 1
    assert TIER_RETRY_MAP[3] == 0


def test_classify_domain_wikipedia_is_tier1():
    assert classify_domain("https://en.wikipedia.org/wiki/Test") == 1


def test_classify_domain_archive_is_tier1():
    assert classify_domain("https://archive.org/details/test") == 1


def test_classify_domain_facebook_is_tier3():
    assert classify_domain("https://www.facebook.com/page") == 3


def test_classify_domain_x_com_is_tier3():
    assert classify_domain("https://x.com/user") == 3


def test_classify_domain_reddit_is_tier3():
    assert classify_domain("https://reddit.com/r/test") == 3


def test_classify_domain_unknown_is_tier2():
    assert classify_domain("https://unknowndomain.example.com/page") == 2


def test_classify_domain_strips_www_prefix():
    assert classify_domain("https://www.en.wikipedia.org/wiki/Test") == 1


def test_tier1_domains_has_expected_entries():
    assert "archive.org" in TIER_1_DOMAINS
    assert "loc.gov" in TIER_1_DOMAINS
    assert "en.wikipedia.org" in TIER_1_DOMAINS


def test_tier3_domains_has_expected_entries():
    assert "facebook.com" in TIER_3_DOMAINS
    assert "twitter.com" in TIER_3_DOMAINS
    assert "reddit.com" in TIER_3_DOMAINS


def test_classify_domain_loc_is_tier1():
    assert classify_domain("https://loc.gov/collections/something") == 1


def test_classify_domain_twitter_is_tier3():
    assert classify_domain("https://twitter.com/user") == 3
