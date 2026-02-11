import * as Sentry from "@sentry/astro";

Sentry.init({
  dsn: "https://0c4cfe196193e5051fcb710c48cf69ad@o4507646230069248.ingest.de.sentry.io/4510839028777040",
  sendDefaultPii: true,
  debug: true,
});
