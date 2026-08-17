import * as Sentry from "@sentry/astro";

import { getEnvironment, getRelease } from "./src/global/utils";
import { getTracesSampleRate, sanitizeSentryEvent } from "./src/global/sentry";

const environment = getEnvironment();

Sentry.init({
  dsn: "https://0c4cfe196193e5051fcb710c48cf69ad@o4507646230069248.ingest.de.sentry.io/4510839028777040",
  sendDefaultPii: false,
  environment,
  release: getRelease(),
  tracesSampleRate: getTracesSampleRate(environment),
  beforeSend: sanitizeSentryEvent,
});
