from django.conf import settings
import requests
import logging

from .models import Channel

logger = logging.getLogger(__name__)

def get_twitch_oauth_token():
    params = {
        "client_id": settings.TWITCH_CLIENT_ID,
        "client_secret": settings.TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    response = requests.post("https://id.twitch.tv/oauth2/token", params=params)

    if response.status_code != 200:
        logger.error(f"Error getting access token: {response.status_code} - {response.reason}")
        logger.error(response.json())
        return None
    
    data = response.json()
    access_token = data["access_token"]

    return access_token

def do_twitch_api_get(url: str, expected_status: int = 200):
    headers = _get_headers()

    response = requests.get(url, headers=headers)

    if response.status_code != expected_status:
            logger.error(f"Error doing get request to '{url}'. {response.status_code} - {response.reason}")
            logger.error(response.json())
            raise Exception(f"Error doing get request to '{url}'. {response.status_code} - {response.reason}")

    return response.json()

def do_twitch_api_post(url: str, data, expected_status: int = 200):
    headers = _get_headers()

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != expected_status:
            logger.error(f"Error doing get request to '{url}'. {response.status_code} - {response.reason}")
            logger.error(response.json())
            raise Exception(f"Error doing get request to '{url}'. {response.status_code} - {response.reason}")

    return response.json()

def do_twitch_api_delete(url, expected_status: int = 204):
    headers = _get_headers()

    response = requests.delete(url, headers=headers)

    if response.status_code != expected_status:
        logger.error(f"Error doing delete request to {url}. {response.status_code} - {response.reason}")
        logger.error(response.json())
        raise Exception(f"Error doing delete request to {url}. {response.status_code} - {response.reason}")

def _get_headers():
    return {
        "Client-ID": settings.TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {get_twitch_oauth_token()}"
    }

def unsubscribe_from_channel(channel: Channel):
    event_ids = [
        channel.online_event_id,
        channel.offline_event_id,
        channel.update_event_id
    ]

    for event_id in event_ids:
        try:
            do_twitch_api_delete(f"https://api.twitch.tv/helix/eventsub/subscriptions?id={event_id}")
        except Exception as e:
            logger.warning(f"Failed to unsubscribe from event {event_id} for channel {channel.username}: {str(e)}. Continuing...")

def subscribe_to_channel(channel: Channel):
        body = {
            "type": "",
            "version": "1",
            "condition": {
                "user_id": channel.user_id
            },
            "transport": {
                "method": "webhook",
                "callback": "https://twitch.foxhawk.co.uk/PubSub",
                "secret": settings.TWITCH_EVENT_SECRET
            }
        }

        event_mapping = {
            "channel.update": "update_event_id",
            "stream.online": "online_event_id",
            "stream.offline": "offline_event_id"
        }

        try:
            for type, field in event_mapping.items():
                body["type"] = type
                data = do_twitch_api_post("https://api.twitch.tv/helix/eventsub/subscriptions", body, 202)

                if data.get("data") and len(data["data"]) > 0:
                    setattr(channel, field, data["data"][0]["id"])
        except Exception:
            logger.error(f"Error subscribing to twitch events for channel {channel.username}")
            unsubscribe_from_channel(channel)
            raise