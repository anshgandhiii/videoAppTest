from django.db import models

# Create your models here.
from django.db import models

class Room(models.Model):
    room_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.room_id
