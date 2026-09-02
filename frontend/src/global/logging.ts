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

// process.env holds the vars ECS injects at deployed runtime, import.meta.env holds
// local dev's .env. Read both so the gate fires in either, matching utils.ts.
const readEnv = (key: string): string | undefined =>
  (typeof process !== "undefined" ? process.env[key] : undefined) ||
  import.meta.env[key] ||
  undefined;

const serviceName = readEnv("OTEL_SERVICE_NAME");
const otlpEndpoint = readEnv("OTEL_EXPORTER_OTLP_ENDPOINT");
const otelEnabled = readEnv("OTEL_ENABLED") === "true";

const buildLogger = async (serviceName: string): Promise<LoggerAdapter> => {
  const deploymentEnvironment = readEnv("ENVIRONMENT");

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
