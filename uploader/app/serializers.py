# myapp/serializers.py
from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'title', 'video', 'uploaded_at', 'upload_status']
        read_only_fields = ['upload_status','uploaded_at']

