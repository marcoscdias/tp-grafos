from dataclasses import dataclass
from typing import Literal


@dataclass
class User:
    login: str
    id: int
    node_id: str
    type: str


@dataclass
class PullRequest:
    # If present it represents it was merged, if not, and closed_at is present on Issue it was closed without merging
    merged_at: str | None


@dataclass
class Issue:
    id: int
    node_id: str
    # Is None if the account was deleted, skip if so
    user: User | None
    number: int
    title: str
    state: Literal["open", "closed"]
    comments: int
    closed_at: str | None
    # If present this issue is a pull request
    pull_request: PullRequest | None
    closed_by: User | None


@dataclass
class IssueComment:
    id: int
    node_id: str
    # Is None if the account was deleted, skip if so
    user: User | None
    issue_url: str


# Works both for Review comments and Reviews
@dataclass
class PullComment:
    id: int
    node_id: str
    # Is None if the account was deleted, skip if so
    user: User | None
    pull_request_url: str
