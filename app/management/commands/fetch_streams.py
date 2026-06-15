from django.core.management.base import BaseCommand
from Common.models import Livestream, Channel
from Common.utils import do_twitch_api_get
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = ""
	
    def handle(self, *args, **options):
        channels = Channel.objects.all()

        if len(channels) == 0:
            print("No channels stored. Exiting")
            return

        for c in channels:
            url = f"https://api.twitch.tv/helix/videos?user_id={c.user_id}&type=archive"
            self.fetch_and_store_livestreams(url)

    def fetch_and_store_livestreams(self, url):
        pagination_token = ""

        while(True):
            self.stdout.write(f"Fetching streams...")

            full_url = url

            self.stdout.write(full_url)

            if pagination_token:
                full_url += "&after=" + pagination_token

            data = do_twitch_api_get(full_url)

            self.stdout.write(self.style.SUCCESS("Request completed"))

            if not data["data"]:
                self.stdout.write(self.style.SUCCESS("End of channel's vods"))
                break

            self.store_livestreams(data)

            pagination_token = data["pagination"]["cursor"]

    def store_livestreams(self, data):
        if len(data["data"]) == 0:
            self.stdout.write(self.style.NOTICE("Request didn't contain any streams"))

        for vod in data["data"]:
            if Livestream.objects.filter(event_id=vod["stream_id"]).exists():
                self.stdout.write(f"Livestream '{vod["stream_id"]}' already recorded. Skipping")
                continue

            stream = Livestream()

            stream.channel = Channel.objects.get(pk=vod["user_id"])
            stream.id = vod["stream_id"]

            naive_date_time = datetime.strptime(vod["published_at"], "%Y-%m-%dT%H:%M:%SZ")
            stream.started = timezone.make_aware(naive_date_time)
            stream.title = vod["title"]
            
            duration = vod["duration"]

            if "h" in duration:
                parsed_duration = datetime.strptime(vod["duration"], "%Hh%Mm%Ss")
            elif "m" in duration:
                parsed_duration = datetime.strptime(vod["duration"], "%Mm%Ss")
            else:
                parsed_duration = datetime.strptime(vod["duration"], "%Ss")


            duration_timedelta = timedelta(hours=parsed_duration.hour, minutes=parsed_duration.minute, seconds=parsed_duration.second)

            stream.ended = stream.started + duration_timedelta

            stream.save()

            self.stdout.write(self.style.SUCCESS(f"Logged livestream: '{stream.channel.username}': '{stream.title}'"))