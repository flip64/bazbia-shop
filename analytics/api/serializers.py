from rest_framework import serializers

from analytics.models import SiteEvent


class SiteEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteEvent
        fields = (
            "event_type",
            "path",
            "page_url",
            "referrer",
            "source",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "product",
            "variant",
            "visitor_id",
            "metadata",
        )

    def validate_metadata(self, value):
        return value or {}
