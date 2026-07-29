import sentry_sdk

MANUAL_CAPTURE_TAG = "consult.manual_capture"


def capture_handled_sentry_exception(error=None, **kwargs):
    """Drop-in replacement for sentry_sdk.capture_exception for exceptions the
    application already caught and is handling (e.g. converting to a 4xx/5xx
    response). Tags the event so sentry_before_send always forwards it, regardless
    of the handled/unhandled mechanism Sentry infers for manual captures.
    """
    kwargs.setdefault("tags", {})[MANUAL_CAPTURE_TAG] = "true"
    return sentry_sdk.capture_exception(error, **kwargs)


def sentry_before_send(event, hint):
    """Filters Sentry events before sending.

    Adapted from https://jkfran.com/capturing-unhandled-exceptions-sentry-python/

    Explicit captures via capture_handled_sentry_exception are always sent.
    Otherwise, this function filters out exceptions Sentry's own integrations marked
    as handled, since those are typically caught and dealt with by application code
    (see sentry_sdk.utils.single_exception_from_error_tuple: unmarked/manual captures
    default to handled=True, while integration-driven captures of exceptions that
    escaped uncaught mark handled=False).

    Args:
        event (dict): The event dictionary containing exception data.

        hint (dict): Additional information about the event, including
            the original exception.

    Returns:
        dict: The modified event dictionary, or None if the event should be
            ignored.
    """
    if event.get("tags", {}).get(MANUAL_CAPTURE_TAG):
        return event

    # Ignore handled exceptions
    exceptions = event.get("exception", {}).get("values", [])
    if exceptions:
        exc = exceptions[-1]
        mechanism = exc.get("mechanism")

        if mechanism:
            if mechanism.get("handled"):
                return None

    return event
