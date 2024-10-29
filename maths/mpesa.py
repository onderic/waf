import os
import time
import math
import base64
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from maths.models import Subscription
from maths.models import Mpesa


class LipaNaMpesa:
    def __init__(self) -> None:
        self.now = datetime.now()
        self.shortcode = "174379"
        self.consumer_key = "stRGGFdT68FKEW0lH9wxXte2cQmLVoFS8sVHDCE2mtkYxVei"
        self.consumer_secret = "6bfXFtk67G4w6XWzlrZo89WF4mzihq4nK09MWQWGqzSaFGMGdwh5wDHGpEikuGlO"
        self.passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        self.access_token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        self.stk_push_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        self.access_token = None
        self.call_back = "https://62d5-41-89-162-2.ngrok-free.app"
        self.access_token_expiration = 0
        self.headers = None  

        try:
            self.access_token = self.get_mpesa_access_token()
            if self.access_token is None:
                raise Exception("Request for access token failed")
            else:
                self.access_token_expiration = time.time()
        except Exception as e:
            subscription_message = "Something went wrong. Please try again later."
            print(str(e))
    
    def get_mpesa_access_token(self):
        try:
            res = requests.get(
                self.access_token_url,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret)
            )
            res.raise_for_status()
            token = res.json()['access_token']
            self.headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        except Exception as e:
            print(str(e), "error getting access token")
            raise e
        return token

    
    def generate_password(self):
        timestamp = self.now.strftime("%Y%m%d%H%M%S")
        password_str = self.shortcode + self.passkey + timestamp
        password_bytes = password_str.encode()
        return base64.b64encode(password_bytes).decode("utf-8")
    
    def stk_push(self, payload):
        amount = payload['amount']
        subscription_id = payload['subscription'] 
        phone_number = payload['phone_number']
        password = self.generate_password()
        timestamp = self.now.strftime("%Y%m%d%H%M%S")
        callback_url = self.call_back

        data = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": math.ceil(float(amount)),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": f"subscription {subscription_id}", 
            "TransactionDesc": "Payment for subscription", 
        }

        try:
            response = requests.post(
                self.stk_push_url,
                json=data,
                headers=self.headers
            )
            response.raise_for_status()

            merchant_request_id = response.json().get('MerchantRequestID')
            checkout_request_id = response.json().get('CheckoutRequestID')

            # Retrieve the subscription
            subscription = Subscription.objects.get(id=subscription_id)
            
            Mpesa.objects.create(
                subscription=subscription,
                checkout_request_id=checkout_request_id,
                merchant_request_id=merchant_request_id,
                is_processed=False 
            )
            
            return response.json()

        except requests.exceptions.RequestException as e:
            print("Error during STK push request:", str(e))
            raise e