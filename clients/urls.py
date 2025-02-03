from django.urls import path
from .views import ClientApiView,ClientRAPIView

urlpatterns = [
    path("clients",ClientApiView.as_view()),
    path("clients/<int:pk>",ClientRAPIView.as_view())

]