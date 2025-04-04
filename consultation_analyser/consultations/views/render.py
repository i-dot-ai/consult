import subprocess
import json
from shlex import quote
import base64


def renderLitSsr(path, props):
    result = subprocess.run( # nosec
        [f"npm run build-lit-ssr -- --runtime --path {quote(str(path))} {f"--props '{quote(encodeProps(props))}'" if props else ""}"],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Remove initially added command from stdout, only return rendered html element
    htmlStartIndex = result.stdout.find("<!-")
    return result.stdout[htmlStartIndex:] if result.stdout.find("<!-") > -1 else ""

def encodeProps(props):
    jsonString = json.dumps(props)
    return base64.b64encode(jsonString.encode("utf-8")).decode()