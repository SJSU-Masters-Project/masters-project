import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .mongo import get_database

def health(request):
    try:
        get_database().command("ping")
        return JsonResponse({"status": "ok", "mongodb": "connected"})
    except Exception as exc:
        return JsonResponse({"status": "degraded", "mongodb": "unavailable", "detail": str(exc)}, status=503)

@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)
    payload = json.loads(request.body or "{}")
    role = payload.get("role")
    if role not in {"company", "candidate"}:
        return JsonResponse({"detail": "role must be company or candidate"}, status=400)
    # Placeholder session response; replace with real auth once user schema is finalized.
    return JsonResponse({"user": {"email": payload.get("email", ""), "role": role}, "token": "development-token"})

def jobs(request):
    try:
        records = list(get_database().jobs.find({}, {"_id": 0}).limit(50))
        return JsonResponse({"jobs": records})
    except Exception as exc:
        return JsonResponse({"jobs": [], "detail": str(exc)}, status=503)

