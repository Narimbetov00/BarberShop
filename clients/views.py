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
from django.db.models import Count,Sum
from django.db.models.functions import TruncDay,TruncMonth
from rest_framework.views import APIView
from django.utils.timezone import now
from asgiref.sync import async_to_sync
from dotenv import load_dotenv
load_dotenv()
import os
import aiohttp
import asyncio

async def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    async with aiohttp.ClientSession() as session: 
        async with session.post(url, json=data) as response:
            return await response.json()


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
            username_tg = f"https://t.me/{username_tg}",
            phone=phone,
            queue=next_queue,
            time_is_up=time_is_up,
            price= 15000
        )
        serialized_client = ClientSerializer(client).data 
        return Response(data={"message":"success","data":serialized_client}, status=status.HTTP_201_CREATED)

class ClientRAPIView(RetrieveUpdateDestroyAPIView):
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
                "errors": ["Bunday id ga iye paydalaniwshi tabilmadi"]
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
                "errors": ["Bunday id ga iye paydalaniwshi tabilmadi"]
            }, status=status.HTTP_404_NOT_FOUND) 
    
    def put(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        

        try:
            next_client = Client.objects.filter(is_finished=False).order_by("queue").first()
            if not next_client or next_client.chat_id != pk:
                return Response({
                    "message": "Error",
                    "errors": ["Siz Naduris Id jiberdiniz"]
                }, status=status.HTTP_400_BAD_REQUEST)

            next_client.is_finished = True
            is_free = request.data.get("is_free", False)

            if is_free:
                next_client.price = 0
                next_client.if_free = True
            next_client.save()

            next_in_line = Client.objects.filter(is_finished=False).order_by("queue").first()
            if next_in_line:
                chat_id = next_in_line.chat_id
                message = "Sizdi nawbatiniz keldi! Tez arada kirin."
                

                async_to_sync(send_telegram_message)(chat_id, message)

            return Response({
                "message": "success",
                "data": ClientSerializer(next_client).data
            }, status=status.HTTP_200_OK)

        except Client.DoesNotExist:
            return Response({
                "message": "Error",
                "errors": ["Bunday id ga iye paydalaniwshi tabilmadi"]
            }, status=status.HTTP_404_NOT_FOUND)

class ClientYearGet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    

    def get(self, request):
        year = request.GET.get('year')
        data_type = request.GET.get('type')

        if not year:
            return Response(
                {'message': 'error', 'errors': ['Year is required']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if data_type not in ['amount', 'count']:
            return Response(
                {'message': 'error', 'errors': ['Invalid type parameter. Use "amount" or "count".']},
                status=status.HTTP_400_BAD_REQUEST
            )
        

        try:
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year) + 1, 1, 1)

            if data_type == 'amount':
                total_amount = Client.objects.filter(
                    created_at__gte=start_date,
                    created_at__lt=end_date,
                    is_finished=True,
                ).aggregate(total=Sum('price'))['total'] or 0

                result = {'date': year, 'total': total_amount}

            else:  # data_type == 'count'
                total_count = Client.objects.filter(
                    created_at__gte=start_date,
                    created_at__lt=end_date,
                    is_finished=True,
                ).aggregate(count=Count('id'))['count'] or 0
                result = {'date': year, 'total': total_count}

           
            return Response(
                {'data':result},
                status=status.HTTP_200_OK
            )

        except ValueError:
            return Response(
                {'message': 'error', 'errors': ['Invalid year format']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class ClientMonthGet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        year = request.GET.get('year')
        data_type = request.GET.get('type') 

        if not year:
            return Response(
                {'message': 'error', 'errors': ['Year is required']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if data_type not in ['amount', 'count']:
            return Response(
                {'message': 'error', 'errors': ['Invalid type parameter. Use "amount" or "count".']},
                status=status.HTTP_400_BAD_REQUEST
            )
        

        try:
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year) + 1, 1, 1)

            monthly_data = []
            for month in range(1, 13):
                start_of_month = datetime(int(year), month, 1)
                end_of_month = datetime(int(year), month + 1, 1) if month != 12 else end_date

                if data_type == 'amount':
                    total_amount = Client.objects.filter(
                        created_at__gte=start_of_month,
                        created_at__lt=end_of_month,
                        is_finished=True,
                    ).aggregate(total=Sum('price'))['total'] or 0
        
                    monthly_data.append({'date': month, 'total': total_amount})

                else:  # data_type == 'count'
                    total_count = Client.objects.filter(
                        created_at__gte=start_of_month,
                        created_at__lt=end_of_month,
                        is_finished=True,
                    ).aggregate(count=Count('id'))['count'] or 0

                    monthly_data.append({'date': month, 'total': total_count})

            return Response(
                {'data':  monthly_data},
                status=status.HTTP_200_OK
            )

        except ValueError:
            return Response(
                {'message': 'error', 'errors': ['Invalid year format']},
                status=status.HTTP_400_BAD_REQUEST
            )

class ClientDayGet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        year = request.GET.get('year')  
        month = request.GET.get('month') 
        data_type = request.GET.get('type')  

        if not year or not month:
            return Response(
                {'message': 'error', 'errors': ['Year and Month are required']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if data_type not in ['amount', 'count']:
            return Response(
                {'message': 'error', 'errors': ['Invalid type parameter. Use "amount" or "count".']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        

        try:
            start_date = datetime(int(year), int(month), 1)

            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1)
            else:
                end_date = datetime(int(year), int(month) + 1, 1)

            num_days = (end_date - start_date).days

            results = []

            for i in range(num_days):
                day = start_date + timedelta(days=i)
                day_end = day + timedelta(days=1)

                if data_type == 'amount':
                
                    total_amount = Client.objects.filter(
                        created_at__gte=day,
                        created_at__lt=day_end,
                        is_finished=True,
                    ).aggregate(total=Sum('price'))['total'] or 0
                
                    result = {'date': int(day.strftime('%d')), 'total': total_amount}

                else:  # data_type == 'count'
                    total_count = Client.objects.filter(
                        created_at__gte=day,
                        created_at__lt=day_end,
                        is_finished=True,
                    ).aggregate(count=Count('id'))['count'] or 0

                    result = {'date': int(day.strftime('%d')), 'total': total_count}

                results.append(result)

            return Response(
                {'data': results},
                status=status.HTTP_200_OK
            )

        except ValueError:
            return Response(
                {'message': 'error', 'errors': ['Invalid year or month format']},
                status=status.HTTP_400_BAD_REQUEST
            )

class ClientTodayGet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = datetime.today()

        year = request.GET.get('year', today.year)
  
        try:
            start_date = datetime(int(year), today.month, today.day) 
            end_date = start_date + timedelta(days=1) 

        
            total_amount_uzs = Client.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                is_finished=True,
            ).aggregate(total=Sum('price'))['total'] or 0

           

        
            total_count = Client.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                is_finished=True,
            ).aggregate(count=Count('id'))['count'] or 0

            result = {'date': today.strftime('%Y-%m-%d'),'total_amount':total_amount_uzs, 'total_count': total_count}

            return Response(
                {'data': result},
                status=status.HTTP_200_OK
            )
        except ValueError:
            return Response(
                {'message': 'error', 'errors': ['Invalid date format']},
                status=status.HTTP_400_BAD_REQUEST
            )
       