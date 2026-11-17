
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notification_list(request):

    notifications = Notification.objects.filter(
        user=request.user
    )

    unread_count = notifications.filter(is_read=False).count()

    return render(
        request,
        'notifications/notification_list.html',
        {
            'notifications': notifications,
            'unread_count': unread_count
        }
    )


@login_required
@require_POST
def mark_notification_read(request, notification_id):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    notification.is_read = True
    notification.save(update_fields=['is_read'])

    return redirect('notification_list')


@login_required
@require_POST
def mark_all_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect('notification_list')


# Create your views here.
