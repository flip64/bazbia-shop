from rest_framework import serializers


class TorobRequestSerializer(serializers.Serializer):
    page = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    sort = serializers.ChoiceField(
        required=False,
        choices=(
            "date_added_desc",
            "date_updated_desc",
        ),
    )

    page_urls = serializers.ListField(
        required=False,
        allow_empty=False,
        child=serializers.URLField(
            max_length=1500,
        ),
    )

    page_uniques = serializers.ListField(
        required=False,
        allow_empty=False,
        child=serializers.CharField(
            max_length=200,
            allow_blank=False,
            trim_whitespace=True,
        ),
    )

    def validate(self, attrs):
        self._validate_unknown_fields()

        has_page = "page" in attrs
        has_sort = "sort" in attrs
        has_page_urls = "page_urls" in attrs
        has_page_uniques = "page_uniques" in attrs

        has_pagination_mode = has_page or has_sort

        modes_count = sum(
            (
                has_pagination_mode,
                has_page_urls,
                has_page_uniques,
            )
        )

        if modes_count == 0:
            raise serializers.ValidationError(
                "No valid parameters were provided."
            )

        if modes_count > 1:
            raise serializers.ValidationError(
                "Only one request mode can be provided."
            )

        if has_pagination_mode:
            if not has_page:
                raise serializers.ValidationError(
                    "page parameter is not provided"
                )

            if not has_sort:
                raise serializers.ValidationError(
                    "sort parameter is not provided"
                )

        return attrs

    def _validate_unknown_fields(self):
        if not isinstance(self.initial_data, dict):
            raise serializers.ValidationError(
                "Request body must be a JSON object."
            )

        allowed_fields = {
            "page",
            "sort",
            "page_urls",
            "page_uniques",
        }

        unknown_fields = (
            set(self.initial_data.keys()) - allowed_fields
        )

        if unknown_fields:
            fields = ", ".join(sorted(unknown_fields))

            raise serializers.ValidationError(
                f"Unknown parameter(s): {fields}"
            )

    @property
    def request_mode(self):
        data = self.validated_data

        if "page_urls" in data:
            return "page_urls"

        if "page_uniques" in data:
            return "page_uniques"

        return "pagination"
