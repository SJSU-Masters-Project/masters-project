from rest_framework import serializers


class CompanyIn(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=150, trim_whitespace=True)
    website = serializers.URLField(required=False, allow_blank=True)
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=5000, trim_whitespace=False
    )
    location = serializers.CharField(
        required=False, allow_blank=True, max_length=200, trim_whitespace=True
    )


class CompanyPatchIn(serializers.Serializer):
    name = serializers.CharField(required=False, min_length=2, max_length=150, trim_whitespace=True)
    website = serializers.URLField(required=False, allow_blank=True)
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=5000, trim_whitespace=False
    )
    location = serializers.CharField(
        required=False, allow_blank=True, max_length=200, trim_whitespace=True
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one field is required.")
        return attrs


class CompanyOut(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    website = serializers.CharField(allow_null=True, required=False)
    description = serializers.CharField(allow_null=True, required=False)
    location = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.CharField()
