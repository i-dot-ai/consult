"""
Create a Linear issue in the PRO team's "In Review" state for a major dependency bump.

Required environment variables:
  LINEAR_API_KEY     - Linear personal API key (lin_api_*)
  PR_TITLE           - Title of the Dependabot PR
  PR_URL             - URL of the Dependabot PR
  DEPENDENCY_NAMES   - Name(s) of the dependency being bumped
  PREVIOUS_VERSION   - Version before the bump
  NEW_VERSION        - Version after the bump
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
        return json.loads(resp.read())


def main() -> None:
    api_key = os.environ["LINEAR_API_KEY"]
    pr_title = os.environ["PR_TITLE"]
    pr_url = os.environ["PR_URL"]
    dep_names = os.environ["DEPENDENCY_NAMES"]
    prev_version = os.environ["PREVIOUS_VERSION"]
    new_version = os.environ["NEW_VERSION"]

    # Resolve team ID and "In Review" state ID from the team key
    team_resp = linear_query(api_key, """
        query {
          teams(filter: { key: { eq: "PRO" } }) {
            nodes {
              id
              states {
                nodes { id name type }
              }
            }
          }
        }
    """)

    team = team_resp["data"]["teams"]["nodes"][0]
    team_id = team["id"]

    in_review_state = next(
        s for s in team["states"]["nodes"] if s["name"].lower() == "in review"
    )

    issue_title = f"Review major dependency bump: {dep_names} {prev_version} -> {new_version}"
    issue_description = (
        f"Dependabot has opened a PR with a **major version bump** that requires manual review.\n\n"
        f"**Dependency:** {dep_names}\n"
        f"**Version change:** {prev_version} → {new_version}\n\n"
        f"**PR:** [{pr_title}]({pr_url})"
    )

    create_resp = linear_query(api_key, """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue { identifier url }
          }
        }
    """, {"input": {
        "teamId": team_id,
        "stateId": in_review_state["id"],
        "title": issue_title,
        "description": issue_description,
    }})

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
