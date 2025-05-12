# File: autopair_chatbot/utils.py
import re
import time
import pytz
import phonenumbers
from datetime import datetime, timedelta
from autopair_chatbot.config import logger, client
from autopair_chatbot.config import twilio_client, TWILIO_PHONE_NUMBER



# === Modular Warranty Knowledge ===
KNOWLEDGE_OVERVIEW = """
🏆 Welcome to Autopair Warranty — Canada's Most Trusted Direct-to-Consumer Auto Warranty.

We are transforming how Canadians protect their vehicles by:
- Offering **coverage for all makes and models**
- Providing access to **ANY licensed repair facility** in Canada or the US
- Saving you up to **250% vs dealership markups**
- Including **$0 deductible** in every plan — no extra cost for repairs
- Eliminating dealership upsells, quotes, inspections, or hidden fees

Trusted, insured, and backed by industry professionals:
- 30+ years combined experience in automotive sales
- Highly rated on Google and BBB
- Thousands of satisfied customers across North America

Compare us with others:
- 💡 No quotes required, instant pricing
- 🛠️ No forced repair centers — choose any licensed shop
- 💳 Flexible payment options (bi-weekly or monthly), interest-FREE on approved credit
"""

PLAN_DETAILS = """
🚘 Autopair Warranty Plans

1. 🔹 STANDARD PLAN
   - Duration: 24 months / Unlimited KM
   - Price: $1299 or 6 bi-weekly payments of $217
   - Repair Limit: $3,000 per claim
   - Includes: Powertrain, electrical, brakes, A/C, transmission
   - Excludes: Suspension, high-tech, sensors, hybrid
   - Surcharge: $0 (premium), $499 (exotic)

2. 🔹 THE WORKS PLAN
   - Duration: 24 months / 50,000 KM
   - Price: $1799 or 18 monthly payments of $100
   - Repair Limit: $6,000 per claim
   - Includes: All items in Standard + suspension, sensors, hybrid, electronics
   - Surcharge: $299 (premium), $499 (exotic)

3. 🔹 THE WORKS PLUS PLAN
   - Duration: 48 months / 100,000 KM
   - Price: $2599 or 18 monthly payments of $145
   - Same coverage as THE WORKS, with double the term + km
   - Surcharge: Same as WORKS

🟩 Plan Eligibility:
- STANDARD: Vehicle must be ≤10 years & <200,000 KM
- WORKS / PLUS: Vehicle must be ≤6 years & <120,000 KM
"""

COVERAGE_COMPARISON = """
📊 Coverage Comparison by Plan

| Component                        | STANDARD | WORKS | WORKS PLUS |
|----------------------------------|----------|--------|-------------|
| Engine (gas/diesel)             | ✅       | ✅     | ✅          |
| Transmission (auto/manual)      | ✅       | ✅     | ✅          |
| Differentials (front/rear)      | ✅       | ✅     | ✅          |
| Transfer Case (4x4)             | ✅       | ✅     | ✅          |
| Turbo / Supercharger            | ✅       | ✅     | ✅          |
| Seals & Gaskets (major)         | ✅       | ✅     | ✅          |
| Front Suspension                | ❌       | ✅     | ✅          |
| Rear Suspension                 | ❌       | ✅     | ✅          |
| Steering System                 | ✅       | ✅     | ✅          |
| Cooling System                  | ✅       | ✅     | ✅          |
| Brakes                          | ✅       | ✅     | ✅          |
| Electrical System               | ✅       | ✅     | ✅          |
| Air Conditioning                | ✅       | ✅     | ✅          |
| High-Tech & Electronics         | ❌       | ✅     | ✅          |
| Sensors (ABS, O2, etc.)         | ❌       | ✅     | ✅          |
| Hybrid Vehicle Components       | ❌       | ✅     | ✅          |
| Courtesy Rental ($350 max)      | ✅       | ✅     | ✅          |
| Towing ($100 max)               | ✅       | ✅     | ✅          |
| Trip Interruption ($750 max)    | ✅       | ✅     | ✅          |
| $0 Deductible                   | ✅       | ✅     | ✅          |
"""

CLAIMS_INFO = """
🛠️ Autopair Warranty — Claims Process (Simple 4-Step Guide)

1. 🏁 Choose Your Repair Shop  
   - Take your vehicle to ANY licensed repair facility across Canada or the USA.  
   - You’re not limited to dealers or pre-approved shops.

2. 🔍 Get a Diagnostic Report  
   - Ask the mechanic for a full diagnostic report.  
   - Submit the report through Autopair’s online claims portal.

3. ✅ Wait for Approval (12–24 hours)  
   - If the issue is covered in your plan, it’s approved.  
   - Wait for Autopair to confirm before approving any repairs.

4. 💰 Receive Payment  
   - Choose either:  
     1. Payment via your Autopair prepaid card  
     2. Direct Interac e-Transfer  
   - All payments are processed through email after approval.

⏳ Wait Period:  
- Coverage begins after 30 days + 1,500 km from warranty purchase date.  
- Claims cannot be made before this period is completed.

🛑 Reminders:  
- Do not authorize repairs until approval is received.  
- Coverage applies to **listed components only**.  
- **Inspection is not required at purchase**, but is required at time of claim.
- **Maintenance required**: oil + filter every 6 months or 12,000 km.
"""

