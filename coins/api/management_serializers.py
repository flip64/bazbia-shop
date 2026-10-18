from rest_framework import serializers


class AssemblySource(serializers.Serializer):
    item_id = serializers.IntegerField(min_value=1)
    variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class AssemblyInput(serializers.Serializer):
    pack_variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    request_key = serializers.CharField(max_length=100, allow_blank=False)
    sources = AssemblySource(many=True, allow_empty=False)
