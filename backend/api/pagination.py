from rest_framework import serializers


class PageParams(serializers.Serializer):
    """Validate ``limit`` and ``offset`` query parameters.

    ``limit`` defaults to 20 and must be between 1 and 100.
    ``offset`` defaults to 0 and must be >= 0.
    """

    limit = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)
    offset = serializers.IntegerField(required=False, default=0, min_value=0)


def parse_page_params(query_params) -> dict:
    """Validate query params and return ``{"limit": int, "offset": int}``.

    Raises DRF ``ValidationError`` (400 ``validation_error``) on bad values.
    """
    serializer = PageParams(data=query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def page_response(items: list, total: int, params: dict) -> dict:
    """Standard list envelope: ``{"items", "total", "limit", "offset"}``."""
    return {
        "items": items,
        "total": total,
        "limit": params["limit"],
        "offset": params["offset"],
    }
