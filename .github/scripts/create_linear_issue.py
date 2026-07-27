"""
Create a Linear issue for Dependabot PR events, randomly assigned to a member
of the configured assignee team.

Supports two issue types, selected via the ISSUE_TYPE environment variable:

  major-bump  - A major version dependency bump requiring manual review.
  ci-failure  - CI checks failed on a minor/patch Dependabot PR.

Required environment variables (all types):
  LINEAR_API_KEY                - Linear personal API key (lin_api_*)
  LINEAR_TEAM_KEY               - Key of the Linear team to create the issue in (e.g. "ENG")
  LINEAR_ASSIGNEE_TEAM_KEY      - Key of the Linear team to draw assignees from (e.g. "GIT")
  ISSUE_TYPE                    - "major-bump" or "ci-failure"
  PR_TITLE                      - Title of the Dependabot PR
  PR_URL                        - URL of the Dependabot PR

Required for major-bump only:
  DEPENDENCY_NAMES              - Name(s) of the dependency being bumped
  PREVIOUS_VERSION              - Version before the bump
  NEW_VERSION                   - Version after the bump
"""

import json
import os
import random
import sys
import urllib.request


def linear_query(api_key: str, query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": api_key},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    if "errors" in result:
        print(f"GraphQL errors: {json.dumps(result['errors'], indent=2)}")
    return result


def resolve_team(api_key: str, team_key: str) -> dict:
    """Return the team node (id + states) for the given team key, or exit on failure."""
    resp = linear_query(api_key, """
        query($key: String!) {
          teams(filter: { key: { eq: $key } }) {
            nodes {
              id
              states {
                nodes { id name }
              }
            }
          }
        }
    """, {"key": team_key})

    teams = (resp.get("data") or {}).get("teams", {}).get("nodes", [])
    if not teams:
        print(f"ERROR: could not find a Linear team with key '{team_key}'")
        sys.exit(1)
    return teams[0]


def resolve_assignee_id(api_key: str, team_key: str) -> str | None:
    """Pick a random assignable member from the given Linear team."""
    resp = linear_query(api_key, """
        query($key: String!) {
          teams(filter: { key: { eq: $key } }) {
            nodes {
              name
              members {
                nodes { id email isAssignable }
              }
            }
          }
        }
    """, {"key": team_key})

    teams = (resp.get("data") or {}).get("teams", {}).get("nodes", [])
    if not teams:
        print(f"WARNING: could not find a Linear team with key '{team_key}'")
        return None

    pool = [u for u in teams[0]["members"]["nodes"] if u["isAssignable"]]
    if not pool:
        print(f"WARNING: team '{teams[0]['name']}' has no assignable members")
        return None

    chosen = random.choice(pool)
    print(f"Assigning to: {chosen['email']}")
    return chosen["id"]


def create_issue(api_key: str, issue_input: dict) -> str:
    """Create a Linear issue and return its id."""
    resp = linear_query(api_key, """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue { id identifier url }
          }
        }
    """, {"input": issue_input})

    result = (resp.get("data") or {}).get("issueCreate", {})
    if result.get("success"):
        issue = result["issue"]
        print(f"Created Linear issue {issue['identifier']}: {issue['url']}")
        return issue["id"]

    print("ERROR: Linear issue creation failed")
    print(json.dumps(resp, indent=2))
    sys.exit(1)


def attach_pr(api_key: str, issue_id: str, pr_url: str, pr_title: str) -> None:
    """Link the GitHub PR URL to the Linear issue as an attachment."""
    resp = linear_query(api_key, """
        mutation AttachPR($issueId: String!, $url: String!, $title: String) {
          attachmentLinkURL(issueId: $issueId, url: $url, title: $title) {
            success
            attachment { id }
          }
        }
    """, {"issueId": issue_id, "url": pr_url, "title": pr_title})

    success = (resp.get("data") or {}).get("attachmentLinkURL", {}).get("success")
    if success:
        print("Attached PR to Linear issue")
    else:
        # Non-fatal: issue was created, attachment is best-effort
        print("WARNING: failed to attach PR URL to Linear issue")
        print(json.dumps(resp, indent=2))


def main() -> None:
    api_key = os.environ["LINEAR_API_KEY"]
    team_key = os.environ["LINEAR_TEAM_KEY"]
    assignee_team_key = os.environ["LINEAR_ASSIGNEE_TEAM_KEY"]
    issue_type = os.environ["ISSUE_TYPE"]
    pr_title = os.environ["PR_TITLE"]
    pr_url = os.environ["PR_URL"]

    team = resolve_team(api_key, team_key)
    team_id = team["id"]

    in_review_state = next(
        (s for s in team["states"]["nodes"] if s["name"].lower() == "in review"),
        None,
    )
    if in_review_state is None:
        print(f"ERROR: could not find an 'In Review' state in the '{team_key}' team workflow")
        sys.exit(1)

    assignee_id = resolve_assignee_id(api_key, assignee_team_key)

    if issue_type == "major-bump":
        dep_names = os.environ["DEPENDENCY_NAMES"]
        prev_version = os.environ["PREVIOUS_VERSION"]
        new_version = os.environ["NEW_VERSION"]

        title = f"Review major dependency bump: {dep_names} {prev_version} -> {new_version}"
        description = (
            f"Dependabot has opened a PR with a **major version bump** that requires manual review.\n\n"
            f"**Dependency:** {dep_names}\n"
            f"**Version change:** {prev_version} → {new_version}\n\n"
            f"**PR:** [{pr_title}]({pr_url})"
        )

    elif issue_type == "ci-failure":
        title = f"CI failure on Dependabot PR: {pr_title}"
        description = (
            f"CI checks failed on a Dependabot minor/patch PR that would normally be auto-merged.\n\n"
            f"**PR:** [{pr_title}]({pr_url})\n\n"
            f"Please investigate the failure and either fix the issue or manually merge/close the PR."
        )

    else:
        print(f"ERROR: unknown ISSUE_TYPE '{issue_type}' — expected 'major-bump' or 'ci-failure'")
        sys.exit(1)

    issue_input: dict = {
        "teamId": team_id,
        "stateId": in_review_state["id"],
        "title": title,
        "description": description,
    }
    if assignee_id:
        issue_input["assigneeId"] = assignee_id

    issue_id = create_issue(api_key, issue_input)
    attach_pr(api_key, issue_id, pr_url, pr_title)


if __name__ == "__main__":
    main()
