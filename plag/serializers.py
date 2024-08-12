# # serializers.py
from rest_framework import serializers
from .models import User, PlagCheck, UsageStat
from .models import PlagData



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    
class PlagCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlagCheck
        fields = '__all__'

class PlagDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlagData
        fields = '__all__'

class UsageStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageStat
        fields ='__all__'
