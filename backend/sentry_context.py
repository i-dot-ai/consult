import sentry_sdk

MANUAL_CAPTURE_TAG = "consult.manual_capture"


def capture_handled_sentry_exception(error=None, **kwargs):
    """Drop-in replacement for sentry_sdk.capture_exception for exceptions the
    application already caught and is handling (e.g. converting to a 4xx/5xx
    response). Tags the event so sentry_before_send always forwards it, regardless
    of the handled/unhandled mechanism Sentry infers for manual captures.
    """
    new_kwargs = kwargs.copy()
    new_kwargs.setdefault("tags", {})[MANUAL_CAPTURE_TAG] = "true"
    return sentry_sdk.capture_exception(error, **new_kwargs)


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
    try:
        # If the event was captured via capture_handled_sentry_exception, it will be
        # tagged so we always send it, regardless of the handled/unhandled mechanism
        # Sentry infers for manual captures.
        if event["tags"][MANUAL_CAPTURE_TAG]:
            return event
    except KeyError:
        pass

    # Ignore handled exceptions
    try:
        exceptions = event["exception"]["values"]

        exc = exceptions[-1]
        mechanism = exc["mechanism"]

        if mechanism:
            if mechanism["handled"]:
                return None
    except (KeyError, IndexError):
        pass

    return event
