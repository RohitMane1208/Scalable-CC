import requests
import logging
from django.conf import settings

# Standard logger for tracking API failures
logger = logging.getLogger(__name__)

class RailService:
    """
    Service layer to handle communication between the RailGuard Web App 
    and external APIs (AWS Identity and Emergency Services).
    """

    @staticmethod
    def get_verification_status(email):
        """
        Calls the Identity Server to check if a passenger is already verified.
        """
        url = getattr(settings, 'AWS_STATUS_URL', None)
        if not url:
            return {"is_verified": False, "error": "API Configuration missing"}
            
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.get(url, params={"email": email}, headers=headers, timeout=5)
            response.raise_for_status() 
            return response.json()
        except Exception as e:
            logger.error(f"Identity Server Connection Error: {e}")
            return {"is_verified": False, "error": "Identity Server unreachable"}

    @staticmethod
    def validate_and_send(email):
        """
        Triggers the validation suite. Handles raw text responses
        to identify if a user is already verified.
        """
        url = getattr(settings, 'AWS_VERIFY_URL', None)
        if not url:
            return {"status": "fail", "message": "API Configuration missing"}
            
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json={"email": email}, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Get raw text to check for specific AWS responses
            res_text = response.text.lower()
            
            if "already verified" in res_text:
                return {"status": "already_verified"}
            elif "sent" in res_text:
                return {"status": "sent"}
            
            # Fallback to JSON if the API starts returning structured data
            try:
                return response.json()
            except ValueError:
                return {"status": "success", "message": response.text}

        except requests.RequestException as e:
            logger.error(f"Verification API Connection Error: {e}")
            return {"status": "fail", "message": "Connection failed."}

    @staticmethod
    def send_admin_alert(admin_email, user_email, service_details):
        """
        Sends an emergency trigger notification using the CloudMail API.
        Uses multipart/form-data as required by the verified PowerShell test.
        """
        url = "https://dfz5aavjml.execute-api.us-east-1.amazonaws.com/prod/api/send/"
        
        payload = {
            "to_email": admin_email,
            "subject": f"EMERGENCY ALERT: {service_details}",
            "message": f"User {user_email} has triggered an alert for: {service_details}.",
            "from_name": "RailGuard Admin System"
        }

        try:
            
            response = requests.post(url, data=payload, files={}, timeout=10)
            
            logger.info(f"Admin Alert Status: {response.status_code}")
            
            if response.status_code == 200:
                res_data = response.json()
                return res_data.get("status") == "success"
            return False
        except Exception as e:
            logger.error(f"Failed to connect to CloudMail API: {e}")
            return False

    @staticmethod
    def trigger_emergency(city="Dublin"):
        url = getattr(settings, 'EMERGENCY_SERVICE_URL', None)
        if not url: return []
        try:
            response = requests.get(url, params={"city": city}, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    @staticmethod
    def get_emergency_by_coords(lat, lon):
        url = getattr(settings, 'EMERGENCY_SERVICE_URL', None)
        if not url: return []
        try:
            response = requests.get(url, params={"lat": lat, "lon": lon}, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []