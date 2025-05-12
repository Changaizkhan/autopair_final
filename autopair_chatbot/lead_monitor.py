# File: autopair_chatbot/lead_monitor.py
import time
import threading
import requests
from autopair_chatbot.config import logger
from autopair_chatbot.hubspot import fetch_lead_details
from autopair_chatbot.utils import now_in_toronto
from autopair_chatbot.hubspot import update_lead_in_hubspot

most_recent_lead_id = None
most_recent_lead_time = None
processing_locks = {}


def start_lead_monitor():
    lead_monitor_thread = threading.Thread(target=lead_monitor_loop, daemon=True)
    lead_monitor_thread.start()
    logger.info("Lead monitoring thread started")


def lead_monitor_loop():
    global most_recent_lead_id, most_recent_lead_time
    initial_leads = fetch_latest_leads()
    if initial_leads:
        most_recent_lead = initial_leads[0]
        most_recent_lead_id = most_recent_lead.get("id")
        props = most_recent_lead.get("properties", {})
        most_recent_lead_time = props.get("createdate")
        logger.info(f"Lead monitor initialized. Most recent lead: {most_recent_lead_id}")

    while True:
        try:
            time.sleep(60)
            logger.info("Checking for new leads...")
            latest_leads = fetch_latest_leads()
            new_leads = identify_new_leads(latest_leads)
            for lead in reversed(new_leads):
                lead_id = lead.get("id")
                logger.info(f"Processing new lead from polling: {lead_id}")
                threading.Thread(target=process_new_lead, args=(lead_id,)).start()
        except Exception as e:
            logger.error(f"Error in lead monitor: {e}")


def fetch_latest_leads():
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    from autopair_chatbot.config import HUBSPOT_API_KEY
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "filterGroups": [{
            "filters": [{"propertyName": "lifecyclestage", "operator": "EQ", "value": "lead"}]
        }],
        "sorts": [{"propertyName": "createdate", "direction": "DESCENDING"}],
        "properties": [
            "firstname", "lastname", "email", "phone", "createdate",
            "vehicle_make", "vehicle_model", "vehicle_year", "vehicle_mileage",
            "autopair_processed", "hs_object_id"
        ],
        "limit": 10
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        return []


def identify_new_leads(leads):
    global most_recent_lead_id, most_recent_lead_time
    if not leads:
        return []

    new_leads = []
    for lead in leads:
        lead_id = lead.get("id")
        props = lead.get("properties", {})
        lead_time = props.get("createdate")

        if most_recent_lead_time and lead_time <= most_recent_lead_time:
            continue
        if props.get("autopair_processed") == "true":
            continue

        required_fields = ['phone', 'vehicle_year', 'vehicle_mileage']
        missing = [f for f in required_fields if not props.get(f)]
        if missing:
            logger.info(f"Lead {lead_id} missing required fields: {missing}")
            continue

        new_leads.append(lead)

    if new_leads:
        most_recent_lead_id = new_leads[0].get("id")
        most_recent_lead_time = new_leads[0].get("properties", {}).get("createdate")

    return new_leads


def process_new_lead(lead_id):
    from autopair_chatbot.hubspot import fetch_lead_details
    from autopair_chatbot.sms_handlers import handle_question_submission, handle_schedule_submission
    from autopair_chatbot.utils import qualify_plans, send_qualification_sms

    global processing_locks

    if lead_id in processing_locks:
        logger.info(f"Lead {lead_id} already processing")
        return

    processing_locks[lead_id] = True

    try:
        logger.info(f"Processing lead {lead_id}")
        lead = fetch_lead_details(lead_id)
        if not lead:
            logger.error(f"No data for lead {lead_id}")
            return

        props = lead.get("properties", {})
        if props.get("autopair_processed") == "true":
            logger.info(f"Lead {lead_id} already processed")
            return

        required = ['phone', 'vehicle_year', 'vehicle_mileage']
        if any(field not in props for field in required):
            logger.error(f"Lead {lead_id} missing required fields")
            return

        qualification = qualify_plans(props['vehicle_year'], props['vehicle_mileage'])
        update_data = {
            "properties": {
                "autopair_qualified": str(qualification["qualified"]).lower(),
                "autopair_qualified_plans": ", ".join([p["name"] for p in qualification.get("plans", [])])
            }
        }

        if send_qualification_sms(lead, qualification):
            update_data["properties"].update({
                "autopair_processed": "true",
                "autopair_last_processed": int(now_in_toronto().timestamp() * 1000)
            })

        update_lead_in_hubspot(lead_id, update_data)

    except Exception as e:
        logger.error(f"Error processing lead {lead_id}: {e}")
    finally:
        processing_locks.pop(lead_id, None)
