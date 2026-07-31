"""
Create a Linear issue for Dependabot PR events, assigned to the GitHub-assigned
reviewer via a username-to-Linear-email map stored in a secret.

Supports two issue types, selected via the ISSUE_TYPE environment variable:

  major-bump  - A major version dependency bump requiring manual review.
  ci-failure  - CI checks failed on a minor/patch Dependabot PR.

Required environment variables (all types):
  LINEAR_API_KEY                - Linear personal API key (lin_api_*)
  LINEAR_TEAM_KEY               - Key of the Linear team to create the issue in (e.g. "ENG")
  DEPENDABOT_USER_MAP           - JSON secret mapping GitHub username to Linear email
                                  e.g. '{"octocat": "octocat@example.com"}'
  GITHUB_ASSIGNEE               - GitHub username of the PR assignee (may be empty)
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

    try:
        team = resp["data"]["teams"]["nodes"][0]
    except (KeyError, IndexError):
        print(f"ERROR: could not find a Linear team with key '{team_key}'")
        sys.exit(1)
    return team


def resolve_assignee_id(api_key: str, github_username: str, user_map: dict) -> str | None:
    """Resolve a Linear user ID from a GitHub username via the user map."""
    if not github_username:
        return None

    email = user_map.get(github_username)
    if not email:
        print(f"WARNING: GitHub user '{github_username}' not found in user map, issue will be unassigned")
        return None

    resp = linear_query(api_key, """
        query($email: String!) {
          users(filter: { email: { eq: $email } }) {
            nodes { id email }
          }
        }
    """, {"email": email})

    try:
        user = resp["data"]["users"]["nodes"][0]
    except (KeyError, IndexError):
        print(f"WARNING: no Linear user found for email '{email}', issue will be unassigned")
        return None

    print(f"Assigning to: {user['email']}")
    return user["id"]


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
    github_assignee = os.environ.get("GITHUB_ASSIGNEE", "")
    user_map = json.loads(os.environ.get("DEPENDABOT_USER_MAP", "{}"))
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

    assignee_id = resolve_assignee_id(api_key, github_assignee, user_map)

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
