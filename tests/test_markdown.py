# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

from glean_parser import markdown
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser(tmpdir):
    """Test translating metrics to Markdown files."""
    tmpdir = Path(tmpdir)

    translate.translate(
        ROOT / "data" / "core.yaml",
        "markdown",
        tmpdir,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["metrics.md"])

    # Make sure descriptions made it in
    with open(tmpdir / "metrics.md", "r", encoding="utf-8") as fd:
        content = fd.read()
        assert "is assembled out of the box by the Glean SDK." in content
        # Make sure the table structure is in place
        assert (
            "| Name | Type | Description | Data reviews | Extras | Expiration |"
            in content
        )
        # Make sure non ASCII characters are there
        assert "جمع 搜集" in content


def test_extra_info_generator():
    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=[42],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
        extra_keys={"my_extra": {"description": "an extra"}},
    )

    assert markdown.extra_info(event) == [("my_extra", "an extra")]

    # We don't currently support extra info for types other than events.
    other = metrics.Timespan(
        type="timespan",
        category="category",
        name="metric",
        bugs=[42],
        time_unit="day",
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )

    assert len(markdown.extra_info(other)) == 0


def test_ping_desc():
    # Make sure to return something for built-in pings.
    for ping_name in pings.RESERVED_PING_NAMES:
        assert len(markdown.ping_desc(ping_name)) > 0

    # We don't expect nothing for unknown pings.
    assert len(markdown.ping_desc("unknown-ping")) == 0

    # If we have a custom ping cache, try look up the
    # description there.
    cache = {}
    cache["cached_ping"] = pings.Ping(
        name="cached_ping",
        description="the description for the custom ping\n with a surprise",
        bugs=["1234"],
        notification_emails=["email@example.com"],
        data_reviews=["https://www.example.com/review"],
        include_client_id=False,
    )

    assert (
        markdown.ping_desc("cached_ping", cache)
        == "the description for the custom ping\n with a surprise"
    )

    # We don't expect nothing for unknown pings, even with caches.
    assert len(markdown.ping_desc("unknown-ping", cache)) == 0


def test_ping_docs():
    # Make sure to return something for built-in pings.
    for ping_name in pings.RESERVED_PING_NAMES:
        docs = markdown.ping_docs(ping_name)
        assert docs.startswith("https://")
        assert len(docs) > 0

    # We don't expect nothing for unknown pings.
    assert len(markdown.ping_docs("unknown-ping")) == 0


def test_metrics_docs():
    assert (
        markdown.metrics_docs("boolean")
        == "https://mozilla.github.io/glean/book/user/metrics/boolean.html"
    )
    assert (
        markdown.metrics_docs("labeled_counter")
        == "https://mozilla.github.io/glean/book/user/metrics/labeled_counters.html"
    )
    assert (
        markdown.metrics_docs("labeled_string")
        == "https://mozilla.github.io/glean/book/user/metrics/labeled_strings.html"
    )
