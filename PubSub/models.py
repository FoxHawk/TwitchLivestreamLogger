from django.db import models

# Create your models here.

class TwitchEvent(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    type = models.CharField(max_length=15)
    
    def __str__(self) -> str:
        return self.id