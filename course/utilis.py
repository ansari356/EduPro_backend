import random
import string
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from decouple import config
from rest_framework import serializers
import logging

def genrate_coupon_code(length=10):
    characters = string.ascii_uppercase + string.digits 
    coupon_code = ''.join(random.choice(characters) for _ in range(length))
    return coupon_code


def genrate_otp(video_id):
    """
    Generates an OTP for VdoCipher video playback.
    """
    api_secret_key = config('SECRET_KEY_VED')
    url = f"https://dev.vdocipher.com/api/videos/{video_id}/otp"
    headers = {
        'Authorization': f"Apisecret {api_secret_key}",
        'Content-Type': "application/json",
        'Accept': "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('otp'), data.get('playbackInfo')
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to generate OTP for video_id {video_id}: {e}")
        return None, None
    
    



logger = logging.getLogger(__name__)

def get_vdocipher_video_details(video_id):
    """
    Fetches video details from VdoCipher, including status and duration.
    """
    api_secret_key = config('SECRET_KEY_VED')
    url = f"https://dev.vdocipher.com/api/videos/{video_id}"
    headers = {
        'Authorization': f"Apisecret {api_secret_key}",
        'Accept': "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get video details from VdoCipher for video_id {video_id}: {e}")
        return None

def get_vdocipher_upload_credentials(title):
    """
    Requests upload credentials from VdoCipher.
    """
    api_secret_key = config('SECRET_KEY_VED')
    url = "https://dev.vdocipher.com/api/videos"
    headers = {
        'Authorization': f"Apisecret {api_secret_key}"
    }
    querystring = {"title": title}
    
    try:
        response = requests.put(url, headers=headers, params=querystring)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"VdoCipher API request failed: {e}")
        raise serializers.ValidationError(f'VdoCipher API request failed: {e}')

    return response.json()



def delete_vdocipher_video(video_id):
    """
    Deletes a video from VdoCipher.
    """
    api_secret_key = config('SECRET_KEY_VED')
    url = "https://dev.vdocipher.com/api/videos"
    headers = {
        'Authorization': f"Apisecret {api_secret_key}"
    }
    querystring = {"videos": video_id}

    try:
        response = requests.delete(url, headers=headers, params=querystring)
        response.raise_for_status()
        logger.info(f"Successfully initiated deletion for video_id {video_id} from VdoCipher.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to delete video from VdoCipher for video_id {video_id}: {e}")
        return None


def create_lesson_progress_for_access(student, course=None, module=None):
    from .models import StudentLessonProgress, Lesson

    lessons_qs = Lesson.objects.none()

    if course:
        lessons_qs = Lesson.objects.filter(module__course=course)
    
    elif module:
        lessons_qs = Lesson.objects.filter(module=module)

    if lessons_qs.exists():
        StudentLessonProgress.objects.bulk_create(
            [StudentLessonProgress(student=student, lesson=lesson) for lesson in lessons_qs],
            ignore_conflicts=True
        )
