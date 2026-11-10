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
class Comment:
    author: str
    created: str
    body: str
    visibility: str | None


@dataclass(frozen=True)
class Issue:
    summary: str
    description: str | None
    comments: list[Comment]
    comment_total: int


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


def fetch_issue(creds: Credentials, issue_id: str) -> Issue:
    endpoint = f"{creds.url}/rest/api/2/issue/{issue_id}"
    try:
        # No `fields` param: jira.cubrid.org redirects between http and https and re-encodes the
        # query, turning the comma into %252C so "summary,description" arrives as one bogus field
        # name and the response comes back without `fields`. Requesting all fields avoids it, and
        # the full response also carries every comment.
        resp = requests.get(
            endpoint,
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
        thread = fields.get("comment") or {}
        comments = [
            Comment(
                author=(c.get("author") or {}).get("displayName") or "(unknown)",
                created=c["created"],
                body=c.get("body") or "",
                visibility=(c.get("visibility") or {}).get("value"),
            )
            for c in thread.get("comments") or []
        ]
        return Issue(
            summary=fields["summary"],
            description=fields.get("description"),
            comments=comments,
            comment_total=thread.get("total", len(comments)),
        )
    except (ValueError, KeyError, TypeError) as e:
        raise IssueFetchError(f"unexpected response format: {e}") from e
