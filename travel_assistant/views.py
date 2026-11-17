
import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .models import ChatMessage
from .assistant_engine import get_response

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@csrf_protect
def chat_api(request):

    # Return saved conversation history.
    if request.method == "GET":
        if not request.user.is_authenticated:
            return JsonResponse({"messages": []})

        history = ChatMessage.objects.filter(
            user=request.user
        ).order_by("-created_at")[:30]

        history = list(reversed(history))

        return JsonResponse({
            "messages": [
                {
                    "role": item.role,
                    "message": item.message,
                }
                for item in history
            ]
        })

    # Read the user's message.
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Invalid request."},
            status=400,
        )

    message = str(data.get("message", "")).strip()

    if not message:
        return JsonResponse(
            {"error": "Please enter a message."},
            status=400,
        )

    if len(message) > 1000:
        return JsonResponse(
            {"error": "Message must be under 1000 characters."},
            status=400,
        )

    try:
        answer = get_response(message, request.user)

        # Save conversations for registered users.
        if request.user.is_authenticated:
            ChatMessage.objects.create(
                user=request.user,
                role="user",
                message=message,
            )

            ChatMessage.objects.create(
                user=request.user,
                role="assistant",
                message=answer,
            )

        return JsonResponse({
            "reply": answer,
        })

    except Exception:
        logger.exception("AeroMate assistant error")

        return JsonResponse({
            "error": "Sorry, something went wrong. Please try again."
        }, status=500)
