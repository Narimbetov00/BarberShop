from rest_framework.decorators import api_view,permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny
from rest_framework.response import Response
from .serializers import ClientSerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import ListAPIView,RetrieveUpdateDestroyAPIView,ListCreateAPIView,CreateAPIView,RetrieveDestroyAPIView
from .models import Client
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDay,TruncMonth
from rest_framework.views import APIView
from django.utils.timezone import now



class ClientApiView(ListCreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdminUser()] 
        return [AllowAny()]  

    def get(self, request, *args, **kwargs):
        queue_param = request.query_params.get('queue')
        
        if queue_param:
            try:
                next_client = Client.objects.filter(is_finished=False).order_by('queue').first()
                if next_client:
                    serializer = self.get_serializer(next_client)
                    return Response({"data": serializer.data}, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "message": "Tabilmadi"
                    }, status=status.HTTP_404_NOT_FOUND)
            except Client.DoesNotExist:
                return Response({
                    "message": "Xatolik",
                    "errors": ["Not Found"]
                }, status=status.HTTP_404_NOT_FOUND)
        
        return super().get(request, *args, **kwargs)

    def create(self,request,*args,**kwargs):
        chat_id = request.data.get("chat_id")
        phone = request.data.get("phone")
        username_tg= request.data.get("username_tg")

        if not chat_id or not username_tg:
            return Response({"message":"chat_id yaki username kiritilmegen"},status=status.HTTP_400_BAD_REQUEST)

        existing_client = Client.objects.filter(chat_id=chat_id,is_finished=False).first()
        if existing_client:
            return Response({"message":"Siz alleqashan nawbet algansiz","data":ClientSerializer(existing_client).data},status=status.HTTP_400_BAD_REQUEST)
        last_active_client = Client.objects.filter(is_finished=False).order_by("-queue").first()

        if last_active_client:
            next_queue = last_active_client.queue + 1
            time_is_up = last_active_client.time_is_up + timedelta(minutes=20)
        else:
            next_queue = 1
            time_is_up = now() + timedelta(minutes=10) 

        client = Client.objects.create(
            chat_id=chat_id,
            username_tg = username_tg,
            phone=phone,
            queue=next_queue,
            time_is_up=time_is_up,
            price= 15000
        )
        serialized_client = ClientSerializer(client).data 
        return Response(data={"message":"success","data":serialized_client}, status=status.HTTP_201_CREATED)

class ClientRAPIView(RetrieveDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    lookup_field = "chat_id"
    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")  
        try:
            instance = self.get_queryset().get(chat_id=pk,is_finished=False) 
            serializer = self.get_serializer(instance)
            return Response({
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Client.DoesNotExist:  
            return Response({
                "message": "Error",
                "errors": ["Bunday chat_id ga iye paydalaniwshi tabilmadi"]
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self,request,*args,**kwargs):
        pk = kwargs.get("pk")
        try:
            instance = self.get_queryset().get(chat_id=pk,is_finished=False)
            instance.price = 0
            instance.is_finished = True
            instance.save()
            return Response({
                "message":"success"
            }, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({
                "message": "Error",
                "errors": ["Bunday chat_id ga iye paydalaniwshi tabilmadi"]
            }, status=status.HTTP_404_NOT_FOUND) 
