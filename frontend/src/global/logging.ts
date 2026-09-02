import type { MiddlewareHandler } from "astro";
import {
  configureOtel,
  createLogger,
} from "@i-dot-ai-npm/utilities-observability";

export interface LoggerAdapter {
  middleware: MiddlewareHandler;
}

const disabledLogger: LoggerAdapter = {
  middleware: async (_, next) => next(),
};

const serviceName = process.env.OTEL_SERVICE_NAME;
const otlpEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
const otelEnabled = process.env.OTEL_ENABLED === "true";

const buildLogger = async (serviceName: string): Promise<LoggerAdapter> => {
  const deploymentEnvironment = process.env.ENVIRONMENT;

  try {
    // configureOtel patches pino, so it has to run before createLogger.
    await configureOtel({
      serviceName,
      deploymentEnvironment,
      otlpEndpoint,
    });

    const logger = createLogger({
      serviceName,
      deploymentEnvironment,
      otlpEndpoint,
      // Marks log lines for the CloudWatch subscription filter, matching the backend.
      shipLogs: 1,
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
  } catch (error) {
    // Telemetry setup must never stop the server from handling requests.
    console.warn("OTel setup failed; request logging disabled", error);
    return disabledLogger;
  }
};

const logger: LoggerAdapter =
  otelEnabled && otlpEndpoint && serviceName
    ? await buildLogger(serviceName)
    : disabledLogger;

export default logger;
