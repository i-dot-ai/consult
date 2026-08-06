# 12. Minimum Self-Serve

Date: 2026-08-06

## Status

Accepted

## Context

The main sticking point in the application for users to get from initial contact to value is the data set up and
pipeline flow through the system. To improve upon the current approach, we need to create a new way for users to get
their data into the system.

The main challenges are the data formats that we will receive, and the downtime in the system this change could cause
due to it being such a large change that touches every part of the system.

To stop us getting stuck in the weeds of it, and trying to design a perfect system on paper before implementation, we
would like to start off with a small MVP to get the risk stage out of the way, then improve upon it after-the-fact.

## Decision

After many discussions about self-serve, what it will entail, how to action it, what to include in the MVP - we have
decided that the following will be the MVP, and we will iterate from there:

- Permissions will follow a 3 tier structure:
  - superuser
  - consultation manager
  - consultation user
- Data checklist to ensure the users have formatted their data correctly
- Ability to upload data exported directly from Qualtrics or CitizenSpace
- Ability to check and confirm question types
- Ability to confirm the consultation



## Consequences

The consequences of this work carry some risk:

- We open the floodgates to everyone and brick the system
- We get major scope creep as more things become requirements for self-serve to work
- Data templates that we get aren't representative of the users data
- The pipeline gets overwhelmed

But if this work goes as planned, it would fundamentally change the app for the better:

- We can now open the door for anyone to self-serve rather than waiting for us
- We massively cut down the time from initial contact to value, allowing us to focus on delivering more of that value
- We cut out the current template file
- We reduce the setup time from weeks to days
- We allow users more flexibility in data and question types
- Onboarding can be done at the pace we want it to be done, instead of dictated by engineer capacity