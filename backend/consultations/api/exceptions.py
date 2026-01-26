from rest_framework.exceptions import APIException


class PreconditionRequired(APIException):
    status_code = 428
    default_detail = "If-Match header required"
    default_code = "precondition_required"


class PreconditionFailed(APIException):
    status_code = 412
    default_detail = "Version mismatch"
    default_code = "precondition_failed"
