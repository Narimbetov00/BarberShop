from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id","chat_id","username_tg","phone","queue","time_is_up","price","if_free","created_at","updated_at","is_finished"]

    
