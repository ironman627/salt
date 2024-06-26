"""
Wrapper around uptime API
=========================
"""

import logging

from salt.exceptions import CommandExecutionError

try:
    import requests

    ENABLED = True
except ImportError:
    ENABLED = False

log = logging.getLogger(__name__)


def __virtual__():
    """
    Only load this module if the requests python module is available
    """
    if ENABLED:
        return "uptime"
    return (False, "uptime module needs the python requests module to work")


def create(name, **params):
    """Create a check on a given URL.

    Additional parameters can be used and are passed to API (for
    example interval, maxTime, etc). See the documentation
    https://github.com/fzaninotto/uptime for a full list of the
    parameters.

    CLI Example:

    .. code-block:: bash

        salt '*' uptime.create http://example.org

    """
    if check_exists(name):
        msg = f"Trying to create check that already exists : {name}"
        log.error(msg)
        raise CommandExecutionError(msg)
    application_url = _get_application_url()
    log.debug("[uptime] trying PUT request")
    params.update(url=name)
    req = requests.put(f"{application_url}/api/checks", data=params, timeout=120)
    if not req.ok:
        raise CommandExecutionError(f"request to uptime failed : {req.reason}")
    log.debug("[uptime] PUT request successful")
    return req.json()["_id"]


def delete(name):
    """
    Delete a check on a given URL

    CLI Example:

    .. code-block:: bash

        salt '*' uptime.delete http://example.org
    """
    if not check_exists(name):
        msg = f"Trying to delete check that doesn't exists : {name}"
        log.error(msg)
        raise CommandExecutionError(msg)
    application_url = _get_application_url()
    log.debug("[uptime] trying DELETE request")
    jcontent = requests.get(f"{application_url}/api/checks", timeout=120).json()
    url_id = [x["_id"] for x in jcontent if x["url"] == name][0]
    req = requests.delete(f"{application_url}/api/checks/{url_id}", timeout=120)
    if not req.ok:
        raise CommandExecutionError(f"request to uptime failed : {req.reason}")
    log.debug("[uptime] DELETE request successful")
    return True


def _get_application_url():
    """
    Helper function to get application url from pillar
    """
    application_url = __salt__["pillar.get"]("uptime:application_url")
    if application_url is None:
        log.error("Could not load uptime:application_url pillar")
        raise CommandExecutionError(
            "uptime:application_url pillar is required for authentication"
        )
    return application_url


def checks_list():
    """
    List URL checked by uptime

    CLI Example:

    .. code-block:: bash

        salt '*' uptime.checks_list
    """
    application_url = _get_application_url()
    log.debug("[uptime] get checks")
    jcontent = requests.get(f"{application_url}/api/checks", timeout=120).json()
    return [x["url"] for x in jcontent]


def check_exists(name):
    """
    Check if a given URL is in being monitored by uptime

    CLI Example:

    .. code-block:: bash

        salt '*' uptime.check_exists http://example.org
    """
    if name in checks_list():
        log.debug("[uptime] found %s in checks", name)
        return True
    return False
