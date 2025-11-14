# bazbiapacking/serializers.py
from rest_framework import serializers

class ItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    length = serializers.FloatField()
    width = serializers.FloatField()
    height = serializers.FloatField()
    weight = serializers.FloatField(required=False, default=0)

class PackingRequestSerializer(serializers.Serializer):
    items = ItemSerializer(many=True)
