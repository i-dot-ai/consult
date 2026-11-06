# Postman collection

A Postman collection for exercising the backend API against a local stack,
with sign-in handled for you.

| File | Purpose |
| --- | --- |
| `consult.postman_collection.json` | Every API route, grouped by resource, with example bodies. v2 routes sit in their own folder. |
| `local.postman_environment.json` | Variables for a local backend: base URL, the dev user to act as, and the ids the requests reference. |

## Setting up

1. Start the stack with `make dev`. The environment's `devEmail` defaults to
   `admin@example.com`, the first of the staff users `make setup` creates from
   `ADMIN_USERS` in `.env`. To act as someone else, add them to `ADMIN_USERS`
   and rerun `cd backend && uv run python manage.py createadminusers`.
2. In Postman, **Import** both files from this directory.
3. Select the **Consult local** environment.
4. Send any request. The collection's pre-request script builds a dev token for
   `devEmail`, calls `POST /api/validate-token/`, and stores the returned access
   token in the environment. It refreshes the token when it is within a minute
   of expiring, so you should not need to touch it. Both tokens are visible in
   the environment as `devToken` and `accessToken` if you need to debug sign-in.

## Acting as a different user

Change `devEmail` in the environment and clear `accessToken`. The next request
signs in as that user. To check permission boundaries you need a non-staff
user: `createadminusers` makes everyone staff, so demote one with
**Users > Update user** (`{"is_staff": false}`) while signed in as another
admin, then switch `devEmail` to it.

Local sign-in works because the backend, when not deployed, decodes the dev
token without verifying its signature. In deployed environments the token
comes from the auth proxy, so this collection is not meant to be pointed at
them.

## Ids

Most requests reference `consultationId`, `questionId`, `responseId`, and so
on. Run the list endpoints first and paste ids into the environment, or use
**Consultations > Create test data** to load a fixture consultation and take
the ids from its response.

## v2 routes

The `v2` folder is only reachable when the backend runs with
`DATA_SETUP_V2_ENABLED=true` in `.env`; otherwise every request in it returns
404. Restart the backend after changing the flag, since gunicorn's reload
watches Python files, not `.env`.

## Keeping it current

The collection is maintained by hand. When you add or change a route, update
the matching request here in the same pull request. For the exhaustive,
generated view of the API, use Swagger at `http://localhost:8000/api/docs/`
(local settings only).