FAQS = """
❓ Frequently Asked Questions (FAQs)

1. **What is a factory or manufacturer’s warranty?**  
Every new vehicle comes with a factory warranty that covers non-wear & tear parts. Once it expires, you’re on your own. Autopair fills that gap with extended coverage.

2. **Why not just get this from a dealer?**  
Dealers charge 2–3x more and force you to use specific repair centers. Autopair lets you choose your shop and buy directly — saving you thousands.

3. **I still have factory coverage. Why buy now?**  
You can defer Autopair coverage to begin right after your manufacturer warranty ends — up to 12 months in advance.

4. **My dealer gave me a 3-month warranty. What should I do?**  
You can still purchase Autopair and set it to start after the dealer plan ends.

5. **Can I transfer my plan if I sell the car?**  
Yes! Plans are fully transferable to the next owner. Just contact support.

6. **What happens during a breakdown?**  
Refer to the claims process: get a diagnosis, submit it, get approval, and choose your payment method (card or e-transfer).

7. **Are you better than other warranty companies?**  
Yes — we cut out middlemen, offer direct pricing, allow any licensed repair shop, and include $0 deductible on all plans.

8. **Can I cancel my plan?**  
Yes, within 10 days of purchase and no claims made. A $99 fee applies. After 10 days, plans are non-cancellable and non-refundable.

9. **Is there a limit to how many claims I can make?**  
No limit to the number of claims — but the max per claim is $3,000 (Standard) or $6,000 (Works), and total claim value cannot exceed the vehicle’s acquisition cost.

10. **Do I need to maintain the vehicle?**  
Yes. You must do oil + filter changes every 6 months or 12,000 km to keep coverage valid.

11. **Do I need an inspection to buy a plan?**  
No inspection is required to purchase. However, one is needed to process a claim.
"""
def send_qualification_sms(lead, qualification):
    """Send qualification SMS via Twilio"""
    from autopair_chatbot.config import twilio_client, TWILIO_PHONE_NUMBER
    props = lead.get("properties", {})
    
    phone = format_phone_number(props.get("phone", ""))
    if not phone:
        logger.error("Invalid phone number format")
        return False

    first_name = props.get("firstname", "there")
    vehicle = f"{props.get('vehicle_year')} {props.get('vehicle_make', '')} {props.get('vehicle_model', '')}".strip()

    try:
        if not qualification["qualified"]:
            message = f"Hi {first_name}, your vehicle doesn't qualify for our warranty plans."
        else:
            plans = "\n".join(f"○ {p['name']}: {p['duration']}" for p in qualification["plans"])
            message = (
                f"Hi {first_name}, your {vehicle} qualifies for:\n"
                f"{plans}\n\n"
                "Reply with:\n1⃣ Call now\n2⃣ Schedule call\n3⃣ Questions"
            )

        logger.info(f"📲 Sending SMS to {phone} with message: {message}")
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        return True
    except Exception as e:
        logger.error(f"SMS send failed: {e}")
        return False


def now_in_toronto():
    return datetime.now(pytz.timezone("America/Toronto"))


def qualify_plans(vehicle_year, mileage):
    try:
        current_year = now_in_toronto().year
        vehicle_age = current_year - int(vehicle_year)
        mileage = int(str(mileage).replace(",", "").strip())

        qualifies_standard = vehicle_age <= 10 and mileage < 200000
        qualifies_works = vehicle_age <= 6 and mileage < 120000

        if qualifies_works:
            return {
                "qualified": True,
                "plans": [
                    {"name": "Works Plan", "duration": "24 months / 50,000 km"},
                    {"name": "Works Plus Plan", "duration": "48 months / 100,000 km"}
                ]
            }
        elif qualifies_standard:
            return {
                "qualified": True,
                "plans": [{"name": "Standard Plan", "duration": "Basic coverage"}]
            }
        return {"qualified": False}
    except Exception as e:
        logger.error(f"Qualification error: {e}")
        return {"qualified": False, "error": "Invalid vehicle data"}


