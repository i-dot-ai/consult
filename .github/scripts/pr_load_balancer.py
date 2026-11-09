"""Comment on a pull request with the current review load for the Consult team."""

import json
import os
from urllib import parse, request

API_URL = "https://api.github.com"
COMMENT_MARKER = "<!-- pr-review-load -->"


def github_request(
    path: str,
    token: str,
    *,
    method: str = "GET",
    data: dict | None = None,
) -> tuple[object, dict]:
    body = json.dumps(data).encode() if data is not None else None
    api_request = request.Request(
        f"{API_URL}{path}",
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with request.urlopen(api_request) as response:
        return json.loads(response.read() or b"null"), response.headers


def get_all_pages(path: str, token: str) -> list[dict]:
    separator = "&" if "?" in path else "?"
    page = 1
    results = []

    while True:
        data, _ = github_request(f"{path}{separator}per_page=100&page={page}", token)
        if not isinstance(data, list):
            raise TypeError(f"Expected a list response from GitHub for {path}")
        results.extend(data)
        if len(data) < 100:
            return results
        page += 1


def build_comment(review_counts: dict[str, int]) -> str:
    rows = "\n".join(
        f"| {login} | {count} |"
        for login, count in sorted(
            review_counts.items(), key=lambda item: (item[1], item[0])
        )
    )
    return f"""{COMMENT_MARKER}
## PR review load

Use this snapshot to choose reviewers manually. Counts show open PRs where each team member currently has a pending review request.

| Team member | Assigned reviews |
| --- | ---: |
{rows}"""


def main() -> None:
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/", maxsplit=1)
    pull_request_number = int(os.environ["PR_NUMBER"])
    github_token = os.environ["GITHUB_TOKEN"]
    team_token = os.environ["CONSULT_TEAM_READ_TOKEN"]
    owner_path = parse.quote(owner, safe="")
    repo_path = parse.quote(repo, safe="")

    team_members = get_all_pages(
        f"/orgs/{owner_path}/teams/consult-team/members",
        team_token,
    )
    review_counts = {member["login"]: 0 for member in team_members}
    pull_requests = get_all_pages(
        f"/repos/{owner_path}/{repo_path}/pulls?state=open", github_token
    )

    for pull_request in pull_requests:
        requested_reviewers, _ = github_request(
            f"/repos/{owner_path}/{repo_path}/pulls/{pull_request['number']}/requested_reviewers",
            github_token,
        )
        if not isinstance(requested_reviewers, dict):
            raise TypeError("Expected an object response for requested reviewers")
        for reviewer in requested_reviewers["users"]:
            login = reviewer["login"]
            if login in review_counts:
                review_counts[login] += 1

    body = build_comment(review_counts)
    comments = get_all_pages(
        f"/repos/{owner_path}/{repo_path}/issues/{pull_request_number}/comments",
        github_token,
    )
    existing_comment = next(
        (
            comment
            for comment in comments
            if comment.get("user", {}).get("login") == "github-actions[bot]"
            and COMMENT_MARKER in comment.get("body", "")
        ),
        None,
    )

    if existing_comment:
        github_request(
            f"/repos/{owner_path}/{repo_path}/issues/comments/{existing_comment['id']}",
            github_token,
            method="PATCH",
            data={"body": body},
        )
    else:
        github_request(
            f"/repos/{owner_path}/{repo_path}/issues/{pull_request_number}/comments",
            github_token,
            method="POST",
            data={"body": body},
        )


if __name__ == "__main__":
    main()
