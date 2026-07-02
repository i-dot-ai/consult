"""
Create a Linear issue in the configured team's "In Review" state for a major dependency bump,
randomly assigned to a member of the configured assignee project.

Required environment variables:
  LINEAR_API_KEY                - Linear personal API key (lin_api_*)
  LINEAR_TEAM_KEY               - Key of the Linear team to create the issue in (e.g. "PRO")
  LINEAR_ASSIGNEE_PROJECT_KEY   - Key of the Linear project to draw assignees from (e.g. "GIT")
  PR_TITLE                      - Title of the Dependabot PR
  PR_URL                        - URL of the Dependabot PR
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
        return json.loads(resp.read())


def resolve_assignee_id(api_key: str, project_key: str) -> str | None:
    """Pick a random assignable member from the given Linear project."""
    project_resp = linear_query(api_key, """
        query($key: String!) {
          projects(filter: { identifier: { eq: $key } }) {
            nodes {
              id
              name
              members {
                nodes { id email isAssignable }
              }
            }
          }
        }
    """, {"key": project_key})

    projects = project_resp["data"]["projects"]["nodes"]
    if not projects:
        print(f"WARNING: could not find a Linear project with key '{project_key}'")
        return None

    pool = [u for u in projects[0]["members"]["nodes"] if u["isAssignable"]]
    if not pool:
        print(f"WARNING: project '{project_key}' has no assignable members")
        return None

    chosen = random.choice(pool)
    print(f"Assigning to: {chosen['email']}")
    return chosen["id"]


def main() -> None:
    api_key = os.environ["LINEAR_API_KEY"]
    team_key = os.environ["LINEAR_TEAM_KEY"]
    project_key = os.environ["LINEAR_ASSIGNEE_PROJECT_KEY"]
    pr_title = os.environ["PR_TITLE"]
    pr_url = os.environ["PR_URL"]
    dep_names = os.environ["DEPENDENCY_NAMES"]
    prev_version = os.environ["PREVIOUS_VERSION"]
    new_version = os.environ["NEW_VERSION"]

    # Resolve team ID and "In Review" state ID from the team key
    team_resp = linear_query(api_key, """
        query($key: String!) {
          teams(filter: { key: { eq: $key } }) {
            nodes {
              id
              states {
                nodes { id name type }
              }
            }
          }
        }
    """, {"key": team_key})

    teams = team_resp["data"]["teams"]["nodes"]
    if not teams:
        print(f"ERROR: could not find a Linear team with key '{team_key}'")
        sys.exit(1)

    team = teams[0]
    team_id = team["id"]

    in_review_state = next(
        (s for s in team["states"]["nodes"] if s["name"].lower() == "in review"),
        None,
    )
    if in_review_state is None:
        print("ERROR: could not find an 'In Review' state in the PRO team workflow")
        sys.exit(1)

    assignee_id = resolve_assignee_id(api_key, project_key)

    issue_title = f"Review major dependency bump: {dep_names} {prev_version} -> {new_version}"
    issue_description = (
        f"Dependabot has opened a PR with a **major version bump** that requires manual review.\n\n"
        f"**Dependency:** {dep_names}\n"
        f"**Version change:** {prev_version} → {new_version}\n\n"
        f"**PR:** [{pr_title}]({pr_url})"
    )

    issue_input: dict = {
        "teamId": team_id,
        "stateId": in_review_state["id"],
        "title": issue_title,
        "description": issue_description,
    }
    if assignee_id:
        issue_input["assigneeId"] = assignee_id

    create_resp = linear_query(api_key, """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue { identifier url }
          }
        }
    """, {"input": issue_input})

    result = create_resp["data"]["issueCreate"]
    if result["success"]:
        issue = result["issue"]
        print(f"Created Linear issue {issue['identifier']}: {issue['url']}")
    else:
        print("ERROR: Linear issue creation failed")
        print(json.dumps(create_resp, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
