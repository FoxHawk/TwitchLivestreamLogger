from .models import TwitchEvent
from Common.models import Channel
from django.http import HttpRequest
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

def record_event(request: HttpRequest):
    event_id = request.headers.get("Twitch-Eventsub-Message-Id")
    event_timestamp_string = request.headers.get("Twitch-Eventsub-Message-Timestamp")
    event_type = request.headers.get("Twitch-Eventsub-Message-Type")

    if not event_id or not event_timestamp_string or not event_type:
        logger.warning("Got an event request with missing headers")
        logger.debug(f"event_id is {event_id}")
        logger.debug(f"event_timestamp_string is {event_timestamp_string}")
        logger.debug(f"event_type is {event_type}")
        return False
    
    event_timestamp_string = event_timestamp_string[:26] + "Z"
    
    if TwitchEvent.objects.filter(id=event_id).exists():
        logger.debug(f"Event {event_id} already logged. skipping")
        return False

    event_timestamp = datetime.strptime(event_timestamp_string, "%Y-%m-%dT%H:%M:%S.%fZ")

    current_timestamp = datetime.now()

    if current_timestamp - event_timestamp > timedelta(minutes=10):
        logger.debug(f"Event {event_id} was recieved over 10 minutes past it's creation time")
        return False
    
    event = TwitchEvent()

    event.id = event_id
    event.type = event_type

    event.save()

    return True

def handle_challenge(request: HttpRequest) -> str | None:
    event_type = request.headers.get("Twitch-Eventsub-Message-Type")

    if event_type == "webhook_callback_verification":
        logger.debug("Got a challenge request")

        body = json.loads(request.body)
        subscription = body['subscription']
        user_id = subscription['condition']['broadcaster_user_id']
        event_type = subscription['type']
        challenge = body['challenge']

        if not Channel.objects.filter(user_id=user_id).exists():
            logger.warning(f"Got an event challenge request for a channel we aren't following: {user_id}")
            raise Exception(f"Got an event challenge request for a channel we aren't following: {user_id}")

        valid_types = ['stream.online', 'stream.offline', 'channel.update']

        if event_type not in valid_types:
            logger.warning(f"Got an event challenge for an unexpected event type: {event_type}")
            raise Exception(f"Got an event challenge for an unexpected event type: {event_type}")

        return challenge
    else:
        logger.debug("Event is not a challenge request")
        return None