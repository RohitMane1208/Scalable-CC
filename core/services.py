import requests
import logging
from django.conf import settings

# Standard logger for tracking API failures
logger = logging.getLogger(__name__)

class RailService:
    """
    Service layer to handle communication between the RailGuard Web App 
    and the external Email Verification API.
    """

    @staticmethod
    def get_verification_status(email):
        """
        Calls the Identity Server to check if a passenger is already verified.
        """
        # SECURITY: URL is fetched from settings.py to avoid hardcoding
        url = getattr(settings, 'AWS_STATUS_URL', None)
        if not url:
            return {"is_verified": False, "error": "API Configuration missing"}

        try:
            response = requests.get(url, params={"email": email}, timeout=5)
            response.raise_for_status() # Check for 4xx or 5xx errors
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Identity Server Connection Error: {e}")
            return {"is_verified": False, "error": "Identity Server unreachable"}

    @staticmethod
    def validate_and_send(email):
        """
        Triggers the full validation suite (Syntax, MX, Disposable, etc.) 
        on the remote Email Verification API.
        """
        url = getattr(settings, 'AWS_VERIFY_URL', None)
        if not url:
            return {"status": "fail", "message": "API Configuration missing"}

        try:
            # Note: We use json= here to ensure content-type is application/json
            response = requests.post(url, json={"email": email}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Verification API Connection Error: {e}")
            return {
                "status": "fail", 
                "message": "Connection to Verification API failed. Please try again."
            }

    @staticmethod
    def trigger_emergency(train_id, carriage, category):
        """
        Placeholder for the Emergency Dispatch API.
        """
        # Logic for logging or dispatching alerts to Irish Rail Control
        return True