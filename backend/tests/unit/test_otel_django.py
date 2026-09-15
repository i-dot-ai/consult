from unittest.mock import MagicMock, patch

import otel_django


def test_configure_warns_and_continues_when_setup_fails():
    logger = MagicMock()
    with patch.object(otel_django, "configure_otel_for_django", side_effect=RuntimeError("boom")):
        otel_django.configure_django_otel(logger=logger, service_name="consult-backend-test")
    logger.warning.assert_called_once()
    assert logger.warning.call_args.kwargs["service_name"] == "consult-backend-test"
