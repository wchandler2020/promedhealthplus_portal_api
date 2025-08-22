from .models import SalesRep
from rest_framework import serializers

class SalesRepSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRep
        fields = ['id', 'name', 'email', 'phone']