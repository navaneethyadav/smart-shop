from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        unread = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        return {
            'unread_count': unread.count(),
            'notifications': unread[:5]
        }
    return {
        'unread_count': 0,
        'notifications': []
    }
