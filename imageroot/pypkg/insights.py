#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Helpers shared by the insights module actions and events."""

import os
import subprocess
import sys

import agent

SERVICE = "insights-collector.service"
DEFAULT_SERVER_URL = "https://insights.nethesis.it"
STREAM_CURSOR_FILE = "insights_stream_cursor"


def get_subscription(rdb):
    """(system_id, auth_token) of the cluster subscription, or (None, None).

    The insights server accepts data only from subscribed machines, and
    the subscription is the only identity the collector uses.
    """
    subscription = rdb.hgetall("cluster/subscription") or {}
    system_id = subscription.get("system_id")
    auth_token = subscription.get("auth_token")
    if not system_id or not auth_token:
        return None, None
    return system_id, auth_token


def find_active_elsewhere(rdb, module_id=None):
    """Id of another insights instance with the collector enabled, or "".

    The collector reads the logs of the whole cluster, so a second enabled
    instance would ship every line twice. The core can only limit
    instances per node, hence this cluster-wide check.
    """
    module_id = module_id or os.environ["MODULE_ID"]
    image_name = agent.get_image_name_from_url(os.environ["IMAGE_URL"])
    for other_id in sorted(rdb.hkeys("cluster/module_node") or []):
        if other_id == module_id:
            continue
        env = rdb.hgetall(f"module/{other_id}/environment") or {}
        other_url = env.get("IMAGE_URL")
        if not other_url or agent.get_image_name_from_url(other_url) != image_name:
            continue
        if env.get("INSIGHTS_ENABLED") == "1":
            return other_id
    return ""


def systemctl(*args, check=True):
    return subprocess.run(["systemctl", "--user", *args],
                          stdout=sys.stderr,
                          stderr=sys.stderr,
                          text=True,
                          check=check)


def start_collector():
    # The collector reads its environment once at startup: enable and
    # restart covers both a first start and a configuration change.
    systemctl("enable", SERVICE)
    systemctl("restart", SERVICE)


def stop_collector(check=True):
    systemctl("disable", "--now", SERVICE, check=check)


def reset_cursor():
    """Forget the stream position: next start follows the log from now."""
    try:
        os.unlink(STREAM_CURSOR_FILE)
    except FileNotFoundError:
        pass
