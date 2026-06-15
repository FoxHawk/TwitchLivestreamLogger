from django.db import models

# Create your models here.

class Channel(models.Model):
    user_id = models.CharField(max_length=200, primary_key=True)
    username = models.CharField(max_length=200)
    update_event_id = models.CharField(max_length=50)
    online_event_id = models.CharField(max_length=50)
    offline_event_id = models.CharField(max_length=50)
    
    def __str__(self) -> str:
        return self.username

class Livestream(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    started = models.DateTimeField()
    ended = models.DateTimeField(null=True)
    title = models.CharField(max_length=500)

    def __str__(self) -> str:
        return self.id
    
class LivestreamCategory(models.Model):
    id = models.AutoField(primary_key=True)
    livestream_id = models.ForeignKey(Livestream, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    changed_at = models.DateTimeField()