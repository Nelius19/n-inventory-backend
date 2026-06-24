from rest_framework import serializers
from .models import House, HouseMember

# 
class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ['id', 'name', 'invite_code']

# 
class HouseMemberSerializer(serializers.ModelSerializer):
    house = HouseSerializer()
    username = serializers.CharField(source='user.username')

    class Meta:
        model = HouseMember
        fields = ["id", "username", "role", "house"]
