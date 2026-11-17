from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from consultations.api_v2.pagination import BespokePagination, QuestionPagination


def _request(query_string=""):
    return Request(APIRequestFactory().get(f"/{query_string}"))


def test_base_pagination_has_no_search_behaviour():
    """The foundation stays inert even when clients send searchMode params."""
    pagination = BespokePagination()

    assert pagination.get_search_mode(_request("?searchMode=representative")) is None
    assert pagination.get_page_size(_request("?searchMode=representative")) == 100
    assert pagination.get_page_size(_request()) == 100


def test_response_pagination_representative_mode_caps_page_size():
    pagination = BespokePagination()
    pagination.search_mode_field = "searchMode"
    pagination.representative_search_mode = "representative"

    assert pagination.get_search_mode(_request("?searchMode=representative")) == "representative"
    assert pagination.get_page_size(_request("?searchMode=representative")) == 10
    assert pagination.get_page_size(_request()) == 100


def test_surface_subclasses_declare_their_contract():
    from consultations.api_v2.pagination import ResponsePagination

    assert ResponsePagination.results_key == "all_respondents"
    assert ResponsePagination.search_mode_field == "searchMode"

    assert QuestionPagination.results_key == "results"
    assert QuestionPagination.page_size == 500
    assert QuestionPagination.search_mode_field is None
