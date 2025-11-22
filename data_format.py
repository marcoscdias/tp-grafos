from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class User:
    login: str
    id: int
    node_id: str
    type: str


@dataclass
class PullRequest:
    id: int
    number: int
    state: str
    title: str
    user: Optional[User]
    # If present it represents it was merged
    merged_at: Optional[str]
    # Graph Weight 5 (Merge)
    merged_by: Optional[User]


@dataclass
class Issue:
    id: int
    node_id: str
    # Is None if the account was deleted, skip if so
    user: Optional[User]
    number: int
    title: str
    state: Literal["open", "closed"]
    comments: int
    closed_at: Optional[str]
    # If present this issue is a pull request
    pull_request: Optional[dict] 
    closed_by: Optional[User]


@dataclass
class IssueComment:
    id: int
    node_id: str
    # Is None if the account was deleted, skip if so
    user: Optional[User]
    issue_url: str

@dataclass
class PullComment:
    id: int
    node_id: str
    # Is None if the account was deleted, skip if so
    user: Optional[User]
    pull_request_url: str