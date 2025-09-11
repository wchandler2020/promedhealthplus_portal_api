from django.shortcuts import render
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
import notifications.serializers as api_serializers
import notifications.models as api_models



class NotificationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = api_serializers.NotificationSerializer
    
    def get_queryset(self):
        return api_models.Notification.objects.filter(recipient=self.request.user)
    
class MarkNotificationReadView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = api_models.Notification.objects.all()
    serializer_class = api_serializers.NotificationSerializer  # Assuming it includes `is_read` field

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        if notification.recipient != request.user:
            raise PermissionDenied("You do not have permission to mark this notification.")

        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'}, status=status.HTTP_200_OK)
    
class UnreadNotificationCountView(generics.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = api_models.Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})
