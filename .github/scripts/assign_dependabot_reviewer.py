"""Request a review on a Dependabot PR from a least-loaded team member.

Reviewers are no longer auto-assigned, so Dependabot PRs (major bumps and CI
failures, which need a human) would otherwise sit unowned. Ties are broken
randomly to spread load evenly.
"""

import os
import random
from urllib import error, parse

from pr_load_balancer import get_review_counts, github_request


def main() -> None:
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/", maxsplit=1)
    owner_path = parse.quote(owner, safe="")
    repo_path = parse.quote(repo, safe="")
    github_token = os.environ["GITHUB_TOKEN"]

    counts = get_review_counts(
        owner_path, repo_path, github_token, os.environ["CONSULT_TEAM_READ_TOKEN"]
    )
    if not counts:
        # Warn rather than fail so the Linear issue is still created, just unassigned.
        print("::warning::No consult-team members found; no reviewer requested for dependabot PR.")
        return

    fewest = min(counts.values())
    reviewer = random.choice([login for login, n in counts.items() if n == fewest])

    try:
        github_request(
            f"/repos/{owner_path}/{repo_path}/pulls/{os.environ['PR_NUMBER']}/requested_reviewers",
            github_token,
            method="POST",
            data={"reviewers": [reviewer]},
        )
    except error.HTTPError as exc:
        # e.g. reviewer isn't a collaborator; don't lose the Linear issue over it.
        print(f"::warning::Could not request review from {reviewer}: HTTP {exc.code}.")
        return
    print(f"Requested review from {reviewer} ({fewest} open review requests).")
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"reviewer={reviewer}\n")


if __name__ == "__main__":
    main()
