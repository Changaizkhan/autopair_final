# Autopair Warranty Chatbot

This is a production-ready Flask-based chatbot system for Autopair's warranty sales. It handles:
- AI-powered SMS interactions
- Twilio IVR-based call handling
- HubSpot lead processing and qualification
- Scheduled callback and customer queries

---

## 📁 Project Structure

autopair_chatbot_project_complete/
├── autopair_chatbot/
│ ├── init.py
│ ├── config.py # Environment + API clients
│ ├── hubspot.py # HubSpot API fetch/update logic
│ ├── sms_handlers.py # SMS routing, AI responses
│ ├── call_handlers.py # IVR and call flow (Twilio)
│ ├── lead_monitor.py # Lead polling from HubSpot
│ └── utils.py # Helpers: phone, AI, parsing, etc.
├── main.py # Flask app entrypoint
├── requirements.txt # Python dependencies
└── README.md # Project setup and usage


---

## 🚀 How to Run

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt

## Set your environment variables in a .env file:
HUBSPOT_API_KEY=your_hubspot_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+11234567890
OPENAI_API_KEY=your_openai_key
HUBSPOT_WEBHOOK_SECRET=optional
NGROK_URL=http://your-ngrok-url.ngrok.io

## Start the Flask server
python main.py


## API Endpoints
# Endpoint	        Method	Description
/sms-webhook	    POST	Handle incoming SMS from Twilio
/call-handler/<id>	POST	Twilio IVR Call entry
/ivr-handler/<id>	POST	Handle IVR keypress logic
/hubspot-webhook	POST	HubSpot contact creation handler



<!-- source venv/bin/activate -->




git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/Changaizkhan/autopair_final.git
git push -u origin main