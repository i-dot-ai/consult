import * as Sentry from "@sentry/astro";

import { getEnvironment, getRelease } from "./src/global/utils";
import { getTracesSampleRate, sanitizeSentryEvent } from "./src/global/sentry";

const environment = getEnvironment();

Sentry.init({
  dsn: "https://0c4cfe196193e5051fcb710c48cf69ad@o4507646230069248.ingest.de.sentry.io/4510839028777040",
  dataCollection: {
    userInfo: false,
    cookies: false,
    httpHeaders: {
      request: {
        deny: [
          "forwarded",
          "-ip",
          "remote-",
          "via",
          "-user",
          "x-amzn-oidc-data",
          "x-amzn-oidc-accesstoken",
          "x-amzn-oidc-identity",
          "authorization",
          "cookie",
          "set-cookie",
          "x-api-key",
        ],
      },
      response: {
        deny: [
          "forwarded",
          "-ip",
          "remote-",
          "via",
          "-user",
          "x-amzn-oidc-data",
          "x-amzn-oidc-accesstoken",
          "x-amzn-oidc-identity",
          "authorization",
          "cookie",
          "set-cookie",
          "x-api-key",
        ],
      },
    },
    httpBodies: [],
    urlQueryParams: { deny: ["forwarded", "-ip", "remote-", "via", "-user"] },
    graphQL: { document: false, variables: false },
    genAI: { inputs: false, outputs: false },
    databaseQueryData: false,
    queues: false,
  },
  environment,
  release: getRelease(),
  tracesSampleRate: getTracesSampleRate(environment),
  beforeSend: sanitizeSentryEvent,
});
