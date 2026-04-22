import os
from dataclasses import dataclass

import requests


REQUIRED_ENV = ("JIRA_URL", "JIRA_USER", "JIRA_PASSWORD")
REQUEST_TIMEOUT = 30


class MissingCredentials(Exception):
    pass


class IssueFetchError(Exception):
    pass


@dataclass(frozen=True)
class Credentials:
    url: str
    user: str
    password: str


def load_credentials() -> Credentials:
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        raise MissingCredentials(
            f"missing environment variable(s): {', '.join(missing)}"
        )
    return Credentials(
        url=os.environ["JIRA_URL"].rstrip("/"),
        user=os.environ["JIRA_USER"],
        password=os.environ["JIRA_PASSWORD"],
    )


def fetch_issue(creds: Credentials, issue_id: str) -> tuple[str, str | None]:
    endpoint = f"{creds.url}/rest/api/2/issue/{issue_id}"
    try:
        resp = requests.get(
            endpoint,
            params={"fields": "summary,description"},
            auth=(creds.user, creds.password),
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as e:
        raise IssueFetchError(f"network error: {e}") from e

    if resp.status_code != 200:
        raise IssueFetchError(f"HTTP {resp.status_code} {resp.reason}")

    try:
        data = resp.json()
        fields = data["fields"]
        summary = fields["summary"]
        description = fields.get("description")
    except (ValueError, KeyError, TypeError) as e:
        raise IssueFetchError(f"unexpected response format: {e}") from e

    return summary, description
