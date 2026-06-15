from django.http import HttpResponse, HttpRequest, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
import logging

from .utils import handle_challenge, record_event
from Common.models import Livestream, Channel, LivestreamCategory
from Common.utils import do_twitch_api_get

logger = logging.getLogger(__name__)

@csrf_exempt
def online(request: HttpRequest):
    logger.debug("Got stream online event")
    if not record_event(request):
        return HttpResponseBadRequest()
    
    challenge_response = handle_challenge(request)

    if challenge_response:
        return HttpResponse(challenge_response, content_type="text/plain")

    body = json.loads(request.body)
    event = body["event"]
    broadcaster_user_id = event["broadcaster_user_id"]
    stream_id = event["id"]
    started_at = datetime.fromisoformat(event["started_at"].replace("Z", "+00:00"))

    channel, _ = Channel.objects.get_or_create(
        user_id=broadcaster_user_id,
        defaults={"username": event["broadcaster_user_login"]}
    )

    logger.debug("Fetching stream info")

    stream_info = do_twitch_api_get(f"https://api.twitch.tv/helix/streams?user_id={broadcaster_user_id}")

    if len(stream_info["data"]) == 0:
        logger.warning(f"Got a stream online event for a stream that is probably offline Stream ID: '{broadcaster_user_id}'")
        return HttpResponse(status=204)

    logger.debug(f"Stream title: {stream_info["data"][0]["title"]}")
    logger.debug(f"Stream cagegory name: {stream_info["data"][0]["game_name"]}")
    title = stream_info["data"][0]["title"]
    category = stream_info["data"][0]["game_name"]

    livestream = Livestream(
        id=stream_id,
        channel=channel,
        started=started_at,
        title=title
    )
    livestream.save()

    LivestreamCategory.objects.create(
        livestream_id=livestream,
        category=category,
        changed_at=datetime.now().isoformat()
    )

    return HttpResponse(status=204)

@csrf_exempt
def offline(request: HttpRequest):
    logger.debug("Got a stream offline event request")
    
    if not record_event(request):
        return HttpResponseBadRequest()
    
    challenge_response = handle_challenge(request)

    if challenge_response:
        return HttpResponse(challenge_response, content_type="text/plain")
    
    body = json.loads(request.body)
    event = body["event"]
    user_id = event["broadcaster_user_id"]

    stream = Livestream.objects.filter(channel_id=user_id).order_by("-started").first()

    if stream is None:
        logger.warning(f"Offline event: Got an event for a channel we are not following: {user_id}")
        return HttpResponse(204)
    
    if stream.channel.user_id != user_id:
        logger.warning(f"Offline event: Got mismatched user ID. Stored: '{stream.channel.user_id}'. Event: '{user_id}'")
        return HttpResponse(204)
    
    stream.ended = datetime.now()

    stream.save()

    return HttpResponse(204)

@csrf_exempt
def updated(request: HttpRequest):
    if not record_event(request):
        return HttpResponseBadRequest()
    
    challenge_response = handle_challenge(request)

    if challenge_response:
        return HttpResponse(challenge_response, content_type="text/plain")
    
    body = json.loads(request.body)
    event = body["event"]
    user_id = event["broadcaster_user_id"]
    category = event["category_name"]

    stream = Livestream.objects.order_by("-started").filter(channel__user_id=user_id, ended__isnull=True).first()

    if not stream:
        logger.debug("Got stream updated event for a channel that isn't live. Ignoring")
        return HttpResponse(204)
    
    current_category = LivestreamCategory.objects.filter(livestream_id=stream.id).order_by("-changed_at").first()

    if not current_category:
        logger.error(f"Missing current category for stream {stream.id}")
        return HttpResponse(204)

    if category == current_category.category:
        # The category hasn't changed, so don't record anything
        return HttpResponse(204)
    
    new_category = LivestreamCategory(
        livestream_id=stream,
        category=category,
        changed_at=datetime.now()
    )

    new_category.save()

    return HttpResponse(204)