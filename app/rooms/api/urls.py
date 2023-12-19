from django.urls import include, path

urlpatterns = [
    path('v1/', include('rooms.api.v1.urls')),
]
