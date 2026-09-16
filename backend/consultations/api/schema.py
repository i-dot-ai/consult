from django.conf import settings


def hide_disabled_v2_endpoints(endpoints, **kwargs):
    # drf-spectacular builds the schema by walking the URLconf statically and
    # never runs the DataSetupV2Enabled permission, so without this the V2
    # routes stay in the schema even while the flag gates them off at request
    # time. Drop them here so the schema matches what's actually reachable.
    if settings.DATA_SETUP_V2_ENABLED:
        return endpoints
    return [endpoint for endpoint in endpoints if not endpoint[0].startswith("/api/v2/")]
