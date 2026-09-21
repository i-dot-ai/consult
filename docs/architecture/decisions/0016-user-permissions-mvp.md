# 16. User Permissions MVP

Date: 2026-09-17

## Status

Accepted

Supersedes: [0012](0012-minimum-self-serve-decision.md)

## Context

As part of the data setup V2 work, a decision is needed on what the initial permissions structure should entail,
what is in-scope, what is out-of-scope and what to push to later in the year.

This is largely dependent on whether to include departments and department owners into the initial set of
permissions or stick with a 2 user setup for now instead.

The two options are:

1) superuser, department owner and user:
    i) superuser: team members, have superadmin privileges
    ii) department owner: has admin powers based on department → consultation and department → user 
    relationships
    iii) user: can upload data to consultations they are assigned to, and read results of a consultation 
    they are assigned to

2) superuser and user:
    i) superuser: team members, have superadmin privileges 
    ii) user: permissions are based on whether the user has created or is assigned to consultations
        a) has created: can assign users, add data, unassign users, delete a consultation
        b) has been assigned: can upload data to and read results of a consultation

## Decision

After discussions within the team, it was decided to implement option 2 (superuser and user) for the MVP to get 
an updated permission feature deployed as soon as possible, and then return to the 3 permissions set at a later date.

## Consequences

### Positive

1. Reduced time needed to implement updated permissions required for data setup v2
2. Updates to the permissions can be done iteratively
3. Frontend screens can be created with less intensive design and implementation requirements

### Negative

1. The permissions will need double-handling
