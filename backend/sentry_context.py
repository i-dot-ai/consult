import sentry_sdk

MANUAL_CAPTURE_TAG = "consult.manual_capture"


def capture_handled_sentry_exception(error=None, **kwargs):
    """Drop-in replacement for sentry_sdk.capture_exception for exceptions the
    application already caught and is handling (e.g. converting to a 4xx/5xx
    response). Tags the event so sentry_before_send always forwards it, regardless
    of the handled/unhandled mechanism Sentry infers for manual captures.
    """
    new_kwargs = kwargs.copy()
    new_kwargs["tags"] = {**kwargs.get("tags", {}), MANUAL_CAPTURE_TAG: "true"}
    return sentry_sdk.capture_exception(error, **new_kwargs)


def sentry_before_send(event, hint):
    """Drops integration-captured handled exceptions. Manual captures also default to
    handled=True, so capture_handled_sentry_exception tags them to bypass this.
    """
    if MANUAL_CAPTURE_TAG in event.get("tags", {}):
        return event

    try:
        mechanism = event["exception"]["values"][-1]["mechanism"]
        if mechanism and mechanism.get("handled") is True:
            return None
    except (KeyError, IndexError):
        pass

    return event
