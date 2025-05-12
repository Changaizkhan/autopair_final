# File: autopair_chatbot/call_handlers.py
import os
from flask import request
from twilio.twiml.voice_response import VoiceResponse, Gather
from autopair_chatbot.config import logger
from autopair_chatbot.hubspot import update_lead_in_hubspot
from dotenv import load_dotenv
load_dotenv() 

# Load full ngrok URL from env
NGROK_URL = os.getenv("NGROK_URL")
logger.info(f"✅ Loaded NGROK_URL: {NGROK_URL}")


def call_handler(lead_id):
    logger.info(f"✅ Twilio reached /call-handler/{lead_id}")

    response = VoiceResponse()
    gather = Gather(
        num_digits=1,
        action=f"{NGROK_URL}/ivr-handler/{lead_id}",
        method="POST",
        timeout=10
    )
    gather.say("Hello! This is Auto Pair Warranty Services. Press 1 to talk to a specialist. Press 2 to hear about our warranty plans.")
    response.append(gather)
    response.say("We didn’t get your response. We'll call you back later.")

    return str(response), 200, {'Content-Type': 'text/xml'}

def ivr_handler(lead_id):
    digit = request.values.get('Digits')
    logger.info(f"IVR input received from lead {lead_id}: {digit}")

    update_lead_in_hubspot(lead_id, {
        "properties": {
            "autopair_last_digit_pressed": digit
        }
    })

    response = VoiceResponse()

    if digit == "1":
        response.say("Connecting you to a specialist, please hold.")

        # Dial with fallback option
        with response.dial(timeout=20, record="record-from-answer") as dial:
            dial.number("+18334268672")  # ✅ Primary: Canada toll-free
            dial.number("+12185683118")  # ✅ Fallback: US/Canada backup

        # If no one answers, fallback message
        response.say("We’re sorry. We could not connect you to a specialist right now.")
        response.hangup()

    elif digit == "2":
        response.say("Our warranty plans cover engine, transmission, and drivetrain components. They include roadside assistance and have a $100 deductible per visit. Coverage begins after a 30-day waiting period.")
    else:
        response.say("Invalid option. Please try again.")
        response.redirect(f"{NGROK_URL}/call-handler/{lead_id}")

    return str(response), 200, {'Content-Type': 'text/xml'}
