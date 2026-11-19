# 1. Record design decisions

Date: 2026-10-16

## Status

Done

## Context

Objective: Build the ability to import survey responses from two survey providers in order to improve ease and user satisfaction of setting up a new consultation​

## Decision

We will use Interaction Design Records (saved in the style of ADRs), as [described by Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

## Consequences

Each design decision should be recorded as a copy of the design HTML file, as well as an IDR to describe the changes
that have taken place. Use the pattern `dd-mm-yy-<decision>` for the folder, and use versions for the documents inside.
7 new design records have been written IDR-096 to IDR-102,  and 3 older ones updated IDR-94 IDR-95 IDR90

## Summary

Every control says what it is before anyone touches it.
A link goes to a page; a button does something.
No greyed-out controls: hide what isn’t available, and say why.
Only actions that can’t be undone get a confirmation.
Confirmation before an action, success message after.
Delete this consultation is a warning button, apart from the safe links.
One word for one thing, with the screen leading.
Finalise, not Sign off.
Everyone can add people; adding someone new creates their account.
Lists keep their shape: up to three people in the Team column, then +N.

Use this decision record as a template.
