# Consult Astro UI

## Setting up

1. Install nvm ([instructions](https://github.com/nvm-sh/nvm?tab=readme-ov-file#install--update-script))
2. Use the correct Node version by running `nvm install` and `nvm use`
3. Install dependencies with `npm install`
4. Create `.env` and copy contents of `env.example`

To run locally, make sure you have the Django application running then run `npm run dev`.

## Testing
Run `npx playwright install` to be able to run end-to-end tests with playwright.

## Commands

All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:3000`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |
| `npm run test`            | Run vitest unit tests                            |
| `npm run e2e`             | Run playwright end-to-end tests                  |
| `npm run e2e-ui`          | Run playwright end-to-end tests with ui          |

## Astro documentation

See [astro documentation](https://docs.astro.build) for more information.
