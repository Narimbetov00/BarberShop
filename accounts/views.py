from rest_framework.decorators import api_view,permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import LoginSerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import ListAPIView,RetrieveUpdateDestroyAPIView,ListCreateAPIView
from .models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDay,TruncMonth
from rest_framework.views import APIView
from django.utils.timezone import now



@api_view(["POST"])
def login_view(request):
    if request.method == "POST":
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "data": {
                    "phone": user.phone,
                    "token": access_token,}
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)