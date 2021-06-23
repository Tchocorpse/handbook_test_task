from rest_framework import serializers
from .models import Handbook, HandbookElement, HandbookVersion


class HandbookModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Handbook
        fields = "__all__"


class HandbookVersionSerializerDeep(serializers.ModelSerializer):
    class Meta:
        model = HandbookVersion
        fields = "__all__"
        depth = 1


class HandbookVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandbookVersion
        fields = "__all__"


class HandbookFullSerializer(serializers.ModelSerializer):
    versions = HandbookVersionSerializer(many=True)

    class Meta:
        model = Handbook
        fields = ("id", "name", "short_name", "description", "versions")


class HandbookElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandbookElement
        fields = "__all__"
