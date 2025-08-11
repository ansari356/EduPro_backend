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

def upload_to_vdocipher(video_path, video_name, title):
    """
    Initiates the upload process with VdoCipher and uploads the video file.
    Returns the video_id.
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

    upload_info = response.json()
    client_payload = upload_info.get('clientPayload')
    upload_link = client_payload.get('uploadLink')
    video_id = upload_info.get('videoId')

    if not all([client_payload, upload_link, video_id]):
        logger.error("Invalid response from VdoCipher API during upload initiation.")
        raise serializers.ValidationError('Invalid response from VdoCipher API')

    with open(video_path, 'rb') as video_file:
        m = MultipartEncoder(fields=[
            ('x-amz-credential', client_payload['x-amz-credential']),
            ('x-amz-algorithm', client_payload['x-amz-algorithm']),
            ('x-amz-date', client_payload['x-amz-date']),
            ('x-amz-signature', client_payload['x-amz-signature']),
            ('key', client_payload['key']),
            ('policy', client_payload['policy']),
            ('success_action_status', '201'),
            ('success_action_redirect', ''),
            ('file', (video_name, video_file, 'video/mp4'))
        ])

        try:
            response = requests.post(upload_link, data=m, headers={'Content-Type': m.content_type})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload video to VdoCipher: {e}")
            raise serializers.ValidationError(f'Failed to upload video to VdoCipher: {e}')

    return video_id

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
