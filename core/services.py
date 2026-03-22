import requests
import logging
from django.conf import settings

# Standard logger for tracking API failures
logger = logging.getLogger(__name__)

class RailService:
    """
    Service layer to handle communication between the RailGuard Web App 
    and the external Email Verification API via AWS API Gateway.
    """

    @staticmethod
    def get_verification_status(email):
        """
        Calls the Identity Server to check if a passenger is already verified.
        Uses the x-api-key for authentication.
        """
        url = getattr(settings, 'AWS_STATUS_URL', None)
        api_key = getattr(settings, 'AWS_API_KEY', None)
        
        if not url or not api_key:
            return {"is_verified": False, "error": "API Configuration missing"}
            
        # These headers are required by your AWS API Gateway configuration
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        try:
            # UPDATED: Added headers=headers to the requests.get call
            response = requests.get(
                url, 
                params={"email": email}, 
                headers=headers, 
                timeout=5
            )
            response.raise_for_status() 
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Identity Server Connection Error: {e}")
            return {"is_verified": False, "error": "Identity Server unreachable"}

    @staticmethod
    def validate_and_send(email):
        """
        Triggers the full validation suite on the remote Email Verification API.
        Uses the x-api-key for authentication.
        """
        url = getattr(settings, 'AWS_VERIFY_URL', None)
        api_key = getattr(settings, 'AWS_API_KEY', None)
        
        if not url or not api_key:
            return {"status": "fail", "message": "API Configuration missing"}
            
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        try:
            # UPDATED: Added headers=headers to the requests.post call
            response = requests.post(
                url, 
                json={"email": email}, 
                headers=headers, 
                timeout=10
            )
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