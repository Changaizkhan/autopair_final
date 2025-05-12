# File: autopair_chatbot/sms_handlers.py
from flask import request, jsonify
from autopair_chatbot.utils import format_phone_number, is_schedule_text, get_ai_response, now_in_toronto, get_vehicle_info, send_sms
from autopair_chatbot.hubspot import find_lead_by_phone, update_lead_in_hubspot


def sms_webhook():
    from_number = request.form.get("From")
    body = request.form.get("Body", "").strip().lower()

    if not from_number:
        return jsonify({"status": "error", "message": "Missing phone"}), 400

    lead = find_lead_by_phone(from_number)
    if not lead:
        return jsonify({"status": "error", "message": "Lead not found"}), 404

    props = lead.get("properties", {})
    current_status = props.get("autopair_status", "")

    if body in ["1", "call now"]:
        return handle_call_request(lead)
    elif body in ["2", "schedule call"]:
        return handle_schedule_request(lead)
    elif body in ["3", "questions"]:
        return handle_question_request(lead)
    elif current_status == "Awaiting Schedule":
        if is_schedule_text(body):
            return handle_schedule_submission(lead, body)
        else:
            return handle_question_submission(lead, body)
    elif current_status == "Awaiting Question":
        return handle_question_submission(lead, body)
    else:
        return handle_question_submission(lead, body)


def handle_call_request(lead):
    from autopair_chatbot.config import TWILIO_PHONE_NUMBER, NGROK_URL, twilio_client, logger

    props = lead.get("properties", {})
    phone = format_phone_number(props.get("phone", ""))
    if not phone:
        return jsonify({"status": "error", "message": "Invalid phone number"}), 400

    update_lead_in_hubspot(lead["id"], {
        "properties": {
            "autopair_status": "Call Requested",
            "autopair_last_response": now_in_toronto().isoformat()
        }
    })

    try:
        twilio_client.calls.create(
            url=f"{NGROK_URL}/call-handler/{lead['id']}",
            to=phone,
            from_=TWILIO_PHONE_NUMBER
        )
        send_sms(phone, "We're calling you now! Please pick up.")
        return jsonify({"status": "success", "action": "Call initiated"})
    except Exception as e:
        logger.error(f"Call failed: {e}")
        send_sms(phone, "We're having trouble calling. Please try again later.")
        return jsonify({"status": "error", "message": "Call failed"}), 500


def handle_schedule_request(lead):
    phone = format_phone_number(lead.get("properties", {}).get("phone"))
    send_sms(phone, "We're available Mon–Fri, 9am–6pm Eastern Time. When should we call you? (e.g. 'Tomorrow 10am' or 'Friday afternoon')")

    update_lead_in_hubspot(lead["id"], {
        "properties": {
            "autopair_status": "Awaiting Schedule",
            "autopair_last_response": now_in_toronto().isoformat()
        }
    })
    return jsonify({"status": "success", "action": "Schedule requested"})


def handle_question_request(lead):
    phone = format_phone_number(lead.get("properties", {}).get("phone"))
    send_sms(phone, "What would you like to know about your warranty options?")

    update_lead_in_hubspot(lead["id"], {
        "properties": {
            "autopair_status": "Awaiting Question",
            "autopair_last_response": now_in_toronto().isoformat()
        }
    })
    return jsonify({"status": "success", "action": "Question requested"})


def handle_schedule_submission(lead, schedule_text):
    from autopair_chatbot.utils import parse_schedule_text

    phone = format_phone_number(lead.get("properties", {}).get("phone"))
    scheduled_time = parse_schedule_text(schedule_text)

    if scheduled_time:
        formatted_time = scheduled_time.strftime("%A, %B %d at %I:%M %p")
        send_sms(phone, f"Thank you! We've scheduled your callback for {formatted_time} (Eastern Time).")
        update_data = {
            "properties": {
                "autopair_status": "Call Scheduled",
                "autopair_scheduled_time": int(scheduled_time.timestamp() * 1000),
                "autopair_last_response": now_in_toronto().isoformat()
            }
        }
    else:
        send_sms(phone, "I didn't understand that time. Please try again (e.g. 'Friday 2pm').")
        update_data = {
            "properties": {
                "autopair_last_response": now_in_toronto().isoformat()
            }
        }

    update_lead_in_hubspot(lead["id"], update_data)
    return jsonify({"status": "success"})


def handle_question_submission(lead, question):
    props = lead.get("properties", {})
    phone = format_phone_number(props.get("phone", ""))

    if not phone:
        return jsonify({"status": "error", "message": "Invalid phone number"}), 400

    context = f"Customer: {props.get('firstname', '')}, Vehicle: {props.get('vehicle_year', '')} {props.get('vehicle_make', '')} {props.get('vehicle_model', '')}, Qualified plans: {props.get('autopair_qualified_plans', 'Unknown')}"
    ai_response = get_ai_response(question, context)
    if not ai_response or "trouble" in ai_response:
        ai_response = "A specialist will contact you shortly to assist further."

    send_sms(phone, ai_response)

    update_lead_in_hubspot(lead["id"], {
        "properties": {
            "autopair_status": "Question Answered",
            "autopair_last_question": question,
            "autopair_last_response": int(now_in_toronto().timestamp() * 1000)
        }
    })
    return jsonify({"status": "success", "response": ai_response})
