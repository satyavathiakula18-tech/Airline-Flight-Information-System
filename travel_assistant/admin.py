
from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "created_at",
    )

    list_filter = (
        "role",
        "created_at",
    )

    search_fields = (
        "user__username",
        "message",
    )

    readonly_fields = (
        "created_at",
    )
