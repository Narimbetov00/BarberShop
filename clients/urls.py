from django.urls import path
from .views import ClientApiView,ClientRAPIView,ClientDayGet,ClientMonthGet,ClientYearGet,ClientTodayGet

urlpatterns = [
    path("clients",ClientApiView.as_view()),
    path("clients/<int:pk>",ClientRAPIView.as_view()),
    path('client-by-year',ClientYearGet.as_view()),
    path('client-by-days',ClientDayGet.as_view()),
    path('client-by-month',ClientMonthGet.as_view()),
    path('client-by-today',ClientTodayGet.as_view())

]