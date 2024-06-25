import sentry_sdk

from consultation_analyser.settings.base import *  # noqa

CSRF_TRUSTED_ORIGINS = ["https://" + env("DOMAIN_NAME")]  # noqa: F405

SENTRY_DSN = env("SENTRY_DSN")  # noqa: F405
EXECUTION_CONTEXT = env("EXECUTION_CONTEXT")  # noqa: F405
GIT_SHA = env("GIT_SHA")  # noqa: F405


def sentry_before_send(event, hint):
    """Filters Sentry events before sending.

    Adapted from https://jkfran.com/capturing-unhandled-exceptions-sentry-python/

    This function filters out handled exceptions.

    Args:
        event (dict): The event dictionary containing exception data.

        hint (dict): Additional information about the event, including
            the original exception.

    Returns:
        dict: The modified event dictionary, or None if the event should be
            ignored.
    """
    # Ignore handled exceptions
    exceptions = event.get("exception", {}).get("values", [])
    if exceptions:
        exc = exceptions[-1]
        mechanism = exc.get("mechanism")

        if mechanism:
            if mechanism.get("handled"):
                return None

    return event


sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,  # noqa: F405
    release=GIT_SHA,
    before_send=sentry_before_send,
)


sentry_sdk.set_tags({"execution_context": EXECUTION_CONTEXT})
