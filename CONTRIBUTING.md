# Contributing

How we work on this repo: raising pull requests, reviewing them, and the small
conventions that keep review fast and low-friction. These are norms, not
bureaucracy - the goal is smaller changes, clearer intent, and reviews that move
quickly. If a rule is getting in the way of shipping something obvious, say so in
the PR rather than working around it silently.

For the optional tooling (Claude Code/OpenCode, GitHub CLI, Linear, Context7), see
[docs/devex.md](docs/devex.md).

## Coding standards

We follow the GDS engineering standards found [here](https://gds-way.digital.cabinet-office.gov.uk/). We also have our
own engineering standards that build on-top of this that can be
found [here](https://github.com/i-dot-ai/config/tree/main/ways-of-working).

## Pull requests

- CICD will only run on the relevant changes, e.g. if only the frontend has been changed
  then only the frontend tests will run. It is your responsibility to make sure no unintended
  changes happen in a location that isn't tested automatically
- **Branch off `main`.** Name branches should follow the Linear patterns, this can be done simply by copying the branch
  name from the Linear work item.
- GitHub now supports [stacked PRs](https://docs.github.com/en/pull-requests/how-tos/stacked-pull-requests), make
  use of these when doing large pieces of work to break down individual pieces of reviewable code.
- **Keep PRs small and focused** - one logical change. A reviewer should be able to
  hold the whole diff in their head. If a change is genuinely large (a migration, a
  refactor that touches many files), split it where you can and explain the shape in
  the PR description.
- **Fill in the template.** (or even better, get your coding agent to do it, but don't make it too verbose)
  GitHub loads [`.github/pull_request_template.md`](.github/pull_request_template.md) automatically:
  say what changed and why, link the Linear issue (`PRO-*` if not done automatically by branch name),
  point reviewers at where to start, and flag the PR size.
- **Self-review first.** Read your own diff before requesting review - it catches
  leftover debug code, stray files, and unclear naming, and respects reviewers' time.
- If you self-review and catch fixes that you are going to look at, raise them as a comment with a checkbox
  yourself, so that reviewers know they don't need to review this part.
- **Keep the Linear issue up to date** as the PR moves through review - see the Linear
  conventions in [docs/devex.md](docs/devex.md#linear).
- **Double-check for AI leftovers** before requesting a review - excessive comments, imports out of place
  or code that is needlessly complex are all mental fatigue for reviewers to look through.

## Reviewers

- **Always add one reviewer from the team.** PRs don't auto-request the whole team - a sinle person
  from the team will be automatically assigned when a PR is opened. (See
  [`CODEOWNERS`](.github/CODEOWNERS).)
- **One approval is required to merge** (enforced by branch protection). 
- **Be pragmatic about trivial PRs.** If the author flags a PR as *trivial* (a one-liner,
  a typo, a comment), a single approval is enough - don't wait for only the assigned person to review it.
- **Tag beyond the two where it helps.** Add other stakeholders as reviewers for
  awareness, and if a change warrants a specific person's sign-off, tag or message them
  explicitly asking for approval - and don't merge until they've approved.

A reviewer can approve with open **nit**/**consider** comments only when small **nit** comments are the
only comments left on the PR that are unresolved - trust the author to handle the nit comments without a need for a
re-review. Reserve "request changes" for **blocking** issues.

## Addressing review comments

- **Reply, don't just resolve.** Push the fix, then reply (even briefly - "done",
  "fixed in `abc123`") so the reviewer knows what happened. If you disagree, say why
  rather than silently closing the thread.
- If it is helpful to you, reply to the user with a checklist of actions to take from their comment,
  so they know what you are working on.
- **The commenter resolves the thread**, not the author - it signals they're satisfied.
  For plain **nit**s the author may resolve their own.
- **Re-request review after non-trivial changes** (the 🔄 icon by the reviewer's name)
  so it re-enters their queue - remember this is what gets your PR over the line once
  you've addressed the comments; a reviewer won't necessarily come back on their own.
- **Prefer follow-up commits over force-pushes** while a review is in progress - a
  reviewer can then see just what changed since they last looked. Rebase on merge.
- **Out-of-scope suggestions become a follow-up**, not scope creep in this PR. Open a
  Linear issue and link it.

## Merging

- Rebase-merge to keep `main` history clean.
- CI (build, tests, pre-commit, and the Claude auto-review) must be green. Don't merge
  around a red check without understanding why it's red.

## Keeping the PR list healthy

As a team we keep on top of stale PRs rather than letting them pile up. If a PR has gone
quiet, don't just close it - **check with the author first**: it may be waiting on a
re-review, blocked on something, or still wanted. Nudge it forward, hand it off, or close
it by agreement.

## Dependabot

Dependabot will auto-merge minor and patch version bumps. If you see a dependabot PR that is stuck
only because the branch is out of date, comment `@dependabot rebase` to force a rebase. This should
merge the PR when the branch is up-to-date.

Major dependabot PRs are opened in Linear as issues, with a person assigned to them. It is that persons
responsibility to check with relevant people whether the changes in the PR are acceptable or breaking,
and resolve any issues with failing CICD due to the package update.