from django.shortcuts import render
from django.http import HttpRequest
from Common.models import Livestream
import logging

logger = logging.getLogger(__name__)

def index(request: HttpRequest):
    latest_streams = Livestream.objects.order_by("-started")[:10]
    logger.debug(f"Got {len(latest_streams)} streams")
    context = {"latest_streams": latest_streams}
    return render(request, "index.html", context)