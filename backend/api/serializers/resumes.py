from rest_framework import serializers


class ResumeUploadIn(serializers.Serializer):
    file = serializers.FileField()


class ResumeOut(serializers.Serializer):
    id = serializers.CharField()
    filename = serializers.CharField()
    content_type = serializers.CharField()
    size_bytes = serializers.IntegerField()
    text_status = serializers.CharField()
    created_at = serializers.CharField()


class ResumeDetailOut(ResumeOut):
    text_chars = serializers.IntegerField()


class ResumeListOut(serializers.Serializer):
    items = ResumeOut(many=True)
    total = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
