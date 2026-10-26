from rest_framework import serializers


class HealthOut(serializers.Serializer):
    status = serializers.CharField()
    mongodb = serializers.CharField()
    version = serializers.CharField()
    detail = serializers.CharField(required=False)


class MeOut(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    created_at = serializers.CharField()


class ErrorDetail(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)


class ErrorOut(serializers.Serializer):
    error = ErrorDetail()
