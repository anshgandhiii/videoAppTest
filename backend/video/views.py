from rest_framework import viewsets
from rest_framework.response import Response
from .models import Room
from .serializers import RoomSerializer
import uuid

class RoomViewSet(viewsets.ViewSet):
    def create(self, request):
        room_id = str(uuid.uuid4())
        Room.objects.create(room_id=room_id)
        return Response({'room_id': room_id})

    def retrieve(self, request, pk=None):
        room = Room.objects.get(room_id=pk)
        serializer = RoomSerializer(room)
        return Response(serializer.data)