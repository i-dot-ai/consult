import base64
import json
import subprocess
from shlex import quote


def renderLitSsr(path, props):
    result = subprocess.run(  # nosec
        [
            f"npm run build-lit-ssr -- --runtime --path {quote(str(path))} {f"--props '{quote(encodeProps(props))}'" if props else ''}"
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Remove initially added command from stdout, only return rendered html element
    htmlStartIndex = result.stdout.find('<div data-comment="ssr-component">')
    return result.stdout[htmlStartIndex:] if htmlStartIndex > -1 else ""


def encodeProps(props):
    jsonString = json.dumps(props)
    return base64.b64encode(jsonString.encode("utf-8")).decode()
