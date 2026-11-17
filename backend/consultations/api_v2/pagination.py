import uuid

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class BespokePagination(PageNumberPagination):
    """Cursor-style pagination foundation for result-set listings.

    Emits `has_more_pages` / `next_cursor`, a first-page-only `total_count`,
    and the page items under `results_key`. Surfaces tailor `page_size`,
    `results_key`, and the search-mode vocabulary via subclass attributes;
    with `search_mode_field = None` (the default) no search-driven behaviour
    applies and cursors are plain id-keyset.
    """

    results_key = "results"

    search_mode_field: str | None = None
    representative_search_mode: str | None = None
    offset_cursor_search_mode: str | None = None

    representative_page_size = 10

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_search_mode(self, request):
        if not self.search_mode_field:
            return None
        return request.query_params.get(self.search_mode_field)

    def get_page_size(self, request):
        search_mode = self.get_search_mode(request)
        if search_mode and search_mode == self.representative_search_mode:
            return min(self.representative_page_size, self.max_page_size)
        return super().get_page_size(request)

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        search_mode = self.get_search_mode(request)
        self._offset_cursor = bool(search_mode) and (
            search_mode == self.offset_cursor_search_mode
        )
        page_size = self.get_page_size(request)
        cursor = request.query_params.get("cursor")

        # Load-more requests skip the full-table COUNT.
        self._filtered_count = queryset.count() if not cursor else None

        if cursor:
            if self._offset_cursor:
                # Offset cursors power orderings with no stable row key.
                try:
                    self._cursor_offset = int(cursor)
                except ValueError:
                    self._cursor_offset = 0
                items = list(queryset[self._cursor_offset : self._cursor_offset + page_size + 1])
            else:
                # Keyset: seek past the id encoded in the cursor.
                self._cursor_offset = 0
                try:
                    queryset = queryset.filter(id__gt=uuid.UUID(cursor))
                except ValueError:
                    pass  # Malformed cursors serve the first page.
                items = list(queryset[: page_size + 1])
        else:
            self._cursor_offset = 0
            items = list(queryset[: page_size + 1])

        self._has_next = len(items) > page_size
        self._page = items[:page_size] if self._has_next else items
        return self._page

    def get_paginated_response(self, data):
        next_cursor = None
        if self._has_next and self._page:
            if self._offset_cursor:
                next_cursor = str(self._cursor_offset + len(self._page))
            else:
                next_cursor = str(self._page[-1].id)

        result = {
            "has_more_pages": self._has_next,
            "next_cursor": next_cursor,
            self.results_key: data,
        }
        if self._filtered_count is not None:
            result["total_count"] = self._filtered_count
        return Response(result)


class ResponsePagination(BespokePagination):
    """Response listings: legacy `all_respondents` envelope key and the
    semantic / representative search-mode vocabulary."""

    results_key = "all_respondents"

    search_mode_field = "searchMode"
    offset_cursor_search_mode = "semantic"
    representative_search_mode = "representative"


class QuestionPagination(BespokePagination):
    """Question listings: larger pages under the standard `results` key.

    Not yet wired to the v2 questions endpoint — its consumers expect a bare
    array today; flip `pagination_class` when the frontend is ready for the
    envelope.
    """

    page_size = 500
