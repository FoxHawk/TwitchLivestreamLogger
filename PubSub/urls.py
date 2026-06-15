from django.urls import path
from . import views

urlpatterns = [
	path("online", views.online, name="online"),
	path("offline", views.offline, name="offline"),
	path("updated", views.updated, name="updated")
]