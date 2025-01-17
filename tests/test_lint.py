# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from pathlib import Path


from glean_parser import lint
from glean_parser import parser


import util


ROOT = Path(__file__).parent


def test_common_prefix():
    contents = [
        {
            "telemetry": {
                "network_latency": {
                    "type": "quantity",
                    "gecko_datapoint": "GC_NETWORK_LATENCY",
                    "unit": "ms",
                },
                "network_bandwidth": {
                    "type": "quantity",
                    "gecko_datapoint": "GC_NETWORK_BANDWIDTH",
                    "unit": "kbps",
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 1
    assert nits[0][0] == "COMMON_PREFIX"

    # Now make sure the override works
    contents[0]["no_lint"] = ["COMMON_PREFIX"]
    all_metrics = parser.parse_objects(contents)
    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 0


def test_unit_in_name():
    contents = [
        {
            "telemetry": {
                "network_latency_ms": {"type": "timespan", "time_unit": "millisecond"},
                "memory_usage_mb": {
                    "type": "memory_distribution",
                    "memory_unit": "megabyte",
                },
                "width_pixels": {
                    "type": "quantity",
                    "gecko_datapoint": "WIDTH_PIXELS",
                    "unit": "pixels",
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 3
    assert all(nit[0] == "UNIT_IN_NAME" for nit in nits)

    # Now make sure the override works
    contents[0]["telemetry"]["network_latency_ms"]["no_lint"] = ["UNIT_IN_NAME"]
    all_metrics = parser.parse_objects(contents)
    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 2


def test_category_generic():
    contents = [{"metrics": {"measurement": {"type": "boolean"}}}]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 1
    assert nits[0][0] == "CATEGORY_GENERIC"

    contents[0]["no_lint"] = ["CATEGORY_GENERIC"]
    all_metrics = parser.parse_objects(contents)
    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 0


def test_combined():
    contents = [
        {
            "metrics": {
                "m_network_latency_ms": {
                    "type": "timespan",
                    "time_unit": "millisecond",
                },
                "m_memory_usage_mb": {
                    "type": "memory_distribution",
                    "memory_unit": "megabyte",
                },
                "m_width_pixels": {
                    "type": "quantity",
                    "gecko_datapoint": "WIDTH_PIXELS",
                    "unit": "pixels",
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 5
    assert set(["COMMON_PREFIX", "CATEGORY_GENERIC", "UNIT_IN_NAME"]) == set(
        v[0] for v in nits
    )


def test_superfluous():
    contents = [
        {
            "telemetry": {
                "network_latency": {
                    "type": "timespan",
                    "time_unit": "millisecond",
                    "no_lint": ["UNIT_IN_NAME"],
                }
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 1
    assert all(nit[0] == "SUPERFLUOUS_NO_LINT" for nit in nits)
    assert all("UNIT_IN_NAME" in nit[2] for nit in nits)
