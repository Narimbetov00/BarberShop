from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from rest_framework_simplejwt.tokens import AccessToken


class LoginSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id','phone', 'password', 'token']

    def validate(self, data): # Validate fun
        phone = data.get("phone")
        password = data.get("password")

      
        user = authenticate(phone=phone, password=password)
       
        if user is None:
            raise serializers.ValidationError({"message":"Error","errors":["Invalid Phone or password."]})
        return {'user': user}
 