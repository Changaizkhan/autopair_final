# File: autopair_chatbot/hubspot.py
from flask import request, jsonify
import time
import json
import re
import requests
from autopair_chatbot.config import HUBSPOT_API_KEY, logger


def fetch_lead_details(lead_id, max_retries=3):
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{lead_id}"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        "properties": ",".join([
            "firstname", "lastname", "phone", "email",
            "vehicle_make", "vehicle_model", "vehicle_year", "vehicle_mileage",
            "autopair_processed", "autopair_status", "autopair_qualified_plans",
            "hs_object_id"
        ])
    }
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"HubSpot fetch attempt {attempt} failed: {e}")
            time.sleep(2)
    return None


def update_lead_in_hubspot(lead_id, update_data, max_retries=3):
    logger.info(f"🔄 Updating HubSpot (lead_id: {lead_id}):\n{json.dumps(update_data, indent=2)}")
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{lead_id}"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.patch(url, headers=headers, json=update_data)
            response.raise_for_status()
            logger.info(f"✅ HubSpot update successful for lead {lead_id}")
            return True
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            message = http_err.response.text
            if status_code == 404:
                logger.warning(f"⚠️ Lead {lead_id} not found (404). Skipping update.")
                return False
            elif status_code == 429:
                logger.warning(f"🔁 Rate limited (429). Retrying after 2s... [Attempt {attempt}]")
                time.sleep(2)
            elif status_code in [502, 503, 504]:
                logger.warning(f"🔁 Temporary HubSpot error ({status_code}). Retrying... [Attempt {attempt}]")
                time.sleep(2)
            else:
                logger.error(f"❌ HubSpot update failed (Status: {status_code}): {message}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection error updating HubSpot: {e}")
            time.sleep(1)
    logger.error(f"❌ All attempts to update HubSpot (lead_id: {lead_id}) failed.")
    return False


def find_lead_by_phone(phone):
    phone_clean = re.sub(r'\D', '', phone)
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    search_patterns = [phone]
    if phone.startswith("+"):
        search_patterns.append(phone[1:])
    if phone.startswith("+1") and len(phone) == 12:
        search_patterns.append(phone[2:])

    for pattern in search_patterns:
        data = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "phone",
                    "operator": "CONTAINS_TOKEN",
                    "value": pattern
                }]
            }],
            "properties": [
                "firstname", "lastname", "phone", "email",
                "vehicle_make", "vehicle_model", "vehicle_year", "vehicle_mileage",
                "autopair_processed", "autopair_status", "autopair_qualified_plans",
                "hs_object_id"
            ],
            "limit": 1
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            results = response.json().get("results", [])
            if results:
                return results[0]
        except requests.exceptions.RequestException as e:
            logger.error(f"HubSpot search failed: {e}")
    return None


def hubspot_webhook():
    data = request.json
    logger.info(f"📥 Received HubSpot webhook: {data}")
    return jsonify({"status": "received"}), 200
