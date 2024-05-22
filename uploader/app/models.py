# models.py
from django.db import models


class Video(models.Model):
    UPLOAD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('uploading', 'Uploading'),
        ('uploaded', 'Uploaded'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=255)
    video = models.FileField(upload_to='')  # Initially uploaded to the server
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload_status = models.CharField(max_length=10, choices=UPLOAD_STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return self.title
