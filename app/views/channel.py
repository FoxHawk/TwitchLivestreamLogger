from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpRequest
from django.views import View
import logging

from Common.models import Channel
from Common.utils import do_twitch_api_get, subscribe_to_channel, unsubscribe_from_channel

class ChannelView(View):
    logger = logging.getLogger(__name__)

    def get(self, request: HttpRequest):
        channels = Channel.objects.order_by("username")
        context = {"channels": channels}
        return render(request, "manage_streams.html", context)
    
    def post(self, request: HttpRequest):
        channel = request.POST.get("channel")

        if channel is None:
            self.logger.error("Error getting user details: channel was empty or missing")
            return HttpResponseBadRequest()
        
        data = do_twitch_api_get(f"https://api.twitch.tv/helix/users?login={channel}")

        user_id = data["data"][0]["id"]
        channel = data["data"][0]["display_name"]

        new_channel = Channel()
        new_channel.user_id = user_id
        new_channel.username = channel

        subscribe_to_channel(new_channel)

        new_channel.save()

        return HttpResponseRedirect("/add")

class DeleteChannelView(View):
    logger = logging.getLogger(__name__)

    def post(self, request: HttpRequest):
        if request.method != "POST":
            self.logger.error(f"Error: Tried to use {request.method} instead of POST for /delete")
            return HttpResponseBadRequest()
        
        username = request.POST.get("channel")

        if username is None:
            self.logger.error("Error: missing username")
            return HttpResponseBadRequest()
        
        channel = Channel.objects.filter(username=username).first()

        if channel is None:
            self.logger.error(f"Error: could not find channel '{username}' in database")
            return HttpResponseBadRequest()
        
        unsubscribe_from_channel(channel)
        
        channel.delete()

        return HttpResponseRedirect("/add")