def get_ai_response(question, context=""):
    try:
        question_lower = question.lower()

        # Plan-specific response customization
        if any(word in question_lower for word in ["plan", "price", "cost", "monthly"]):
            if "Works Plus Plan" in context or "Works Plan" in context:
                # Extract only the WORKS plans from PLAN_DETAILS
                works_section_start = PLAN_DETAILS.find("2. 🔹 THE WORKS PLAN")
                section = PLAN_DETAILS[works_section_start:].strip()
            elif "Standard Plan" in context:
                # Extract only the STANDARD plan from PLAN_DETAILS
                works_section_start = PLAN_DETAILS.find("2. 🔹 THE WORKS PLAN")
                section = PLAN_DETAILS[:works_section_start].strip()
            else:
                section = PLAN_DETAILS

        elif any(word in question_lower for word in ["coverage", "included", "compare", "parts"]):
            section = COVERAGE_COMPARISON
        elif any(word in question_lower for word in ["claim", "repair", "shop", "approval", "mechanic"]):
            section = CLAIMS_INFO
        elif any(word in question_lower for word in ["how", "what if", "can i", "faq", "cancel"]):
            section = FAQS
        else:
            section = KNOWLEDGE_OVERVIEW

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You're a friendly warranty expert assistant. Use this knowledge:\n{section}\n\nCurrent context: {context}"
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"AI response error: {e}")
        return "I'm having trouble answering that. A specialist will contact you soon."


def send_sms(to_number, message, max_retries=3):
    from autopair_chatbot.config import twilio_client, TWILIO_PHONE_NUMBER
    try:
        to_number = format_phone_number(to_number)
        if not to_number:
            logger.error("Invalid phone number format")
            return False

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"📨 Sending SMS to {to_number} (Attempt {attempt})")
                twilio_client.messages.create(
                    body=message,
                    from_=TWILIO_PHONE_NUMBER,
                    to=to_number
                )
                logger.info(f"✅ SMS sent to {to_number}")
                return True
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    time.sleep(2)
                else:
                    logger.error(f"❌ Twilio error sending SMS to {to_number}: {e}")
                    return False
        logger.error(f"❌ Failed to send SMS after {max_retries} attempts")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected SMS error: {e}")
        return False


def format_phone_number(phone):
    try:
        phone = phone.strip()
        if phone.startswith("+"):
            parsed = phonenumbers.parse(phone, None)
        else:
            for region in ["US", "GB", "PK", "IN", "CA", "AU"]:
                try:
                    parsed = phonenumbers.parse(phone, region)
                    if phonenumbers.is_valid_number(parsed):
                        break
                except phonenumbers.NumberParseException:
                    continue
            else:
                raise ValueError("Could not parse number")

        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Phone number not valid")

        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception as e:
        logger.error(f"Phone format error: {e} | Raw: {phone}")
        return None


def is_schedule_text(text):
    text = text.lower().strip()
    if "tomorrow" in text or any(day in text for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
        return True
    if re.search(r'\d{1,2}(:\d{2})?\s*(am|pm|a\.m\.|p\.m\.)?', text):
        return True
    return False


def parse_schedule_text(text):
    text = text.lower().strip()
    now = now_in_toronto()
    try:
        if "tomorrow" in text:
            date = now.date() + timedelta(days=1)
            time_match = re.search(r'(\d+)(?::(\d+))?\s*(am|pm|a\.m\.|p\.m\.)?', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                am_pm = time_match.group(3)
                if am_pm and ('pm' in am_pm or 'p.m.' in am_pm) and hour < 12:
                    hour += 12
                return datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
            return datetime.combine(date, datetime.min.time().replace(hour=9))

        days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        for day_name, day_num in days.items():
            if day_name in text:
                date = next_weekday(day_num)
                hour = 9
                if "afternoon" in text:
                    hour = 14
                elif "evening" in text:
                    hour = 18
                else:
                    time_match = re.search(r'(\d+)(?::(\d+))?\s*(am|pm|a\.m\.|p\.m\.)?', text)
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2) or 0)
                        am_pm = time_match.group(3)
                        if am_pm and ('pm' in am_pm or 'p.m.' in am_pm) and hour < 12:
                            hour += 12
                return datetime.combine(date, datetime.min.time().replace(hour=hour))

        if now.hour < 16:
            return datetime.combine(now.date(), datetime.min.time().replace(hour=14))
        else:
            next_day = now.date() + timedelta(days=1)
            if next_day.weekday() >= 5:
                next_day = next_weekday(0)
            return datetime.combine(next_day, datetime.min.time().replace(hour=9))
    except Exception as e:
        logger.error(f"Error parsing schedule text '{text}': {e}")
        return None


def next_weekday(weekday):
    today = now_in_toronto().date()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def get_vehicle_info(lead):
    props = lead.get("properties", {})
    return {
        "vehicle": f"{props.get('vehicle_year', '')} {props.get('vehicle_make', '')} {props.get('vehicle_model', '')}".strip(),
        "plans": props.get("autopair_qualified_plans", "Unknown"),
        "customer": props.get("firstname", "Customer")
    }

