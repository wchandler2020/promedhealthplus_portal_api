from .models import Patient
from rest_framework import serializers

class PatientSerializer(serializers.ModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Patient
        fields = '__all__'
