# app/views.py
from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .models import Video
from .serializers import VideoSerializer
from .tasks import upload_video_to_s3
from drf_yasg.utils import swagger_auto_schema # type: ignore
from rest_framework.decorators import action


class VideoViewSet(viewsets.ViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    @swagger_auto_schema(
        request_body=VideoSerializer
        )
    @action(methods=['POST' ], detail=False)
    def upload(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            video = serializer.save(upload_status='pending')
            upload_video_to_s3.delay(video.id)  # Trigger the Celery task
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
