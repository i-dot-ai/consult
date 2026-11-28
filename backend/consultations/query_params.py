from uuid import UUID

from django import forms
from django_filters import Filter


class RepeatedValueField(forms.Field):
    """Collects every occurrence of a repeated query parameter, commas and all."""

    # The filter form reads the query string through the widget's value_from_datadict:
    # SelectMultiple uses getlist, the default TextInput keeps only the last value
    widget = forms.SelectMultiple

    def to_python(self, value):
        return list(value or [])


class RepeatedValueFilter(Filter):
    field_class = RepeatedValueField


def is_uuid(value: str) -> bool:
    try:
        UUID(str(value))
    except ValueError:
        return False
    return True
