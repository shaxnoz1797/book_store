from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'phone_number', 'address', 'password')
        extra_kwargs = {
            'password': {'write_only': True} # Parol faqat yozish uchun, uni qaytarib ko'rsatmaymiz
        }

    def create(self, validated_data):
        # Parolni xavfsiz (hash qilingan) saqlash uchun
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user