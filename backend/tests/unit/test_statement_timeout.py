import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
SHOW_TIMEOUT = (
    "from django.db import connection\n"
    "with connection.cursor() as c:\n"
    "    c.execute('SHOW statement_timeout')\n"
    "    print(c.fetchone()[0])"
)


def _statement_timeout(extra_env: dict[str, str]) -> str:
    env = {k: v for k, v in os.environ.items() if k != "DB_STATEMENT_TIMEOUT_MS"}
    env |= {"DJANGO_SETTINGS_MODULE": "settings.test", **extra_env}
    result = subprocess.run(
        [sys.executable, "manage.py", "shell", "-c", SHOW_TIMEOUT],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()[-1]


@pytest.mark.parametrize(
    ("extra_env", "expected"),
    [({}, "0"), ({"DB_STATEMENT_TIMEOUT_MS": "55000"}, "55s")],
)
def test_statement_timeout_follows_env(extra_env, expected):
    assert _statement_timeout(extra_env) == expected
