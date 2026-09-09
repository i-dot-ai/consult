# Error capture is independent of these rates: before_send runs regardless, so
# lowering them doesn't drop errors.
PROD_PERF_SAMPLE_RATE = 0.1
NON_PROD_PERF_SAMPLE_RATE = 1.0


def default_perf_sample_rate(environment):
    """Env-aware default for trace/profile sampling. Overridable per environment via
    the SENTRY_*_SAMPLE_RATE env vars; this is just the fallback when they're unset.
    """
    if environment.lower() == "prod":
        return PROD_PERF_SAMPLE_RATE
    return NON_PROD_PERF_SAMPLE_RATE


def sentry_before_send(event, hint):
    """Drops handled exceptions — only uncaught exceptions reach Sentry."""
    try:
        mechanism = event["exception"]["values"][-1]["mechanism"]
        if mechanism and mechanism.get("handled") is True:
            return None
    except (KeyError, IndexError):
        pass

    return event
