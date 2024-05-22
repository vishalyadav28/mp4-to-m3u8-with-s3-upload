# import os
# import shutil
# import boto3
# import logging
# import uuid
# from datetime import datetime
# from django.conf import settings
# from .models import Video

# from celery import shared_task

# # Configure logging
# logger = logging.getLogger(__name__)

# @shared_task(bind=True, max_retries=3, default_retry_delay=60)
# def upload_video_to_s3(self, video_id):
#     video = Video.objects.get(id=video_id)
#     s3 = boto3.client('s3')

#     try:
#         # Extract title and trainer name
#         title = video.title.strip()
#         parts = title.split()
#         trainer_name = parts[-1]

#         # Create a unique folder using UUID
#         unique_folder_name = str(uuid.uuid4())
#         unique_folder_path = os.path.join(settings.MEDIA_ROOT, unique_folder_name)

#         # Create nested folder structure inside the unique folder
#         current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#         local_folder_path = os.path.join(unique_folder_path, trainer_name, current_datetime)
#         os.makedirs(local_folder_path, exist_ok=True)

#         # Move video file to the nested local folder
#         video_file_name = os.path.basename(video.video.name)
#         video_file_path = os.path.join(local_folder_path, video_file_name)
#         shutil.move(video.video.path, video_file_path)

#         # Construct the S3 folder path
#         s3_folder_path = f"{trainer_name}/{current_datetime}_{title}/"

#         # Upload video file to S3
#         logger.info(f"Uploading {video_file_path} to {s3_folder_path} in bucket {settings.AWS_STORAGE_BUCKET_NAME}")
#         s3.upload_file(video_file_path, settings.AWS_STORAGE_BUCKET_NAME, s3_folder_path + video_file_name)

#         # Update upload status
#         video.upload_status = 'uploaded'

#         # Delete the unique folder and its contents after successful upload
#         logger.info(f"Deleting unique folder: {unique_folder_path}")
#         shutil.rmtree(unique_folder_path)
#         logger.info(f"Unique folder {unique_folder_path} deleted successfully")

#     except Exception as e:
#         # If any error occurs during the process, mark the upload as failed and retry
#         logger.error(f"Error occurred: {e}")
#         video.upload_status = 'failed'
#         self.retry(exc=e)  # Retry the task

#     finally:
#         # Save the changes to the video object
#         video.save()

import os
import shutil
import subprocess
import boto3
import logging
import uuid
from datetime import datetime
from django.conf import settings
from .models import Video

from celery import shared_task

# Configure logging
logger = logging.getLogger(__name__)

# @shared_task(bind=True, max_retries=3, default_retry_delay=60)
@shared_task(bind=True)
def upload_video_to_s3(self, video_id):
    video = Video.objects.get(id=video_id)
    s3 = boto3.client('s3')

    try:
        # Extract title and trainer name
        title = video.title.strip()
        parts = title.split()
        trainer_name = parts[-1]

        # Create a unique folder using UUID
        unique_folder_name = str(uuid.uuid4())
        unique_folder_path = os.path.join(settings.MEDIA_ROOT, unique_folder_name)

        # Create nested folder structure inside the unique folder
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        local_folder_path = os.path.join(unique_folder_path, trainer_name, f"{current_datetime}_{title}")
        os.makedirs(local_folder_path, exist_ok=True)

        # Move video file to the nested local folder
        video_file_name = os.path.basename(video.video.name)
        video_file_path = os.path.join(local_folder_path, video_file_name)
        shutil.move(video.video.path, video_file_path)

        # Define the output directory for the script
        script_output_dir = os.path.join(local_folder_path, 'output')
        os.makedirs(script_output_dir, exist_ok=True)

        # Run the shell script to process the video
        script_path = os.path.join(settings.BASE_DIR, 'uploader', 'conversion_script.sh')  # Update with the correct path to the script

        subprocess.run([script_path, video_file_path, script_output_dir], check=True)

        # Construct the S3 folder path
        s3_folder_path = f"{trainer_name}/{current_datetime}_{title}/output/"

        # Upload processed files to S3
        for root, _, files in os.walk(script_output_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                s3_file_key = os.path.relpath(local_file_path, script_output_dir)
                s3.upload_file(local_file_path, settings.AWS_STORAGE_BUCKET_NAME, s3_folder_path + s3_file_key)

        # Update upload status
        video.upload_status = 'uploaded'

        # Delete the unique folder and its contents after successful upload
        logger.info(f"Deleting unique folder: {unique_folder_path}")
        # shutil.rmtree(unique_folder_path)
        logger.info(f"Unique folder {unique_folder_path} deleted successfully")

    except subprocess.CalledProcessError as e:
        # Handle errors
        logger.error(f"Error occurred during video processing: {e}")
        video.upload_status = 'failed'
        self.retry(exc=e)  # Retry the task

    except Exception as e:
        # Handle other errors
        logger.error(f"Error occurred: {e}")
        video.upload_status = 'failed'
        self.retry(exc=e)  # Retry the task

    finally:
        # Save the changes to the video object
        video.save()
