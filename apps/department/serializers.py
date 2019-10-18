from rest_framework import serializers
from .models import Depart


class DeptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depart
        fields = "__all__"