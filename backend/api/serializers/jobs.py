from rest_framework import serializers

WORK_MODES = ["on_site", "hybrid", "remote"]
EMPLOYMENT_TYPES = ["full_time", "part_time", "internship", "contract", "co_op"]


class SkillIn(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=100, trim_whitespace=True)
    required = serializers.BooleanField()


class SkillOut(serializers.Serializer):
    name = serializers.CharField()
    required = serializers.BooleanField()


def _validate_skills(skills):
    if not (1 <= len(skills) <= 50):
        raise serializers.ValidationError("skills must hold 1 to 50 items.")
    seen = set()
    has_required = False
    for s in skills:
        lower = s["name"].strip().lower()
        if lower in seen:
            raise serializers.ValidationError("Skill names must be unique ignoring case.")
        seen.add(lower)
        if s["required"]:
            has_required = True
    if not has_required:
        raise serializers.ValidationError("At least one skill must be required.")
    return skills


class JobCreateIn(serializers.Serializer):
    title = serializers.CharField(min_length=3, max_length=150, trim_whitespace=True)
    description = serializers.CharField(min_length=50, max_length=20000)
    location = serializers.CharField(max_length=200, allow_blank=True, trim_whitespace=True)
    work_mode = serializers.ChoiceField(choices=WORK_MODES)
    employment_type = serializers.ChoiceField(choices=EMPLOYMENT_TYPES)
    skills = SkillIn(many=True)
    openings = serializers.IntegerField(min_value=1, max_value=100)

    def validate_skills(self, value):
        return _validate_skills(value)


class JobPatchIn(serializers.Serializer):
    title = serializers.CharField(
        required=False, min_length=3, max_length=150, trim_whitespace=True
    )
    description = serializers.CharField(required=False, min_length=50, max_length=20000)
    location = serializers.CharField(
        required=False, max_length=200, allow_blank=True, trim_whitespace=True
    )
    work_mode = serializers.ChoiceField(required=False, choices=WORK_MODES)
    employment_type = serializers.ChoiceField(required=False, choices=EMPLOYMENT_TYPES)
    skills = SkillIn(many=True, required=False)
    openings = serializers.IntegerField(required=False, min_value=1, max_value=100)

    def validate_skills(self, value):
        return _validate_skills(value)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one field is required.")
        return attrs


class CompanyRef(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class JobOut(serializers.Serializer):
    id = serializers.CharField()
    company = CompanyRef()
    title = serializers.CharField()
    description = serializers.CharField()
    location = serializers.CharField(allow_null=True)
    work_mode = serializers.CharField()
    employment_type = serializers.CharField()
    skills = SkillOut(many=True)
    openings = serializers.IntegerField()
    status = serializers.CharField()
    published_at = serializers.CharField(allow_null=True)
    closed_at = serializers.CharField(allow_null=True)
    created_at = serializers.CharField()
    updated_at = serializers.CharField()


class JobListOut(serializers.Serializer):
    items = JobOut(many=True)
    total = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
