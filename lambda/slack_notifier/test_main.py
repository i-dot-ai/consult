import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch


def load_module():
    os.environ["SLACK_WEBHOOK_URL"] = "https://example.com/webhook"
    shared_path = Path(__file__).parents[1] / "shared" / "otel_bootstrap.py"
    shared_spec = importlib.util.spec_from_file_location("otel_bootstrap", shared_path)
    shared_module = importlib.util.module_from_spec(shared_spec)
    shared_spec.loader.exec_module(shared_module)
    sys.modules["otel_bootstrap"] = shared_module
    path = Path(__file__).parent / "code" / "main.py"
    spec = importlib.util.spec_from_file_location("slack_notifier_main", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_worker_event_is_sent_without_batch_console_link():
    module = load_module()
    context = Mock()
    event = {
        "source": "consult.worker",
        "detail": {
            "job_type": "FIND_THEMES",
            "status": "SUCCEEDED",
            "consultation_code": "consultation-code",
            "consultation_name": "Consultation",
            "user_id": "123",
            "job_id": "rq-job-id",
            "context_id": "context-id",
        },
    }

    with (
        patch.object(module, "send_slack_message") as send,
        patch.object(module, "logger"),
    ):
        module.lambda_handler(event, context)

    job = send.call_args.args[0]
    assert job == {
        "id": "rq-job-id",
        "status": "SUCCEEDED",
        "type": "FIND_THEMES",
        "runtime": "worker",
    }
