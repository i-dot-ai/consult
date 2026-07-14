import functools

from django_rq import job as _rq_job

from logging_context import get_context_id, rebind_context


def job(*job_args, **job_kwargs):
    """Drop-in replacement for django_rq.job that transparently propagates context_id:
    - at enqueue time (.delay()/.enqueue()), auto-fills context_id from the caller's
      current logger context if not explicitly supplied
    - at execution time, strips context_id off and rebinds the worker's logger context
      to it before running the job body
    """

    def decorator(func):
        @functools.wraps(func)
        def context_aware(*args, context_id: str | None = None, **kwargs):
            rebind_context(context_id)
            return func(*args, **kwargs)

        decorated = _rq_job(*job_args, **job_kwargs)(context_aware)
        enqueue_call = decorated.delay  # .delay and .enqueue are the same underlying function

        @functools.wraps(func)
        def enqueue_with_context(*args, context_id: str | None = None, **kwargs):
            return enqueue_call(*args, context_id=context_id or get_context_id(), **kwargs)

        decorated.delay = enqueue_with_context
        decorated.enqueue = enqueue_with_context
        return decorated

    return decorator
