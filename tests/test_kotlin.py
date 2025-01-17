# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import shutil
import subprocess

from glean_parser import kotlin
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser(tmpdir):
    """Test translating metrics to Kotlin files."""
    tmpdir = Path(tmpdir)

    translate.translate(
        ROOT / "data" / "core.yaml",
        "kotlin",
        tmpdir,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        [
            "CorePing.kt",
            "Telemetry.kt",
            "Environment.kt",
            "DottedCategory.kt",
            "GleanInternalMetrics.kt",
        ]
    )

    # Make sure descriptions made it in
    with open(tmpdir / "CorePing.kt", "r", encoding="utf-8") as fd:
        content = fd.read()
        assert "True if the user has set Firefox as the default browser." in content
        # Make sure the namespace option is in effect
        assert "package Foo" in content

    with open(tmpdir / "Telemetry.kt", "r", encoding="utf-8") as fd:
        content = fd.read()
        assert "جمع 搜集" in content

    with open(tmpdir / "GleanInternalMetrics.kt", "r", encoding="utf-8") as fd:
        content = fd.read()
        assert 'category = ""' in content

    # Only run this test if ktlint is on the path
    if shutil.which("ktlint"):
        for filepath in tmpdir.glob("*.kt"):
            subprocess.check_call(["ktlint", filepath])


def test_kotlin_generator():
    kdf = kotlin.kotlin_datatypes_filter

    assert kdf("\n") == r'"\n"'
    assert kdf([42, "\n"]) == r'listOf(42, "\n")'
    assert (
        kdf({"key": "value", "key2": "value2"})
        == r'mapOf("key" to "value", "key2" to "value2")'
    )
    assert kdf(metrics.Lifetime.ping) == "Lifetime.Ping"


def test_metric_type_name():
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

    assert kotlin.type_name(event) == "EventMetricType<metricKeys>"

    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=[42],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )

    assert kotlin.type_name(event) == "EventMetricType<NoExtraKeys>"

    boolean = metrics.Boolean(
        type="boolean",
        category="category",
        name="metric",
        bugs=[42],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )
    assert kotlin.type_name(boolean) == "BooleanMetricType"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=[42],
        notification_emails=["nobody@nowhere.com"],
    )
    assert kotlin.type_name(ping) == "PingType"


def test_duplicate(tmpdir):
    """
    Test that there aren't duplicate imports when using a labeled and
    non-labeled version of the same metric.

    https://github.com/mozilla-mobile/android-components/issues/2793
    """

    tmpdir = Path(tmpdir)

    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml", "kotlin", tmpdir, {"namespace": "Foo"}
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Category.kt"])

    with open(tmpdir / "Category.kt", "r", encoding="utf-8") as fd:
        content = fd.read()
        assert (
            content.count(
                "import mozilla.components.service.glean.private.CounterMetricType"
            )
            == 1
        )


def test_glean_namespace(tmpdir):
    """
    Test that setting the glean namespace works.
    """
    tmpdir = Path(tmpdir)

    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml",
        "kotlin",
        tmpdir,
        {"namespace": "Foo", "glean_namespace": "Bar"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Category.kt"])

    with open(tmpdir / "Category.kt", "r", encoding="utf-8") as fd:
        content = fd.read()
        assert content.count("import Bar.private.CounterMetricType") == 1


def test_gecko_datapoints(tmpdir):
    """Test translating metrics to Kotlin files."""
    tmpdir = Path(tmpdir)

    translate.translate(
        ROOT / "data" / "gecko.yaml",
        "kotlin",
        tmpdir,
        {"glean_namespace": "Bar"},
        {"allow_reserved": True},
    )

    metrics_files = [
        "GfxContentCheckerboard.kt",
        "GfxInfoAdapter.kt",
        "PagePerf.kt",
        "NonGeckoMetrics.kt",
    ]
    assert set(x.name for x in tmpdir.iterdir()) == set(
        ["GleanGeckoMetricsMapping.kt"] + metrics_files
    )

    # Make sure descriptions made it in
    with open(tmpdir / "GleanGeckoMetricsMapping.kt", "r", encoding="utf-8") as fd:
        content = fd.read()
        # Make sure we're adding the relevant Glean SDK import, once.
        assert content.count("import Bar.private.HistogramMetricBase") == 1

        # Validate the generated Gecko metric mapper Kotlin functions.
        # NOTE: Indentation, whitespaces  and text formatting of the block
        # below are important. Do not change them unless the file format
        # changes, otherwise validation will fail.
        expected_func = """    fun getHistogram(geckoMetricName: String): HistogramMetricBase? {
        return when (geckoMetricName) {
            // From GfxContentCheckerboard.kt
            "CHECKERBOARD_DURATION" -> GfxContentCheckerboard.duration
            // From PagePerf.kt
            "GV_PAGE_LOAD_MS" -> PagePerf.loadTime
            "GV_PAGE_RELOAD_MS" -> PagePerf.reloadTime
            else -> null
        }
    }"""

        assert expected_func in content

        expected_func = """    fun getCategoricalMetric(
        geckoMetricName: String
    ): LabeledMetricType<CounterMetricType>? {
        return when (geckoMetricName) {
            // From PagePerf.kt
            "DOM_SCRIPT_PRELOAD_RESULT" -> PagePerf.domScriptPreload
            else -> null
        }
    }"""

        assert expected_func in content

        expected_func = """    fun getBooleanScalar(geckoMetricName: String): BooleanMetricType? {
        return when (geckoMetricName) {
            // From GfxInfoAdapter.kt
            "gfx_adapter.stand_alone" -> GfxInfoAdapter.standAlone
            else -> null
        }
    }"""

        assert expected_func in content

        expected_func = """    fun getStringScalar(geckoMetricName: String): StringMetricType? {
        return when (geckoMetricName) {
            // From GfxInfoAdapter.kt
            "gfx_adapter.vendor_id" -> GfxInfoAdapter.vendorId
            else -> null
        }
    }"""

        assert expected_func in content

        expected_func = """    fun getQuantityScalar(geckoMetricName: String): QuantityMetricType? {
        return when (geckoMetricName) {
            // From GfxInfoAdapter.kt
            "gfx_adapter.width" -> GfxInfoAdapter.screenWidth
            else -> null
        }
    }"""

        assert expected_func in content

    for file_name in metrics_files:
        with open(tmpdir / file_name, "r", encoding="utf-8") as fd:
            content = fd.read()
            assert "HistogramMetricBase" not in content

    # Only run this test if ktlint is on the path
    if shutil.which("ktlint"):
        for filepath in tmpdir.glob("*.kt"):
            subprocess.check_call(["ktlint", filepath])
