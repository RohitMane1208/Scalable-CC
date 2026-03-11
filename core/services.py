import requests
from django.conf import settings

class RailService:
    # Your API Endpoints
    AWS_VERIFY_URL = "http://email-verifier-env.eba-mdagwhcq.us-east-1.elasticbeanstalk.com/api/email/"
    AWS_STATUS_URL = "http://email-verifier-env.eba-mdagwhcq.us-east-1.elasticbeanstalk.com/api/status/"

    @staticmethod
    def get_verification_status(email):
        """
        Calls your API to check if identity is already confirmed.
        """
        try:
            response = requests.get(RailService.AWS_STATUS_URL, params={"email": email}, timeout=5)
            return response.json() # Returns {'is_verified': True/False, 'metrics': {...}}
        except Exception:
            return {"is_verified": False, "error": "Identity Server unreachable"}

    @staticmethod
    def validate_and_send(email):
        """
        Triggers the FULL suite from your utils.py:
        - Syntax check
        - MX Record check
        - Disposable check
        - Role-based check
        - Domain suggestion
        - CloudMail sending
        """
        try:
            # We send the email to your API; the API runs all utils.py logic
            response = requests.post(RailService.AWS_VERIFY_URL, json={"email": email}, timeout=10)
            return response.json()
        except Exception:
            return {"status": "fail", "message": "Connection to Verification API failed."}

    @staticmethod
    def trigger_emergency(train_id, carriage, category):
        # Placeholder for the Emergency Dispatch API
        return True