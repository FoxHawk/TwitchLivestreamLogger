from django.urls import path
# from . import views

from .views import index, channel

urlpatterns = [
	path("", index.index, name="index"),
	path("add", channel.ChannelView.as_view(), name="add"),
	path("delete", channel.DeleteChannelView.as_view(), name="delete")
]