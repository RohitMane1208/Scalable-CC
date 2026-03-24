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
        Uses the x-api-key for authentication via AWS API Gateway.
        """
        url = getattr(settings, 'AWS_STATUS_URL', None)
        api_key = getattr(settings, 'AWS_API_KEY', None)
        
        if not url or not api_key:
            return {"is_verified": False, "error": "API Configuration missing"}
            
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        try:
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
        Uses the x-api-key for authentication via AWS API Gateway.
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
    def trigger_emergency(city="Dublin"):
        """
        Fetches geographic data for essential emergency services 
        (Hospitals, Police, Fire, and Pharmacies) using a city name.
        """
        url = getattr(settings, 'EMERGENCY_SERVICE_URL', None)
        
        if not url:
            logger.error("Emergency Service URL configuration missing.")
            return []

        params = {"city": city}

        try:
            # Direct GET request to the public emergency API
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Returns a list of emergency facilities
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Emergency API Connection Error: {e}")
            return []

    @staticmethod
    def get_emergency_by_coords(lat, lon):
        """
        Alternative method to fetch emergency services using exact coordinates.
        """
        url = getattr(settings, 'EMERGENCY_SERVICE_URL', None)
        if not url: return []

        params = {"lat": lat, "lon": lon}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Emergency API Coord Search Error: {e}")
            return []