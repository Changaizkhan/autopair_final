# main.py
import os
from dotenv import load_dotenv
from flask import Flask
import logging
from autopair_chatbot import call_handlers, sms_handlers, hubspot, lead_monitor

load_dotenv()
app = Flask(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Register routes using decorators
@app.route("/call-handler/<lead_id>", methods=["POST"])
def call_handler_route(lead_id):
    return call_handlers.call_handler(lead_id)

@app.route("/ivr-handler/<lead_id>", methods=["POST"])
def ivr_handler_route(lead_id):
    return call_handlers.ivr_handler(lead_id)

@app.route("/sms-webhook", methods=["POST"])
def sms_webhook_route():
    return sms_handlers.sms_webhook()

@app.route("/hubspot-webhook", methods=["POST"])
def hubspot_webhook_route():
    return hubspot.hubspot_webhook()

# Add this route for Twilio direct voice webhook
@app.route("/voice-inbound", methods=["POST"])
def voice_inbound_handler():
    from twilio.twiml.voice_response import VoiceResponse
    response = VoiceResponse()
    response.say("Welcome to Auto Pair Warranty. Please wait while we connect you.")
    response.dial("+12185683118", record="record-from-answer")
    return str(response), 200, {'Content-Type': 'text/xml'}

if __name__ == "__main__":
    lead_monitor.start_lead_monitor()
    app.run(host="0.0.0.0", port=5000)
