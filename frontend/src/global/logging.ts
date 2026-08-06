import type { MiddlewareHandler } from "astro";

export interface LoggerAdapter {
    middleware: MiddlewareHandler;
}

const disabledLogger: LoggerAdapter = {
    middleware: async (_, next) => next(),
}

const enabled = import.meta.env.LOGGING_ENABLED === "true";

let logger: LoggerAdapter = disabledLogger;

if (enabled) {
    try {
        // @ts-ignore: Cannot find module
        const observabilityUtils = await import("@i-dot-ai-npm/utilities-observability");

        const loggingTools = await setupLogger(observabilityUtils);

        logger = loggingTools.logger;

        const liveLogger: LoggerAdapter = {
            middleware: async (_, next) => {
                // TODO: Call logging action here once logger is implemented
                // Ex: logger.log(...);

                return next();
            },
        }

        logger = liveLogger;
    } catch(err) {
        console.warn(
            "@i-dot-ai-npm/utilities-observability could not be loaded. Logging will be disabled.",
            err,
        )
    }
}

// Types not available until @i-dot-ai-npm/utilities-observability is implemented
// @ts-ignore
async function setupLogger(observabilityUtils) {
    const { configureOtel, createLogger, getMeter } = observabilityUtils;
    const SERVICE_NAME = "consult-service";

    await configureOtel({
        serviceName: SERVICE_NAME,
        deploymentEnvironment: import.meta.env.ENVIRONMENT,
        otlpEndpoint: import.meta.env.OTEL_EXPORTER_OTLP_ENDPOINT,
    });

    const logger = createLogger({ serviceName: SERVICE_NAME, shipLogs: 0 });
    const meter = getMeter();
    const counter = meter.createCounter('poc.requests');

    return { logger, meter, counter };
}

export default logger;