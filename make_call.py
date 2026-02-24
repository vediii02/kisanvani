import os
from twilio.rest import Client

print("Initiating test call using Twilio API...")

# # Read credentials from environment variables

account_sid=os.getenv("TWILIO_ACCOUNT_SID")
auth_token=os.getenv("TWILIO_AUTH_TOKEN")


if not account_sid or not auth_token:
    raise EnvironmentError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment variables.")

client = Client(account_sid, auth_token)
# # Replace these placeholders with your actual numbers when running
from_number = "+18304940402"
to_number = "+917354126946"


# Your public webhook URL (update if your ngrok URL changes)
webhook_url = "https://conjugative-tandra-amitotically.ngrok-free.dev/api/twilio/incoming-call"
try:
    call = client.calls.create( 
        to=to_number,
        from_=from_number,
        url=webhook_url
    )
    print(f"Call initiated. Call SID: {call.sid}")
except Exception as e:
    print(f"Failed to initiate call: {e}")
    
