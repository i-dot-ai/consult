import type { MiddlewareHandler } from "astro";
import {
  configureOtel,
  createLogger,
} from "@i-dot-ai-npm/utilities-observability";

export interface LoggerAdapter {
  middleware: MiddlewareHandler;
}

const SERVICE_NAME = "consult-frontend-service";

const disabledLogger: LoggerAdapter = {
  middleware: async (_, next) => next(),
};

const otlpEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
const otelEnabled =
  process.env.OTEL_ENABLED === "true" && Boolean(otlpEndpoint);

const buildLogger = async (): Promise<LoggerAdapter> => {
  const deploymentEnvironment = process.env.ENVIRONMENT;

  // configureOtel patches pino, so it has to run before createLogger.
  await configureOtel({
    serviceName: SERVICE_NAME,
    deploymentEnvironment,
    otlpEndpoint,
  });

  const logger = createLogger({
    serviceName: SERVICE_NAME,
    deploymentEnvironment,
    otlpEndpoint,
    shipLogs: 0,
  });

  return {
    middleware: async ({ locals, request }, next) => {
      const start = performance.now();
      const { method } = request;
      const { pathname } = new URL(request.url);

      const response = await next();

      logger.info(
        {
          contextId: locals.contextId,
          method,
          path: pathname,
          status: response.status,
          durationMs: Math.round(performance.now() - start),
        },
        "request completed",
      );

      return response;
    },
  };
};

const logger: LoggerAdapter = otelEnabled
  ? await buildLogger()
  : disabledLogger;

export default logger;
