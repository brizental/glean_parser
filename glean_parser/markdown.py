# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate Markdown documentation for metrics.
"""

from . import metrics
from . import pings
from . import util
from collections import defaultdict


def extra_info(obj):
    """
    Returns a list of string to string tuples with extra information for the type
    (e.g. extra keys for events) or an empty list if nothing is available.
    """
    extra_info = []

    if isinstance(obj, metrics.Event):
        for key in obj.allowed_extra_keys:
            extra_info.append((key, obj.extra_keys[key]["description"]))

    return extra_info


def ping_desc(ping_name, custom_pings_cache={}):
    """
    Return a text description of the ping. If a custom_pings_cache
    is available, look in there for non-reserved ping names description.
    """
    desc = ""

    if ping_name in pings.RESERVED_PING_NAMES:
        desc = (
            "This is a built-in ping that is assembled out of the "
            "box by the Glean SDK."
        )
    elif ping_name == "all_pings":
        desc = "These metrics are sent in every ping."
    elif ping_name in custom_pings_cache:
        desc = custom_pings_cache[ping_name].description

    return desc


def metrics_docs(obj_name):
    """
    Return a link to the documentation entry for the Glean SDK metric of the
    requested type.
    """
    base_url = "https://mozilla.github.io/glean/book/user/metrics/{}.html"

    # We need to fixup labeled stuff, as types are singular and docs refer
    # to them as plural.
    fixedup_name = obj_name
    if obj_name.startswith("labeled_"):
        fixedup_name += "s"

    return base_url.format(fixedup_name)


def ping_docs(ping_name):
    """
    Return a link to the documentation entry for the requested Glean SDK
    built-in ping.
    """
    if ping_name not in pings.RESERVED_PING_NAMES:
        return ""

    return f"https://mozilla.github.io/glean/book/user/pings/{ping_name}.html"


def output_markdown(objs, output_dir, options={}):
    """
    Given a tree of objects, output Markdown docs to `output_dir`.

    This produces a single `metrics.md`. The file contains a table of
    contents and a section for each ping metrics are collected for.

    :param objects: A tree of objects (metrics and pings) as returned from
    `parser.parse_objects`.
    :param output_dir: Path to an output directory to write to.
    :param options: options dictionary. No option currently supported, stays for
    signature compatibility with the other outputters.
    """

    # Build a dictionary that associates pings with their metrics.
    #
    # {
    #  "baseline": [
    #    { ... metric data ... },
    #    ...
    #  ],
    #  "metrics": [
    #    { ... metric data ... },
    #    ...
    #  ],
    #  ...
    # }
    #
    # This also builds a dictionary of custom pings, if available.
    custom_pings_cache = defaultdict()
    metrics_by_pings = defaultdict(list)
    for category_key, category_val in objs.items():
        for obj in category_val.values():
            # Filter out custom pings. We will need them for extracting
            # the description
            if obj.is_internal_metric():
                continue
            elif isinstance(obj, pings.Ping):
                custom_pings_cache[obj.name] = obj
            else:
                # If we get here, obj is definitely a metric
                for ping_name in obj.send_in_pings:
                    metrics_by_pings[ping_name].append(obj)

    # Sort the metrics by their identifier, to make them show up nicely
    # in the docs and to make generated docs reproducible.
    for ping_name in metrics_by_pings:
        metrics_by_pings[ping_name] = sorted(
            metrics_by_pings[ping_name], key=lambda x: x.identifier()
        )

    template = util.get_jinja2_template(
        "markdown.jinja2",
        filters=(
            ("extra_info", extra_info),
            ("metrics_docs", metrics_docs),
            ("ping_desc", lambda x: ping_desc(x, custom_pings_cache)),
            ("ping_docs", ping_docs),
        ),
    )

    filename = "metrics.md"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as fd:
        fd.write(template.render(metrics_by_pings=metrics_by_pings))
        # Jinja2 squashes the final newline, so we explicitly add it
        fd.write("\n")
