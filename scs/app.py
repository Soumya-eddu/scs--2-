import os
import random
import re
import sqlite3
import smtplib
import uuid
import mimetypes
import unicodedata
from datetime import datetime, timedelta
from email.message import EmailMessage
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, abort, has_request_context, jsonify, redirect, render_template, request, session
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "complaints.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app = Flask(__name__)
app.secret_key = "smart_secret"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

LANGUAGE_LABELS = {
    "en": "English",
    "te": "తెలుగు",
    "hi": "हिन्दी",
}

TRANSLATIONS = {
    "en": {
        "language": "Language",
        "dashboard": "Dashboard",
        "track": "Track",
        "logout": "Logout",
        "login": "Login",
        "register": "Register",
        "back": "Back",
        "welcome_title": "Welcome",
        "portal_name": "Complaint Portal",
        "welcome_subtitle": "Login or register to continue.",
        "total": "Total",
        "open": "Open",
        "resolved": "Resolved",
        "create_account": "Create Account",
        "verify_otp": "Verify OTP",
        "enter_credentials": "Enter credentials",
        "enter_details": "Enter details",
        "send_otp": "Send OTP",
        "username": "Username",
        "password": "Password",
        "phone": "Phone (+91XXXXXXXXXX)",
        "email": "Email address",
        "enter_otp": "Enter 6-digit OTP",
        "already_have_account": "Already have an account? Login",
        "create_account_link": "Create Account",
        "register_complaint": "Register Complaint",
        "register_help": "Choose a GHMC complaint. If you select Others, type or speak the complaint.",
        "complaint_type": "GHMC Complaint Type",
        "select_complaint": "Select complaint",
        "other_complaint": "Other Complaint",
        "other_complaint_placeholder": "Type your complaint here...",
        "voice_command": "Voice Command",
        "district": "District",
        "mandal": "Mandal",
        "pincode": "Pincode",
        "colony": "Colony / Locality",
        "address_hint": "Addresses are checked using district, pincode, and GPS boundary rules before they reach the department.",
        "priority_level": "Priority Level",
        "nearby_landmark": "Nearby Landmark",
        "landmark_placeholder": "School, bus stop, hospital, apartment gate",
        "people_affected": "People Affected",
        "use_current_location": "Use Current Location",
        "location_pending": "Current location not added yet. Manual address entry still works.",
        "map_preview": "Google Map Preview",
        "open_in_maps": "Open in Google Maps",
        "map_help": "The map updates when location is detected or when you finish typing the address.",
        "photos": "Photos (Photo Proof)",
        "submit_complaint": "Submit Complaint",
        "my_complaints": "My Complaints",
        "overdue": "Overdue",
        "auto_refresh": "Auto-refreshing every 10 seconds",
        "search_placeholder": "Search by ticket, area, or complaint",
        "all_statuses": "All statuses",
        "pending": "Pending",
        "in_progress": "In Progress",
        "closed": "Closed",
        "reopened": "Reopened",
        "no_complaints": "No complaints submitted yet.",
        "type": "Type",
        "department": "Department",
        "priority": "Priority",
        "level": "Level",
        "linked_main_ticket": "Linked Main Ticket",
        "sla": "SLA",
        "landmark": "Landmark",
        "address": "Address",
        "address_check": "Address Check",
        "escalation": "Escalation",
        "coordinates": "Coordinates",
        "track_this_complaint": "Track this complaint",
        "recent_alerts": "Recent Alerts",
        "live": "Live",
        "notifications_empty": "Notifications about escalations and updates will appear here.",
        "track_complaint": "Track Complaint",
        "tracking_title": "Complaint Tracking",
        "track_by_ticket": "Track By Ticket ID",
        "enter_ticket_id": "Enter Ticket ID",
        "filed": "Filed",
        "in_review": "In Review",
        "complaint": "Complaint",
        "estimated_resolution": "Estimated Resolution",
        "latest_department_note": "Latest Department Note",
        "complaint_timeline": "Complaint Timeline",
        "timeline_empty": "Timeline updates will appear here.",
        "citizen_feedback": "Citizen Feedback",
        "saved_rating": "Saved Rating",
        "saved_comment": "Saved Comment",
        "rate_resolution": "Rate Resolution",
        "choose_rating": "Choose rating",
        "feedback_comment": "Feedback Comment",
        "feedback_placeholder": "Share what went well or what still needs work",
        "save_feedback": "Save Feedback",
        "still_facing_issue": "Still facing the same issue?",
        "reopen_placeholder": "Explain why the complaint should be reopened",
        "reopen_complaint": "Reopen Complaint",
        "tracking_retry": "Tracking refresh paused. Retrying automatically.",
        "last_updated_at": "Last updated at",
    },
    "te": {
        "language": "భాష",
        "dashboard": "డ్యాష్‌బోర్డ్",
        "track": "ట్రాక్",
        "logout": "లాగ్ అవుట్",
        "login": "లాగిన్",
        "register": "నమోదు",
        "back": "వెనక్కి",
        "welcome_title": "స్వాగతం",
        "portal_name": "ఫిర్యాదు పోర్టల్",
        "welcome_subtitle": "కొనసాగించడానికి లాగిన్ చేయండి లేదా నమోదు చేసుకోండి.",
        "total": "మొత్తం",
        "open": "తెరవబడ్డవి",
        "resolved": "పరిష్కరించబడినవి",
        "create_account": "ఖాతా సృష్టించండి",
        "verify_otp": "OTP నిర్ధారించండి",
        "enter_credentials": "వివరాలు నమోదు చేయండి",
        "enter_details": "వివరాలు నమోదు చేయండి",
        "send_otp": "OTP పంపండి",
        "username": "వినియోగదారు పేరు",
        "password": "పాస్‌వర్డ్",
        "phone": "ఫోన్ (+91XXXXXXXXXX)",
        "email": "ఇమెయిల్ చిరునామా",
        "enter_otp": "6 అంకెల OTP నమోదు చేయండి",
        "already_have_account": "ఇప్పటికే ఖాతా ఉందా? లాగిన్",
        "create_account_link": "ఖాతా సృష్టించండి",
        "register_complaint": "ఫిర్యాదు నమోదు చేయండి",
        "register_help": "GHMC ఫిర్యాదును ఎంచుకోండి. Others ఎంచుకుంటే మీ ఫిర్యాదును టైప్ చేయండి లేదా మాట్లాడండి.",
        "complaint_type": "GHMC ఫిర్యాదు రకం",
        "select_complaint": "ఫిర్యాదు ఎంచుకోండి",
        "other_complaint": "ఇతర ఫిర్యాదు",
        "other_complaint_placeholder": "మీ ఫిర్యాదును ఇక్కడ టైప్ చేయండి...",
        "voice_command": "వాయిస్ కమాండ్",
        "district": "జిల్లా",
        "mandal": "మండలం",
        "pincode": "పిన్‌కోడ్",
        "colony": "కాలనీ / ప్రాంతం",
        "address_hint": "ఫిర్యాదు శాఖకు వెళ్లే ముందు జిల్లా, పిన్‌కోడ్, GPS సరిహద్దులతో చిరునామా తనిఖీ చేయబడుతుంది.",
        "priority_level": "ప్రాధాన్యత స్థాయి",
        "nearby_landmark": "సమీప గుర్తు స్థలం",
        "landmark_placeholder": "పాఠశాల, బస్ స్టాప్, ఆసుపత్రి, అపార్ట్‌మెంట్ గేట్",
        "people_affected": "ప్రభావితుల సంఖ్య",
        "use_current_location": "ప్రస్తుత స్థానం ఉపయోగించండి",
        "location_pending": "ప్రస్తుత స్థానం ఇంకా జోడించలేదు. చేతితో చిరునామా ఇవ్వవచ్చు.",
        "map_preview": "గూగుల్ మ్యాప్ ప్రివ్యూ",
        "open_in_maps": "గూగుల్ మ్యాప్స్‌లో తెరవండి",
        "map_help": "స్థానం గుర్తించినప్పుడు లేదా చిరునామా టైప్ పూర్తి చేసినప్పుడు మ్యాప్ నవీకరించబడుతుంది.",
        "photos": "ఫోటోలు (ఆధారంగా)",
        "submit_complaint": "ఫిర్యాదు సమర్పించండి",
        "my_complaints": "నా ఫిర్యాదులు",
        "overdue": "గడువు దాటినవి",
        "auto_refresh": "ప్రతి 10 సెకన్లకు ఆటో-రిఫ్రెష్ అవుతుంది",
        "search_placeholder": "టికెట్, ప్రాంతం లేదా ఫిర్యాదుతో శోధించండి",
        "all_statuses": "అన్ని స్థితులు",
        "pending": "పెండింగ్",
        "in_progress": "పనిలో ఉంది",
        "closed": "మూసివేయబడింది",
        "reopened": "మళ్లీ తెరవబడింది",
        "no_complaints": "ఇంకా ఎలాంటి ఫిర్యాదులు నమోదు కాలేదు.",
        "type": "రకం",
        "department": "శాఖ",
        "priority": "ప్రాధాన్యత",
        "level": "స్థాయి",
        "linked_main_ticket": "లింక్ చేసిన ప్రధాన టికెట్",
        "sla": "SLA",
        "landmark": "గుర్తు స్థలం",
        "address": "చిరునామా",
        "address_check": "చిరునామా తనిఖీ",
        "escalation": "ఎస్కలేషన్",
        "coordinates": "కోఆర్డినేట్లు",
        "track_this_complaint": "ఈ ఫిర్యాదును ట్రాక్ చేయండి",
        "recent_alerts": "ఇటీవలి అలర్ట్స్",
        "live": "ప్రత్యక్షం",
        "notifications_empty": "ఎస్కలేషన్‌లు మరియు నవీకరణల గురించి నోటిఫికేషన్‌లు ఇక్కడ కనిపిస్తాయి.",
        "track_complaint": "ఫిర్యాదును ట్రాక్ చేయండి",
        "tracking_title": "ఫిర్యాదు ట్రాకింగ్",
        "track_by_ticket": "టికెట్ ID ద్వారా ట్రాక్ చేయండి",
        "enter_ticket_id": "టికెట్ ID నమోదు చేయండి",
        "filed": "నమోదు",
        "in_review": "సమీక్షలో",
        "complaint": "ఫిర్యాదు",
        "estimated_resolution": "అంచనా పరిష్కార సమయం",
        "latest_department_note": "తాజా శాఖ గమనిక",
        "complaint_timeline": "ఫిర్యాదు టైమ్‌లైన్",
        "timeline_empty": "టైమ్‌లైన్ నవీకరణలు ఇక్కడ కనిపిస్తాయి.",
        "citizen_feedback": "పౌర అభిప్రాయం",
        "saved_rating": "సేవ్ చేసిన రేటింగ్",
        "saved_comment": "సేవ్ చేసిన వ్యాఖ్య",
        "rate_resolution": "పరిష్కారాన్ని రేట్ చేయండి",
        "choose_rating": "రేటింగ్ ఎంచుకోండి",
        "feedback_comment": "అభిప్రాయం",
        "feedback_placeholder": "ఏం బాగా జరిగిందో లేదా ఇంకా ఏమి చేయాలో చెప్పండి",
        "save_feedback": "అభిప్రాయం సేవ్ చేయండి",
        "still_facing_issue": "ఇంకా ఇదే సమస్య ఎదురవుతోందా?",
        "reopen_placeholder": "ఫిర్యాదును మళ్లీ ఎందుకు తెరవాలి అని వివరించండి",
        "reopen_complaint": "ఫిర్యాదును మళ్లీ తెరవండి",
        "tracking_retry": "ట్రాకింగ్ రిఫ్రెష్ ఆగింది. స్వయంచాలకంగా మళ్లీ ప్రయత్నిస్తుంది.",
        "last_updated_at": "చివరిసారి నవీకరించబడింది",
    },
    "hi": {
        "language": "भाषा",
        "dashboard": "डैशबोर्ड",
        "track": "ट्रैक",
        "logout": "लॉगआउट",
        "login": "लॉगिन",
        "register": "रजिस्टर",
        "back": "वापस",
        "welcome_title": "स्वागत है",
        "portal_name": "शिकायत पोर्टल",
        "welcome_subtitle": "आगे बढ़ने के लिए लॉगिन करें या रजिस्टर करें।",
        "total": "कुल",
        "open": "खुले",
        "resolved": "समाधान किए गए",
        "create_account": "खाता बनाएं",
        "verify_otp": "OTP सत्यापित करें",
        "enter_credentials": "जानकारी दर्ज करें",
        "enter_details": "विवरण दर्ज करें",
        "send_otp": "OTP भेजें",
        "username": "यूज़रनेम",
        "password": "पासवर्ड",
        "phone": "फोन (+91XXXXXXXXXX)",
        "email": "ईमेल पता",
        "enter_otp": "6 अंकों का OTP दर्ज करें",
        "already_have_account": "पहले से खाता है? लॉगिन करें",
        "create_account_link": "खाता बनाएं",
        "register_complaint": "शिकायत दर्ज करें",
        "register_help": "GHMC शिकायत चुनें। यदि आप Others चुनते हैं, तो शिकायत लिखें या बोलें।",
        "complaint_type": "GHMC शिकायत प्रकार",
        "select_complaint": "शिकायत चुनें",
        "other_complaint": "अन्य शिकायत",
        "other_complaint_placeholder": "अपनी शिकायत यहां लिखें...",
        "voice_command": "वॉइस कमांड",
        "district": "जिला",
        "mandal": "मंडल",
        "pincode": "पिनकोड",
        "colony": "कॉलोनी / क्षेत्र",
        "address_hint": "शिकायत विभाग तक पहुंचने से पहले पते की जांच जिला, पिनकोड और GPS सीमा से की जाती है।",
        "priority_level": "प्राथमिकता स्तर",
        "nearby_landmark": "नज़दीकी पहचान स्थान",
        "landmark_placeholder": "स्कूल, बस स्टॉप, अस्पताल, अपार्टमेंट गेट",
        "people_affected": "प्रभावित लोगों की संख्या",
        "use_current_location": "वर्तमान लोकेशन उपयोग करें",
        "location_pending": "वर्तमान लोकेशन अभी जोड़ी नहीं गई है। आप पता हाथ से भर सकते हैं।",
        "map_preview": "गूगल मैप प्रीव्यू",
        "open_in_maps": "गूगल मैप्स में खोलें",
        "map_help": "लोकेशन मिलने या पता टाइप पूरा होने पर मैप अपडेट होता है।",
        "photos": "फोटो (सबूत)",
        "submit_complaint": "शिकायत जमा करें",
        "my_complaints": "मेरी शिकायतें",
        "overdue": "देरी वाली",
        "auto_refresh": "हर 10 सेकंड में अपने आप रिफ्रेश होता है",
        "search_placeholder": "टिकट, क्षेत्र या शिकायत से खोजें",
        "all_statuses": "सभी स्थितियां",
        "pending": "लंबित",
        "in_progress": "प्रगति में",
        "closed": "बंद",
        "reopened": "फिर से खोला गया",
        "no_complaints": "अभी तक कोई शिकायत दर्ज नहीं हुई है।",
        "type": "प्रकार",
        "department": "विभाग",
        "priority": "प्राथमिकता",
        "level": "स्तर",
        "linked_main_ticket": "लिंक किया गया मुख्य टिकट",
        "sla": "SLA",
        "landmark": "पहचान स्थान",
        "address": "पता",
        "address_check": "पता जांच",
        "escalation": "एस्केलेशन",
        "coordinates": "निर्देशांक",
        "track_this_complaint": "इस शिकायत को ट्रैक करें",
        "recent_alerts": "हाल की सूचनाएं",
        "live": "लाइव",
        "notifications_empty": "एस्केलेशन और अपडेट की सूचनाएं यहां दिखेंगी।",
        "track_complaint": "शिकायत ट्रैक करें",
        "tracking_title": "शिकायत ट्रैकिंग",
        "track_by_ticket": "टिकट ID से ट्रैक करें",
        "enter_ticket_id": "टिकट ID दर्ज करें",
        "filed": "दर्ज",
        "in_review": "समीक्षा में",
        "complaint": "शिकायत",
        "estimated_resolution": "अनुमानित समाधान समय",
        "latest_department_note": "नवीनतम विभागीय टिप्पणी",
        "complaint_timeline": "शिकायत टाइमलाइन",
        "timeline_empty": "टाइमलाइन अपडेट यहां दिखेंगे।",
        "citizen_feedback": "नागरिक प्रतिक्रिया",
        "saved_rating": "सहेजी गई रेटिंग",
        "saved_comment": "सहेजी गई टिप्पणी",
        "rate_resolution": "समाधान को रेट करें",
        "choose_rating": "रेटिंग चुनें",
        "feedback_comment": "प्रतिक्रिया",
        "feedback_placeholder": "क्या अच्छा हुआ या क्या बाकी है, बताएं",
        "save_feedback": "प्रतिक्रिया सहेजें",
        "still_facing_issue": "क्या अभी भी वही समस्या है?",
        "reopen_placeholder": "बताएं कि शिकायत फिर से क्यों खोलनी चाहिए",
        "reopen_complaint": "शिकायत फिर से खोलें",
        "tracking_retry": "ट्रैकिंग रिफ्रेश रुका है। अपने आप फिर से कोशिश होगी।",
        "last_updated_at": "आखिरी अपडेट",
    },
}

GHMC_COMPLAINTS = [
    ("Water Leakage", "Water"),
    ("No Water Supply", "Water"),
    ("Drainage Overflow", "Water"),
    ("Street Light Not Working", "Electrical"),
    ("Power Pole / Electrical Hazard", "Electrical"),
    ("Road Damage / Potholes", "Public Works"),
    ("Garbage Not Cleared", "Sanitation"),
    ("Mosquito / Sanitation Issue", "Sanitation"),
    ("Building Permission / Town Planning", "Town Planning"),
    ("Property Tax / Trade License", "Accounts"),
    ("Online Portal / App Issue", "IT"),
    ("Employee Behaviour / Staff Issue", "HR"),
    ("Others", "Others"),
]

DEPARTMENT_LEVEL_CONTACTS = {
    "Water": {
        1: {"username": "water_level1", "phone": "+919059589588"},
        2: {"username": "water_level2", "phone": "+917386017589"},
        3: {"username": "water_supreme", "phone": "+917207842992"},
    },
    "IT": {
        1: {"username": "it_level1", "phone": "+919182250004"},
        2: {"username": "it_level2", "phone": "+919182250005"},
        3: {"username": "it_supreme", "phone": "+919182250006"},
    },
    "Electrical": {
        1: {"username": "electrical_level1", "phone": "+919182250007"},
        2: {"username": "electrical_level2", "phone": "+919182250008"},
        3: {"username": "electrical_supreme", "phone": "+919182250009"},
    },
    "HR": {
        1: {"username": "hr_level1", "phone": "+919182250010"},
        2: {"username": "hr_level2", "phone": "+919182250011"},
        3: {"username": "hr_supreme", "phone": "+919182250012"},
    },
    "Accounts": {
        1: {"username": "accounts_level1", "phone": "+919182250013"},
        2: {"username": "accounts_level2", "phone": "+919182250014"},
        3: {"username": "accounts_supreme", "phone": "+919182250015"},
    },
    "Public Works": {
        1: {"username": "publicworks_level1", "phone": "+919182250019"},
        2: {"username": "publicworks_level2", "phone": "+919182250020"},
        3: {"username": "publicworks_supreme", "phone": "+919182250021"},
    },
    "Others": {
        1: {"username": "others_level1", "phone": "+919182250016"},
        2: {"username": "others_level2", "phone": "+919182250017"},
        3: {"username": "others_supreme", "phone": "+919182250018"},
    },
}

LEVEL_PHOTO_COLUMNS = {
    1: "level1_photo",
    2: "level2_photo",
    3: "level3_photo",
}

VALID_GHMC_DISTRICTS = {
    "hyderabad",
    "medchal malkajgiri",
    "rangareddy",
    "ranga reddy",
    "sangareddy",
}

VALIDATION_STATUS_META = {
    "Verified": "verified",
    "Needs Review": "review",
    "Invalid": "invalid",
}

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC5510ae1aa3c373a92b2844bbd251818d")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "863334fad7de3126abd4174f0fbb3b08")
TWILIO_PHONE = os.getenv("TWILIO_PHONE", "+16624957425")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
DEV_CONSOLE_OTP_FALLBACK = os.getenv("DEV_CONSOLE_OTP_FALLBACK", "1").lower() in {"1", "true", "yes", "on"}

twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN) if ACCOUNT_SID and AUTH_TOKEN else None


USERNAME_ALIASES = {
    "waterlevel_2": "water_level2",
    "water_level_2": "water_level2",
    "water_level2": "water_level2",
    "waterlevel2": "water_level2",
    "water level2": "water_level2",
    "water level 2": "water_level2",
    "water_supreme": "water_supreme",
    "water supreme": "water_supreme",
    "supreme": "water_supreme",
}


def send_sms(phone, message):
    def console_otp_fallback(reason):
        if DEV_CONSOLE_OTP_FALLBACK and "OTP" in (message or "").upper():
            otp_match = re.search(r"\b(\d{6})\b", message or "")
            if has_request_context() and otp_match:
                session["dev_fallback_otp"] = otp_match.group(1)
            print(f"DEV OTP FALLBACK [{reason}] for {phone}: {message}")
            return True
        return False

    if not twilio_client or not TWILIO_PHONE:
        print("SMS ERROR: Twilio credentials/phone are not configured.")
        return console_otp_fallback("twilio_not_configured")

    to_phone = normalize_phone(phone)
    from_phone = normalize_phone(TWILIO_PHONE, default_country_code=None)

    if not to_phone:
        print(f"SMS ERROR: Invalid recipient phone number: {phone!r}")
        return console_otp_fallback("invalid_recipient_phone")
    if not from_phone:
        print(f"SMS ERROR: Invalid TWILIO_PHONE value: {TWILIO_PHONE!r}")
        return console_otp_fallback("invalid_twilio_phone")

    try:
        msg = twilio_client.messages.create(body=message, from_=from_phone, to=to_phone)
        print(f"SMS SENT: sid={msg.sid} to={to_phone}")
        return True
    except TwilioRestException as exc:
        code = getattr(exc, "code", None)
        hint = ""
        if code == 21608:
            hint = " Trial account can send SMS only to verified numbers."
        elif code == 21408:
            hint = " Enable SMS permissions for the destination country in Twilio."
        elif code == 21211:
            hint = " Destination number format is invalid; use E.164 (+countrycode...)."
        print(f"SMS ERROR: Twilio code={code} status={getattr(exc, 'status', None)} message={exc.msg}.{hint}")
        return console_otp_fallback(f"twilio_error_{code}")
    except Exception as exc:
        print("SMS ERROR:", exc)
        return console_otp_fallback("unexpected_sms_exception")


def normalize_phone(phone, default_country_code="+91"):
    raw = (phone or "").strip()
    if not raw:
        return None

    if raw.startswith("+"):
        digits = "+" + "".join(ch for ch in raw[1:] if ch.isdigit())
        return digits if len(digits) > 7 else None

    digits_only = "".join(ch for ch in raw if ch.isdigit())
    if not digits_only:
        return None

    if default_country_code and len(digits_only) == 10:
        return f"{default_country_code}{digits_only}"

    return f"+{digits_only}"


def send_email(to_email, subject, message, attachments=None):
    if not all([SMTP_HOST, SMTP_PORT, SMTP_FROM_EMAIL]):
        return False

    try:
        email = EmailMessage()
        email["Subject"] = subject
        email["From"] = SMTP_FROM_EMAIL
        email["To"] = to_email
        email.set_content(message)

        if attachments:
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(attachment_path)
                        mime_type, _ = mimetypes.guess_type(attachment_path)
                        if mime_type:
                            maintype, subtype = mime_type.split('/', 1)
                        else:
                            maintype, subtype = 'application', 'octet-stream'
                        email.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(email)
        return True
    except Exception as exc:
        print("EMAIL ERROR:", exc)
        return False


def send_notifications(phone=None, email=None, sms_message=None, email_subject=None, email_message=None, attachments=None):
    sms_sent = False
    email_sent = False

    if phone and sms_message:
        sms_sent = send_sms(phone, sms_message)
    if email and email_subject and email_message:
        email_sent = send_email(email, email_subject, email_message, attachments)

    return sms_sent, email_sent


def get_current_language():
    selected = session.get("language", "en")
    return selected if selected in TRANSLATIONS else "en"


def translate(key, language=None):
    active_language = language or get_current_language()
    return TRANSLATIONS.get(active_language, TRANSLATIONS["en"]).get(
        key,
        TRANSLATIONS["en"].get(key, key),
    )


@app.context_processor
def inject_i18n():
    current_language = get_current_language()
    return {
        "t": lambda key: translate(key, current_language),
        "current_language": current_language,
        "available_languages": LANGUAGE_LABELS,
        "ui_text": TRANSLATIONS.get(current_language, TRANSLATIONS["en"]),
    }


def create_notification(username, message):
    if not username or not message:
        return

    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO notifications(username, message, time)
            VALUES (?, ?, ?)
            """,
            (username, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        db.commit()
    finally:
        db.close()


def get_notifications(username, limit=8):
    db = get_db()
    notifications = db.execute(
        """
        SELECT * FROM notifications
        WHERE username=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (username, limit),
    ).fetchall()
    db.close()
    return notifications


def add_history_event(db, complaint_id, event_type, message):
    if not complaint_id or not message:
        return

    db.execute(
        """
        INSERT INTO complaint_history(complaint_id, event_type, message, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            complaint_id,
            event_type,
            message,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


def clear_pending_login():
    session.pop("pending_login_user", None)
    session.pop("pending_login_role", None)
    session.pop("pending_login_department", None)
    session.pop("pending_department_level", None)
    session.pop("pending_otp", None)
    session.pop("pending_otp_expiry", None)
    session.pop("dev_fallback_otp", None)


def clear_pending_register():
    session.pop("pending_register_username", None)
    session.pop("pending_register_password_hash", None)
    session.pop("pending_register_phone", None)
    session.pop("pending_register_email", None)
    session.pop("pending_register_otp", None)
    session.pop("pending_register_otp_expiry", None)
    session.pop("dev_fallback_otp", None)


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def configured_phone_for_department_user(username):
    for level_map in DEPARTMENT_LEVEL_CONTACTS.values():
        for level_info in level_map.values():
            if level_info["username"] == username:
                return level_info["phone"]
    return None


def resolve_login_username(username):
    username = (username or "").strip()
    if not username:
        return username
    normalized = re.sub(r"[_\-\s]+", "_", username.lower()).strip("_")
    normalized = re.sub(r"level_(\d)", r"level\1", normalized)
    seeded_usernames = {
        info["username"].lower()
        for department_levels in DEPARTMENT_LEVEL_CONTACTS.values()
        for info in department_levels.values()
    }
    alias = USERNAME_ALIASES.get(username.lower()) or USERNAME_ALIASES.get(normalized)
    if alias:
        return alias
    if normalized in seeded_usernames:
        return normalized
    return username


def seed_department_levels(db):
    for department, level_map in DEPARTMENT_LEVEL_CONTACTS.items():
        for level_info in level_map.values():
            default_password_hash = generate_password_hash(level_info["phone"])
            user = db.execute(
                "SELECT id, email, password FROM users WHERE username=?",
                (level_info["username"],),
            ).fetchone()

            if user:
                existing_password = user["password"] or ""
                password_matches_phone = False
                try:
                    password_matches_phone = check_password_hash(
                        existing_password, level_info["phone"]
                    )
                except Exception:
                    password_matches_phone = False

                # Keep seeded department logins consistent: default password is the saved phone number.
                if not password_matches_phone:
                    db.execute(
                        """
                        UPDATE users
                        SET password=?
                        WHERE username=?
                        """,
                        (default_password_hash, level_info["username"]),
                    )

                db.execute(
                    """
                    UPDATE users
                    SET role='department', department=?, phone=?
                    WHERE username=?
                    """,
                    (department, level_info["phone"], level_info["username"]),
                )
            else:
                db.execute(
                    """
                    INSERT INTO users(username, password, role, phone, email, department)
                    VALUES (?, ?, 'department', ?, ?, ?)
                    """,
                    (
                        level_info["username"],
                        default_password_hash,
                        level_info["phone"],
                        None,
                        department,
                    ),
                )


def migrate_database():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            phone TEXT,
            email TEXT,
            department TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            complaint_type TEXT,
            complaint TEXT,
            status TEXT,
            department TEXT DEFAULT 'Not Assigned',
            severity TEXT DEFAULT 'Medium',
            landmark TEXT,
            affected_people INTEGER DEFAULT 1,
            sla_deadline TEXT,
            department_note TEXT,
            estimated_resolution TEXT,
            address_district TEXT,
            address_mandal TEXT,
            address_pincode TEXT,
            address_colony TEXT,
            latitude TEXT,
            longitude TEXT,
            address_validation_status TEXT DEFAULT 'Needs Review',
            address_validation_reason TEXT,
            ticket_id TEXT,
            file_name TEXT,
            user_photos TEXT,
            level1_photo TEXT,
            level2_photo TEXT,
            level3_photo TEXT,
            escalation_message TEXT,
            level INTEGER DEFAULT 1,
            feedback_rating INTEGER,
            feedback_comment TEXT,
            reopened_count INTEGER DEFAULT 0,
            linked_ticket_id TEXT,
            created_at TEXT,
            last_updated TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            time TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS complaint_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER,
            event_type TEXT,
            message TEXT,
            created_at TEXT
        )
        """
    )

    complaint_columns = {
        "complaint_type": "ALTER TABLE complaints ADD COLUMN complaint_type TEXT",
        "department": "ALTER TABLE complaints ADD COLUMN department TEXT DEFAULT 'Not Assigned'",
        "severity": "ALTER TABLE complaints ADD COLUMN severity TEXT DEFAULT 'Medium'",
        "landmark": "ALTER TABLE complaints ADD COLUMN landmark TEXT",
        "affected_people": "ALTER TABLE complaints ADD COLUMN affected_people INTEGER DEFAULT 1",
        "sla_deadline": "ALTER TABLE complaints ADD COLUMN sla_deadline TEXT",
        "department_note": "ALTER TABLE complaints ADD COLUMN department_note TEXT",
        "estimated_resolution": "ALTER TABLE complaints ADD COLUMN estimated_resolution TEXT",
        "address_district": "ALTER TABLE complaints ADD COLUMN address_district TEXT",
        "address_mandal": "ALTER TABLE complaints ADD COLUMN address_mandal TEXT",
        "address_pincode": "ALTER TABLE complaints ADD COLUMN address_pincode TEXT",
        "address_colony": "ALTER TABLE complaints ADD COLUMN address_colony TEXT",
        "latitude": "ALTER TABLE complaints ADD COLUMN latitude TEXT",
        "longitude": "ALTER TABLE complaints ADD COLUMN longitude TEXT",
        "address_validation_status": "ALTER TABLE complaints ADD COLUMN address_validation_status TEXT DEFAULT 'Needs Review'",
        "address_validation_reason": "ALTER TABLE complaints ADD COLUMN address_validation_reason TEXT",
        "user_photos": "ALTER TABLE complaints ADD COLUMN user_photos TEXT",
        "level1_photo": "ALTER TABLE complaints ADD COLUMN level1_photo TEXT",
        "level2_photo": "ALTER TABLE complaints ADD COLUMN level2_photo TEXT",
        "level3_photo": "ALTER TABLE complaints ADD COLUMN level3_photo TEXT",
        "escalation_message": "ALTER TABLE complaints ADD COLUMN escalation_message TEXT",
        "level": "ALTER TABLE complaints ADD COLUMN level INTEGER DEFAULT 1",
        "feedback_rating": "ALTER TABLE complaints ADD COLUMN feedback_rating INTEGER",
        "feedback_comment": "ALTER TABLE complaints ADD COLUMN feedback_comment TEXT",
        "reopened_count": "ALTER TABLE complaints ADD COLUMN reopened_count INTEGER DEFAULT 0",
        "linked_ticket_id": "ALTER TABLE complaints ADD COLUMN linked_ticket_id TEXT",
        "created_at": "ALTER TABLE complaints ADD COLUMN created_at TEXT",
        "last_updated": "ALTER TABLE complaints ADD COLUMN last_updated TEXT",
        "file_name": "ALTER TABLE complaints ADD COLUMN file_name TEXT",
    }
    user_columns = {
        "phone": "ALTER TABLE users ADD COLUMN phone TEXT",
        "email": "ALTER TABLE users ADD COLUMN email TEXT",
        "department": "ALTER TABLE users ADD COLUMN department TEXT",
    }

    existing_complaint_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(complaints)").fetchall()
    }
    existing_user_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()
    }

    for column, statement in complaint_columns.items():
        if column not in existing_complaint_columns:
            db.execute(statement)
    for column, statement in user_columns.items():
        if column not in existing_user_columns:
            db.execute(statement)

    complaints_to_backfill = db.execute(
        """
        SELECT id, address_district, address_mandal, address_pincode, address_colony, latitude, longitude
        FROM complaints
        WHERE address_validation_status IS NULL OR TRIM(address_validation_status) = ''
        """
    ).fetchall()
    for complaint in complaints_to_backfill:
        validation = validate_address(
            complaint["address_district"],
            complaint["address_mandal"],
            complaint["address_pincode"],
            complaint["address_colony"],
            complaint["latitude"],
            complaint["longitude"],
        )
        db.execute(
            """
            UPDATE complaints
            SET address_validation_status=?, address_validation_reason=?
            WHERE id=?
            """,
            (validation["status"], validation["reason"], complaint["id"]),
        )

    seed_department_levels(db)

    db.commit()
    db.close()


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                return redirect("/login")
            if session.get("role") not in roles:
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def save_files(files):
    saved = []
    for file in files:
        if not file or not file.filename:
            continue
        unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))
        saved.append(unique_name)
    return saved


def complaint_options():
    return [option[0] for option in GHMC_COMPLAINTS]


def normalize_location_text(value):
    value = (value or "").strip().lower()
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\u2010-\u2015\u2212]", "-", value)
    value = re.sub(r"\b(district|dist\.?|dt\.?)\b", "", value)
    value = value.replace("-", " ")
    value = re.sub(r"[^a-z0-9\s]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def has_reasonable_location_text(value, minimum_length=3):
    cleaned = (value or "").strip()
    cleaned = unicodedata.normalize("NFKC", cleaned)
    cleaned = re.sub(r"[\u2010-\u2015\u2212]", "-", cleaned)
    if len(cleaned) < minimum_length:
        return False
    return bool(re.fullmatch(r"[^\W_][\w\s,./()'’\-&]*", cleaned, flags=re.UNICODE))


def validate_address(district, mandal, pincode, colony, latitude, longitude):
    reasons = []
    verified_signals = 0

    district = (district or "").strip()
    mandal = (mandal or "").strip()
    pincode = (pincode or "").strip()
    colony = (colony or "").strip()
    latitude = (latitude or "").strip()
    longitude = (longitude or "").strip()

    district_is_reasonable = has_reasonable_location_text(district)
    if not district_is_reasonable:
        reasons.append("District looks incomplete or contains unsupported characters.")
    if not has_reasonable_location_text(mandal):
        reasons.append("Mandal looks incomplete or contains unsupported characters.")
    if not has_reasonable_location_text(colony, minimum_length=2):
        reasons.append("Colony or locality looks incomplete or contains unsupported characters.")

    if not re.fullmatch(r"\d{6}", pincode):
        reasons.append("Pincode must be exactly 6 digits.")
    elif pincode.startswith("500"):
        verified_signals += 1
    else:
        reasons.append("Pincode does not match the usual GHMC range.")

    if district_is_reasonable:
        if normalize_location_text(district) in VALID_GHMC_DISTRICTS:
            verified_signals += 1
        else:
            reasons.append("District is outside the configured GHMC service area.")

    if latitude or longitude:
        try:
            lat_value = float(latitude)
            lon_value = float(longitude)
        except (TypeError, ValueError):
            reasons.append("Location coordinates are not valid numbers.")
        else:
            if not (-90 <= lat_value <= 90 and -180 <= lon_value <= 180):
                reasons.append("Location coordinates are outside valid map bounds.")
            elif 17.20 <= lat_value <= 17.62 and 78.20 <= lon_value <= 78.72:
                verified_signals += 2
            else:
                reasons.append("GPS location is outside the configured GHMC boundary.")
    else:
        reasons.append("Current location was not attached, so the address needs manual review.")

    hard_failures = {
        "Pincode must be exactly 6 digits.",
        "District is outside the configured GHMC service area.",
        "Location coordinates are not valid numbers.",
        "Location coordinates are outside valid map bounds.",
        "GPS location is outside the configured GHMC boundary.",
    }
    if any(reason in hard_failures for reason in reasons):
        status = "Invalid"
    elif verified_signals >= 3 and not reasons:
        status = "Verified"
    else:
        status = "Needs Review"

    if status == "Verified":
        reason_text = "Address matched district, pincode, and map boundary checks."
    else:
        reason_text = " ".join(reasons)

    return {
        "status": status,
        "reason": reason_text,
    }


def calculate_sla_hours(severity, department, affected_people):
    severity_hours = {
        "Low": 72,
        "Medium": 48,
        "High": 24,
        "Critical": 8,
    }
    hours = severity_hours.get(severity, 48)

    if department in {"Water", "Sanitation", "Electrical"}:
        hours = min(hours, 24 if severity in {"High", "Critical"} else hours)
    if (affected_people or 1) >= 25:
        hours = max(6, hours - 12)

    return max(hours, 6)


def complaints_match_location(row, district, mandal, pincode, colony):
    return (
        normalize_location_text(row["address_colony"]) == normalize_location_text(colony)
        and normalize_location_text(row["address_mandal"]) == normalize_location_text(mandal)
        and (row["address_pincode"] or "").strip() == (pincode or "").strip()
        and normalize_location_text(row["address_district"]) == normalize_location_text(district)
    )


def find_matching_open_complaint(db, complaint_type, district, mandal, pincode, colony):
    candidates = db.execute(
        """
        SELECT *
        FROM complaints
        WHERE complaint_type=? AND status NOT IN ('Resolved', 'Closed')
        ORDER BY CASE WHEN linked_ticket_id IS NULL OR TRIM(linked_ticket_id) = '' THEN 0 ELSE 1 END, id ASC
        """,
        (complaint_type,),
    ).fetchall()

    for row in candidates:
        if complaints_match_location(row, district, mandal, pincode, colony):
            if row["linked_ticket_id"]:
                parent = db.execute(
                    "SELECT * FROM complaints WHERE ticket_id=?",
                    (row["linked_ticket_id"],),
                ).fetchone()
                return parent or row
            return row

    return None


def format_eta(sla_deadline, status):
    if not sla_deadline:
        return ""

    try:
        deadline = datetime.strptime(sla_deadline, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ""

    delta = deadline - datetime.now()
    total_hours = int(abs(delta.total_seconds()) // 3600)

    if status in {"Resolved", "Closed"}:
        return "Closed within SLA" if delta.total_seconds() >= 0 else "Closed after SLA"
    if delta.total_seconds() >= 0:
        return f"Due in {max(total_hours, 1)} hrs"
    return f"Overdue by {max(total_hours, 1)} hrs"


def get_department_level(username):
    username = (username or "").lower()
    if re.search(r"level[_\-\s]*1", username):
        return 1
    if re.search(r"level[_\-\s]*2", username):
        return 2
    if "supreme" in username or re.search(r"level[_\-\s]*3", username):
        return 3
    return 1


def department_for_complaint(complaint_type):
    for label, department in GHMC_COMPLAINTS:
        if label == complaint_type:
            return department
    return "Others"


def get_department_contact(db, department, level=1):
    if not department:
        return None
    contacts = get_department_contacts(db, department, levels=[level])
    if contacts:
        return contacts[0]
    return None


def get_department_contacts(db, department, levels=None):
    if not department:
        return []

    level_map = DEPARTMENT_LEVEL_CONTACTS.get(department, {})
    if not level_map:
        return []

    requested_levels = sorted(level_map) if levels is None else levels
    contacts = []
    seen = set()

    for level in requested_levels:
        level_info = level_map.get(level)
        if not level_info:
            continue

        row = db.execute(
            """
            SELECT username, phone, email FROM users
            WHERE role='department' AND department=? AND username=?
            """,
            (department, level_info["username"]),
        ).fetchone()
        if row and row["username"] not in seen:
            contacts.append(row)
            seen.add(row["username"])

    return contacts


def get_user_complaints(username):
    db = get_db()
    complaints = db.execute(
        "SELECT * FROM complaints WHERE name=? ORDER BY id DESC",
        (username,),
    ).fetchall()
    db.close()
    return complaints


def get_user_dashboard_metrics(username):
    db = get_db()
    row = db.execute(
        """
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS open_count,
            SUM(CASE WHEN status NOT IN ('Resolved', 'Closed') AND sla_deadline IS NOT NULL AND sla_deadline < ? THEN 1 ELSE 0 END) AS overdue_count,
            SUM(CASE WHEN feedback_rating >= 4 THEN 1 ELSE 0 END) AS positive_feedback_count
        FROM complaints
        WHERE name=?
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username),
    ).fetchone()
    db.close()
    return row


def get_department_dashboard_data(department, department_level, status_filter="", search_term=""):
    db = get_db()
    base_query = "SELECT * FROM complaints WHERE department=? AND level=?"
    params = [department, department_level]

    if status_filter:
        base_query += " AND status=?"
        params.append(status_filter)
    if search_term:
        base_query += " AND (ticket_id LIKE ? OR name LIKE ? OR complaint LIKE ? OR address_colony LIKE ?)"
        like_term = f"%{search_term}%"
        params.extend([like_term, like_term, like_term, like_term])

    base_query += " ORDER BY CASE WHEN severity='Critical' THEN 1 WHEN severity='High' THEN 2 WHEN severity='Medium' THEN 3 ELSE 4 END, id DESC"
    data = db.execute(base_query, params).fetchall()
    summary_row = db.execute(
        """
        SELECT
            SUM(CASE WHEN status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_count,
            SUM(CASE WHEN severity IN ('High', 'Critical') AND status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS urgent_count,
            SUM(CASE WHEN status NOT IN ('Resolved', 'Closed') AND sla_deadline IS NOT NULL AND sla_deadline < ? THEN 1 ELSE 0 END) AS overdue_count
        FROM complaints
        WHERE department=?
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), department),
    ).fetchone()
    recent_activity = db.execute(
        """
        SELECT c.ticket_id, h.message, h.created_at
        FROM complaint_history h
        JOIN complaints c ON c.id = h.complaint_id
        WHERE c.department=?
        ORDER BY h.id DESC
        LIMIT 6
        """,
        (department,),
    ).fetchall()
    db.close()
    return {
        "data": data,
        "summary": summary_row,
        "recent_activity": recent_activity,
        "status_filter": status_filter,
        "search_term": search_term,
    }


def get_portal_snapshot():
    db = get_db()
    row = db.execute(
        """
        SELECT
            COUNT(*) AS total_complaints,
            SUM(CASE WHEN status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_cases,
            SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS resolved_cases,
            COUNT(DISTINCT department) AS active_departments
        FROM complaints
        """
    ).fetchone()
    db.close()
    return row


def get_complaint_history(complaint_id):
    db = get_db()
    history = db.execute(
        """
        SELECT * FROM complaint_history
        WHERE complaint_id=?
        ORDER BY id DESC
        """,
        (complaint_id,),
    ).fetchall()
    db.close()
    return history


def serialize_complaint(row):
    if not row:
        return None

    photos = []
    if row["user_photos"]:
        photos = [photo for photo in row["user_photos"].split(",") if photo]

    status_step_map = {
        "Pending": 1,
        "In Progress": 2,
        "Reopened": 2,
        "Resolved": 3,
        "Closed": 4,
    }
    current_step = status_step_map.get(row["status"], 1)

    return {
        "id": row["id"],
        "ticket_id": row["ticket_id"],
        "linked_ticket_id": row["linked_ticket_id"] or "",
        "is_linked": bool(row["linked_ticket_id"]),
        "complaint_type": row["complaint_type"] or "Others",
        "complaint": row["complaint"],
        "status": row["status"],
        "status_step": current_step,
        "department": row["department"],
        "level": row["level"] or 1,
        "severity": row["severity"] or "Medium",
        "landmark": row["landmark"] or "",
        "affected_people": row["affected_people"] or 1,
        "sla_deadline": row["sla_deadline"] or "",
        "sla_label": format_eta(row["sla_deadline"], row["status"]),
        "feedback_rating": row["feedback_rating"] or "",
        "feedback_comment": row["feedback_comment"] or "",
        "reopened_count": row["reopened_count"] or 0,
        "department_note": row["department_note"] or "",
        "estimated_resolution": row["estimated_resolution"] or "",
        "address_district": row["address_district"] or "",
        "address_mandal": row["address_mandal"] or "",
        "address_pincode": row["address_pincode"] or "",
        "address_colony": row["address_colony"] or "",
        "latitude": row["latitude"] or "",
        "longitude": row["longitude"] or "",
        "address_validation_status": row["address_validation_status"] or "Needs Review",
        "address_validation_reason": row["address_validation_reason"] or "",
        "address_validation_class": VALIDATION_STATUS_META.get(
            row["address_validation_status"] or "Needs Review",
            "review",
        ),
        "escalation_message": row["escalation_message"] or "",
        "user_photos": photos,
        "level1_photo": row["level1_photo"] or "",
        "level2_photo": row["level2_photo"] or "",
        "level3_photo": row["level3_photo"] or "",
        "last_updated": row["last_updated"] or "",
    }


def auto_escalation():
    db = get_db()
    now = datetime.now()
    complaints = db.execute(
        """
        SELECT * FROM complaints
        WHERE status NOT IN ('Resolved', 'Closed')
        """
    ).fetchall()

    for complaint in complaints:
        reference_time_value = complaint["last_updated"] or complaint["created_at"]
        if not reference_time_value:
            continue

        reference_time = datetime.strptime(reference_time_value, "%Y-%m-%d %H:%M:%S")
        hours_passed = (now - reference_time).total_seconds() / 3600
        department = complaint["department"]
        level = complaint["level"] or 1

        if department in (None, "", "Not Assigned"):
            continue

        escalation_message = None
        next_level = None
        if hours_passed >= 48 and level == 2:
            escalation_message = "Escalated to Level 3 for urgent action"
            next_level = 3
        elif hours_passed >= 24 and level == 1:
            escalation_message = "Escalated to Level 2 for follow-up"
            next_level = 2

        if not next_level:
            continue

        db.execute(
            """
            UPDATE complaints
            SET level=?, escalation_message=?, last_updated=?
            WHERE id=?
            """,
            (
                next_level,
                escalation_message,
                now.strftime("%Y-%m-%d %H:%M:%S"),
                complaint["id"],
            ),
        )
        add_history_event(
            db,
            complaint["id"],
            "escalation",
            f"Auto-escalated to Level {next_level}. {escalation_message}.",
        )

        dept_user = get_department_contact(db, department, next_level)
        if dept_user:
            send_notifications(
                phone=dept_user["phone"],
                email=dept_user["email"],
                sms_message=f"Complaint {complaint['ticket_id']} has moved to level {next_level}.",
                email_subject="Complaint Escalated",
                email_message=f"Complaint {complaint['ticket_id']} has moved to level {next_level}.",
            )

    db.commit()
    db.close()


@app.route("/")
def home():
    snapshot = get_portal_snapshot()
    return render_template(
        "welcome.html",
        complaint_types=complaint_options(),
        snapshot=snapshot,
    )


@app.route("/set_language", methods=["POST"])
def set_language():
    language = request.form.get("language", "en").strip().lower()
    session["language"] = language if language in TRANSLATIONS else "en"

    next_url = request.form.get("next", "").strip()
    if next_url and next_url.startswith("/"):
        return redirect(next_url)

    referrer = request.referrer or "/"
    return redirect(referrer)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None
    dev_fallback_otp = session.get("dev_fallback_otp")

    if request.method == "GET" and request.args.get("restart") == "1":
        clear_pending_register()
        dev_fallback_otp = None

    otp_stage = "pending_register_username" in session

    if otp_stage:
        pending_expiry = session.get("pending_register_otp_expiry")
        if not pending_expiry or datetime.now() > datetime.fromisoformat(pending_expiry):
            clear_pending_register()
            otp_stage = False

    if request.method == "POST":
        action = request.form.get("action", "request_otp")

        if action == "verify_otp":
            entered_otp = request.form.get("otp", "").strip()
            pending_username = session.get("pending_register_username")
            pending_password_hash = session.get("pending_register_password_hash")
            pending_phone = session.get("pending_register_phone")
            pending_email = session.get("pending_register_email")
            pending_otp = session.get("pending_register_otp")
            pending_expiry = session.get("pending_register_otp_expiry")

            if not all([pending_username, pending_password_hash, pending_otp, pending_expiry]):
                error = "OTP session expired. Please start registration again."
                otp_stage = False
            elif datetime.now() > datetime.fromisoformat(pending_expiry):
                clear_pending_register()
                error = "OTP expired. Please request a new registration OTP."
                otp_stage = False
            elif not entered_otp.isdigit() or len(entered_otp) != 6:
                error = "Enter a valid 6-digit OTP."
                otp_stage = True
            elif entered_otp != pending_otp:
                error = "Invalid OTP. Please try again."
                otp_stage = True
            else:
                db = get_db()
                try:
                    db.execute(
                        """
                        INSERT INTO users(username, password, role, phone, email)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            pending_username,
                            pending_password_hash,
                            "user",
                            pending_phone,
                            pending_email,
                        ),
                    )
                    db.commit()
                    success = "Account created successfully. Please login to receive OTP verification."
                except sqlite3.IntegrityError:
                    error = "Username already exists. Please choose another username."
                    otp_stage = False
                finally:
                    db.close()

                clear_pending_register()
                otp_stage = False
                dev_fallback_otp = None
        else:
            clear_pending_register()
            dev_fallback_otp = None
            username = request.form["username"].strip()
            resolved_username = resolve_login_username(username)
            password = request.form["password"]
            phone = request.form["phone"].strip()
            email = request.form.get("email", "").strip()

            if len(password) < 6:
                error = "Password must be at least 6 characters."
            elif not phone and not email:
                error = "Please enter at least a phone number or an email address."
            elif phone and len(phone) < 10:
                error = "Please enter a valid phone number."
            elif email and "@" not in email:
                error = "Please enter a valid email address."
            else:
                db = get_db()
                existing = db.execute(
                    "SELECT 1 FROM users WHERE username=?",
                    (resolved_username,),
                ).fetchone()
                db.close()

                if existing:
                    seeded_usernames = {
                        info["username"]
                        for dept in DEPARTMENT_LEVEL_CONTACTS.values()
                        for info in dept.values()
                    }
                    if (
                        username in seeded_usernames
                        or username in USERNAME_ALIASES
                        or resolved_username in seeded_usernames
                    ):
                        error = "This is a department username. Please use Login instead of Register."
                    else:
                        error = "Username already exists. Please choose another username."
                else:
                    otp = f"{random.randint(100000, 999999)}"
                    sms_sent, email_sent = send_notifications(
                        phone=phone or None,
                        email=email or None,
                        sms_message=f"Your registration OTP for the complaint portal is {otp}. It is valid for 5 minutes.",
                        email_subject="Complaint Portal Registration OTP",
                        email_message=f"Your registration OTP is {otp}. It is valid for 5 minutes.",
                    )
                    if not sms_sent and not email_sent:
                        error = "We could not send the OTP right now. Please check the phone number or email and try again."
                    else:
                        dev_fallback_otp = session.get("dev_fallback_otp")
                        session["pending_register_username"] = username
                        session["pending_register_password_hash"] = generate_password_hash(password)
                        session["pending_register_phone"] = phone
                        session["pending_register_email"] = email
                        session["pending_register_otp"] = otp
                        session["pending_register_otp_expiry"] = (
                            datetime.now() + timedelta(minutes=5)
                        ).isoformat()
                        otp_stage = True
                        if dev_fallback_otp:
                            success = "SMS could not be delivered. Use the dev fallback OTP shown below to complete registration."
                        else:
                            success = "OTP sent successfully. Enter it below to complete registration."

    return render_template(
        "register.html",
        error=error,
        success=success,
        otp_stage=otp_stage,
        pending_user=session.get("pending_register_username"),
        dev_fallback_otp=dev_fallback_otp,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    success = None
    entered_username = ""
    dev_fallback_otp = session.get("dev_fallback_otp")

    if request.method == "GET" and request.args.get("restart") == "1":
        clear_pending_login()
        dev_fallback_otp = None

    otp_stage = "pending_login_user" in session

    if otp_stage:
        pending_expiry = session.get("pending_otp_expiry")
        if not pending_expiry or datetime.now() > datetime.fromisoformat(pending_expiry):
            clear_pending_login()
            otp_stage = False

    if request.method == "POST":
        action = request.form.get("action", "request_otp")

        if action == "verify_otp":
            entered_otp = request.form.get("otp", "").strip()
            pending_user = session.get("pending_login_user")
            pending_role = session.get("pending_login_role")
            pending_department = session.get("pending_login_department")
            pending_department_level = session.get("pending_department_level")
            pending_otp = session.get("pending_otp")
            pending_expiry = session.get("pending_otp_expiry")

            if not all([pending_user, pending_role, pending_otp, pending_expiry]):
                error = "OTP session expired. Please login again."
                otp_stage = False
            elif datetime.now() > datetime.fromisoformat(pending_expiry):
                clear_pending_login()
                error = "OTP expired. Please request a new OTP."
                otp_stage = False
            elif not entered_otp.isdigit() or len(entered_otp) != 6:
                error = "Enter a valid 6-digit OTP."
                otp_stage = True
            elif entered_otp != pending_otp:
                error = "Invalid OTP. Please try again."
                otp_stage = True
            else:
                session["user"] = pending_user
                session["role"] = pending_role
                if pending_department:
                    session["department"] = pending_department
                if pending_role == "department":
                    session["department_level"] = pending_department_level or 1

                clear_pending_login()
                dev_fallback_otp = None

                if pending_role == "department":
                    return redirect("/department")
                return redirect("/dashboard")

        else:
            clear_pending_login()
            dev_fallback_otp = None
            username = request.form.get("username", "").strip()
            resolved_username = resolve_login_username(username)
            password = request.form.get("password", "")
            entered_username = username

            if not username or not password:
                error = "Invalid username or password."
                otp_stage = False
                return render_template(
                    "login.html",
                    error=error,
                    otp_stage=otp_stage,
                    pending_user=session.get("pending_login_user"),
                    entered_username=entered_username,
                    dev_fallback_otp=dev_fallback_otp,
                )

            db = get_db()
            user = db.execute(
                "SELECT * FROM users WHERE username=?",
                (resolved_username,),
            ).fetchone()
            db.close()

            password_matches = False
            if user:
                try:
                    password_matches = check_password_hash(user["password"], password)
                except Exception:
                    password_matches = False

                # Fallback for stale seeded department hashes:
                # allow login when entered password matches current configured phone.
                if (
                    not password_matches
                    and user["role"] == "department"
                    and password
                ):
                    configured_phone = configured_phone_for_department_user(
                        user["username"]
                    )
                    if password in {user["phone"], configured_phone}:
                        password_matches = True
                        # Best effort self-heal of stale hash; ignore DB write issues.
                        try:
                            db_fix = get_db()
                            db_fix.execute(
                                "UPDATE users SET password=? WHERE username=?",
                                (generate_password_hash(password), user["username"]),
                            )
                            db_fix.commit()
                            db_fix.close()
                        except Exception:
                            pass

            if not user or not password_matches:
                error = "Invalid username or password."
                otp_stage = False
            elif user["role"] == "admin":
                error = "Admin login has been removed from the complaint portal."
                otp_stage = False
            elif not user["phone"] and not user["email"]:
                error = "This account does not have a phone number or email for OTP verification."
                otp_stage = False
            else:
                otp = f"{random.randint(100000, 999999)}"
                sms_sent, email_sent = send_notifications(
                    phone=user["phone"],
                    email=user["email"],
                    sms_message=f"Your complaint portal OTP is {otp}. It is valid for 5 minutes.",
                    email_subject="Complaint Portal Login OTP",
                    email_message=f"Your complaint portal login OTP is {otp}. It is valid for 5 minutes.",
                )
                if not sms_sent and not email_sent:
                    error = "We could not send the OTP right now. Please check the saved phone number or email and try again."
                    otp_stage = False
                else:
                    dev_fallback_otp = session.get("dev_fallback_otp")
                    session["pending_login_user"] = user["username"]
                    session["pending_login_role"] = user["role"]
                    session["pending_login_department"] = user["department"]
                    session["pending_department_level"] = get_department_level(
                        user["username"]
                    )
                    session["pending_otp"] = otp
                    session["pending_otp_expiry"] = (
                        datetime.now() + timedelta(minutes=5)
                    ).isoformat()
                    otp_stage = True
                    if dev_fallback_otp:
                        success = "SMS could not be delivered. Use the dev fallback OTP shown below to continue login."
                    else:
                        success = "OTP sent successfully. Enter it below to continue login."

    return render_template(
        "login.html",
        error=error,
        success=success,
        otp_stage=otp_stage,
        pending_user=session.get("pending_login_user"),
        entered_username=entered_username,
        dev_fallback_otp=dev_fallback_otp,
    )


@app.route("/dashboard", methods=["GET", "POST"])
@role_required("user")
def dashboard():
    ticket = None
    error = None
    success_message = None

    if request.method == "POST":
        complaint_type = request.form.get("complaint_type", "").strip()
        custom_complaint = request.form.get("custom_complaint", "").strip()
        complaint_text = custom_complaint if complaint_type == "Others" else complaint_type
        uploaded_photo_files = [
            file
            for file in request.files.getlist("photos")
            if file and (file.filename or "").strip()
        ]
        district = request.form.get("district", "").strip()
        mandal = request.form.get("mandal", "").strip()
        pincode = request.form.get("pincode", "").strip()
        colony = request.form.get("colony", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        address_validation = {
            "status": "Needs Review",
            "reason": "",
        }

        if not complaint_type:
            error = "Please choose a GHMC complaint category."
        elif complaint_type == "Others" and not custom_complaint:
            error = "Please type your complaint in the Others box or use voice input."
        elif not uploaded_photo_files:
            error = "Please upload at least one photo proof before submitting the complaint."

        if request.method == "POST" and not error:
            address_validation = validate_address(
                district,
                mandal,
                pincode,
                colony,
                latitude,
                longitude,
            )
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ticket = f"CMP-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"
            department = department_for_complaint(complaint_type)
            severity = request.form.get("severity", "Medium").strip() or "Medium"
            landmark = request.form.get("landmark", "").strip()
            try:
                affected_people = int(request.form.get("affected_people", "1"))
            except ValueError:
                affected_people = 1
            affected_people = max(1, min(affected_people, 5000))
            sla_deadline = (
                datetime.now() + timedelta(hours=calculate_sla_hours(severity, department, affected_people))
            ).strftime("%Y-%m-%d %H:%M:%S")

            db = get_db()
            matching_complaint = find_matching_open_complaint(
                db,
                complaint_type,
                district,
                mandal,
                pincode,
                colony,
            )

            if matching_complaint and matching_complaint["name"] == session["user"]:
                error = (
                    "You already have an open complaint for this issue at the same address. "
                    f"Please track ticket {matching_complaint['ticket_id']} instead."
                )
                ticket = matching_complaint["ticket_id"]
                db.close()
            else:
                photos = save_files(uploaded_photo_files)
                user_photos = ",".join(photos)
                preview_photo = photos[0] if photos else None
                duplicate_count = 1 if matching_complaint else 0
                complaint_status = matching_complaint["status"] if matching_complaint else "Pending"
                complaint_level = matching_complaint["level"] if matching_complaint else 1
                complaint_sla_deadline = matching_complaint["sla_deadline"] if matching_complaint else sla_deadline
                linked_ticket_id = matching_complaint["ticket_id"] if matching_complaint else None

                cursor = db.execute(
                    """
                    INSERT INTO complaints(
                        name, complaint_type, complaint, status, department,
                        severity, landmark, affected_people, sla_deadline,
                        address_district, address_mandal, address_pincode, address_colony,
                        latitude, longitude, address_validation_status, address_validation_reason,
                        ticket_id, file_name, user_photos, level, linked_ticket_id,
                        created_at, last_updated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session["user"],
                        complaint_type,
                        complaint_text,
                        complaint_status,
                        department,
                        severity,
                        landmark,
                        affected_people,
                        complaint_sla_deadline,
                        district,
                        mandal,
                        pincode,
                        colony,
                        latitude,
                        longitude,
                        address_validation["status"],
                        address_validation["reason"],
                        ticket,
                        preview_photo,
                        user_photos,
                        complaint_level,
                        linked_ticket_id,
                        now,
                        now,
                    ),
                )
                complaint_id = cursor.lastrowid

                if matching_complaint:
                    db.execute(
                        """
                        UPDATE complaints
                        SET affected_people=COALESCE(affected_people, 0) + ?, last_updated=?
                        WHERE id=?
                        """,
                        (affected_people, now, matching_complaint["id"]),
                    )
                    add_history_event(
                        db,
                        complaint_id,
                        "linked",
                        (
                            f"Complaint linked to main ticket {matching_complaint['ticket_id']} because the issue "
                            "matches an open complaint at the same address."
                        ),
                    )
                    add_history_event(
                        db,
                        matching_complaint["id"],
                        "linked",
                        (
                            f"Additional citizen report {ticket} was linked from the same address. "
                            f"Reported affected people added: {affected_people}."
                        ),
                    )
                    success_message = (
                        f"Complaint registered and linked to existing ticket {matching_complaint['ticket_id']}. "
                        f"Your tracking ticket is {ticket}."
                    )
                else:
                    add_history_event(
                        db,
                        complaint_id,
                        "created",
                        (
                            f"Complaint created with {severity.lower()} priority for {affected_people} people. "
                            f"Department assigned: {department}. "
                            f"Address check: {address_validation['status']}. "
                            f"{'Possible locality hotspot detected.' if duplicate_count else 'No similar open complaint in this locality.'}"
                        ),
                    )
                    success_message = f"Complaint registered successfully. Ticket ID: {ticket}"

                user = db.execute(
                    "SELECT phone, email FROM users WHERE username=?",
                    (session["user"],),
                ).fetchone()
                if department == "Water":
                    department_users = get_department_contacts(db, department, levels=[1, 2, 3])
                else:
                    department_users = get_department_contacts(db, department, levels=[1])
                db.commit()
                db.close()

                if user:
                    if linked_ticket_id:
                        send_notifications(
                            phone=user["phone"],
                            email=user["email"],
                            sms_message=(
                                f"Complaint {ticket} linked to existing ticket {linked_ticket_id}. "
                                f"Priority: {severity}."
                            ),
                            email_subject="Complaint Linked To Existing Issue",
                            email_message=(
                                f"Your complaint {ticket} matches an existing open issue at the same address "
                                f"and has been linked to main ticket {linked_ticket_id}. "
                                f"Priority: {severity}. Current status: {complaint_status}."
                            ),
                        )
                    else:
                        send_notifications(
                            phone=user["phone"],
                            email=user["email"],
                            sms_message=f"Complaint registered successfully. Ticket ID: {ticket}. Priority: {severity}.",
                            email_subject="Complaint Registered",
                            email_message=(
                                f"Your complaint was registered successfully. Ticket ID: {ticket}. "
                                f"Priority: {severity}. Estimated attention window ends by {sla_deadline}."
                            ),
                        )
                for department_user in department_users:
                    if linked_ticket_id:
                        send_notifications(
                            phone=department_user["phone"],
                            email=department_user["email"],
                            sms_message=(
                                f"Additional report {ticket} linked to main ticket {linked_ticket_id} "
                                f"in {department}."
                            ),
                            email_subject="Additional Complaint Linked",
                            email_message=(
                                f"A new citizen report {ticket} was linked to existing complaint "
                                f"{linked_ticket_id} in {department}. Please review the updated impact count."
                            ),
                        )
                    else:
                        send_notifications(
                            phone=department_user["phone"],
                            email=department_user["email"],
                            sms_message=f"Alert: New {department} complaint registered. Ticket ID: {ticket}.",
                            email_subject="New Complaint Alert",
                            email_message=f"A new {department} complaint has been registered and assigned to you. Ticket ID: {ticket}. Please check your department panel.",
                        )

    complaints = get_user_complaints(session["user"])
    metrics = get_user_dashboard_metrics(session["user"])
    notifications = get_notifications(session["user"])
    return render_template(
        "index.html",
        ticket=ticket,
        error=error,
        success_message=success_message,
        complaint_types=complaint_options(),
        complaints=complaints,
        metrics=metrics,
        notifications=notifications,
    )


@app.route("/department")
@role_required("department")
def department():
    department_level = session.get("department_level", 1)
    status_filter = request.args.get("status", "").strip()
    search_term = request.args.get("q", "").strip()
    context = get_department_dashboard_data(
        session.get("department"),
        department_level,
        status_filter,
        search_term,
    )
    return render_template(
        "department.html",
        error=None,
        department_level=department_level,
        **context,
    )


@app.route("/update_status", methods=["POST"])
@role_required("department")
def update_status():
    complaint_id = request.form["id"]
    new_status = request.form["status"]
    department_note = request.form.get("department_note", "").strip()
    estimated_resolution = request.form.get("estimated_resolution", "").strip()
    resolution_files = save_files(request.files.getlist("resolution_photo"))
    department_level = session.get("department_level", 1)

    db = get_db()
    complaint = db.execute(
        "SELECT * FROM complaints WHERE id=? AND department=? AND level=?",
        (complaint_id, session.get("department"), department_level),
    ).fetchone()

    if not complaint:
        db.close()
        abort(404)

    current_level = complaint["level"] or 1
    group_ticket_id = complaint["linked_ticket_id"] or complaint["ticket_id"]
    level_column = LEVEL_PHOTO_COLUMNS.get(current_level, "level3_photo")
    update_photo = resolution_files[0] if resolution_files else complaint[level_column]

    if new_status in ("Resolved", "Closed") and not update_photo:
        db.close()
        context = get_department_dashboard_data(
            session.get("department"),
            department_level,
        )
        return render_template(
            "department.html",
            error="Please upload a photo proof before marking the complaint resolved or closed.",
            department_level=department_level,
            **context,
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        f"""
        UPDATE complaints
        SET status=?, last_updated=?, department_note=?, estimated_resolution=?, {level_column}=?
        WHERE ticket_id=? OR linked_ticket_id=?
        """,
        (new_status, now, department_note, estimated_resolution, update_photo, group_ticket_id, group_ticket_id),
    )

    rows = db.execute(
        """
        SELECT id, name, ticket_id, department, status, severity
        FROM complaints
        WHERE ticket_id=? OR linked_ticket_id=?
        ORDER BY id ASC
        """,
        (group_ticket_id, group_ticket_id),
    ).fetchall()
    for row in rows:
        add_history_event(
            db,
            row["id"],
            "status",
            (
                f"Department updated complaint to {new_status} at Level {department_level}. Priority: {row['severity']}."
                f"{f' Note: {department_note}' if department_note else ''}"
                f"{f' ETA: {estimated_resolution}' if estimated_resolution else ''}"
                f"{' Synced from linked complaint group.' if row['ticket_id'] != group_ticket_id else ''}"
            ),
        )
    users = []
    for row in rows:
        user = db.execute(
            "SELECT phone, email FROM users WHERE username=?",
            (row["name"],),
        ).fetchone()
        users.append((row, user))
    db.commit()
    db.close()

    for row, user in users:
        if not user:
            continue
        attachments = None
        if new_status in ("Resolved", "Closed") and update_photo:
            attachments = [os.path.join(UPLOAD_FOLDER, update_photo)]
        status_message = (
            f"Complaint {row['ticket_id']} in {row['department']} was updated to {new_status}."
        )
        send_notifications(
            phone=user["phone"],
            email=user["email"],
            sms_message=status_message,
            email_subject="Complaint Status Updated",
            email_message=(
                f"Complaint {row['ticket_id']} in {row['department']} was updated to {new_status}. "
                f"{f' Department note: {department_note}. ' if department_note else ''}"
                f"{f'Expected resolution: {estimated_resolution}. ' if estimated_resolution else ''}"
                "Please find the photo proof attached."
            ),
            attachments=attachments
        )
        create_notification(row["name"], status_message)

    return redirect("/department")


@app.route("/department/remove_complaint", methods=["POST"])
@role_required("department")
def remove_department_complaint():
    complaint_id = request.form.get("id", "").strip()
    department_level = session.get("department_level", 1)

    db = get_db()
    complaint = db.execute(
        """
        SELECT * FROM complaints
        WHERE id=? AND department=? AND level=?
        """,
        (complaint_id, session.get("department"), department_level),
    ).fetchone()

    if not complaint:
        db.close()
        abort(404)

    db.execute("DELETE FROM complaint_history WHERE complaint_id=?", (complaint_id,))
    db.execute("DELETE FROM complaints WHERE id=?", (complaint_id,))
    db.commit()
    db.close()

    create_notification(
        complaint["name"],
        f"Complaint {complaint['ticket_id']} was removed by the {complaint['department']} department.",
    )
    return redirect("/department")


@app.route("/submit_feedback", methods=["POST"])
@role_required("user")
def submit_feedback():
    complaint_id = request.form.get("id", "").strip()
    action = request.form.get("action", "feedback")
    feedback_comment = request.form.get("feedback_comment", "").strip()
    rating_raw = request.form.get("feedback_rating", "").strip()

    db = get_db()
    complaint = db.execute(
        "SELECT * FROM complaints WHERE id=? AND name=?",
        (complaint_id, session["user"]),
    ).fetchone()

    if not complaint:
        db.close()
        abort(404)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action == "reopen":
        if (complaint["reopened_count"] or 0) >= 1:
            db.close()
            return redirect(f"/track?ticket_id={complaint['ticket_id']}")

        db.execute(
            """
            UPDATE complaints
            SET status='Reopened', reopened_count=?, feedback_comment=?, last_updated=?
            WHERE id=?
            """,
            (
                (complaint["reopened_count"] or 0) + 1,
                feedback_comment or "Citizen marked the issue as unresolved after closure.",
                now,
                complaint_id,
            ),
        )
        add_history_event(
            db,
            complaint_id,
            "reopened",
            feedback_comment or "Citizen reopened the complaint because the issue persists.",
        )
        department_users = get_department_contacts(
            db,
            complaint["department"],
            levels=[complaint["level"] or 1],
        )
    else:
        department_users = []
        rating = None
        if rating_raw.isdigit():
            rating = max(1, min(int(rating_raw), 5))

        db.execute(
            """
            UPDATE complaints
            SET feedback_rating=?, feedback_comment=?, last_updated=?
            WHERE id=?
            """,
            (rating, feedback_comment, now, complaint_id),
        )
        add_history_event(
            db,
            complaint_id,
            "feedback",
            (
                f"Citizen submitted feedback"
                f"{f' with rating {rating}/5' if rating else ''}."
                f"{f' Comment: {feedback_comment}' if feedback_comment else ''}"
            ),
        )

    db.commit()
    db.close()

    for department_user in department_users:
        send_notifications(
            phone=department_user["phone"],
            email=department_user["email"],
            sms_message=f"Complaint {complaint['ticket_id']} has been reopened by the citizen.",
            email_subject="Complaint Reopened",
            email_message=(
                f"Complaint {complaint['ticket_id']} has been reopened by the citizen. "
                "Please review the latest comment in the department panel."
            ),
        )
    return redirect(f"/track?ticket_id={complaint['ticket_id']}")


@app.route("/track", methods=["GET", "POST"])
def track():
    complaint = None
    error = None
    ticket_id = request.form.get("ticket_id", "").strip()

    if request.method == "GET":
        ticket_id = request.args.get("ticket_id", "").strip()

    if ticket_id:
        db = get_db()
        complaint_row = db.execute(
            "SELECT * FROM complaints WHERE ticket_id=?",
            (ticket_id,),
        ).fetchone()
        db.close()
        if not complaint_row:
            error = "No complaint found for that ticket ID."
        else:
            complaint = serialize_complaint(complaint_row)

    history = get_complaint_history(complaint["id"]) if complaint else []
    return render_template("track.html", complaint=complaint, error=error, history=history)


@app.route("/api/my_complaints")
@role_required("user")
def my_complaints_api():
    complaints = get_user_complaints(session["user"])
    metrics = get_user_dashboard_metrics(session["user"])
    notifications = get_notifications(session["user"])
    return jsonify(
        {
            "complaints": [serialize_complaint(row) for row in complaints],
            "metrics": {
                "total_count": metrics["total_count"] or 0,
                "open_count": metrics["open_count"] or 0,
                "overdue_count": metrics["overdue_count"] or 0,
                "positive_feedback_count": metrics["positive_feedback_count"] or 0,
            },
            "notifications": [
                {
                    "message": row["message"],
                    "time": row["time"],
                }
                for row in notifications
            ],
        }
    )


@app.route("/api/complaint/<ticket_id>")
def complaint_api(ticket_id):
    db = get_db()
    complaint = db.execute(
        "SELECT * FROM complaints WHERE ticket_id=?",
        (ticket_id.strip(),),
    ).fetchone()
    db.close()

    if not complaint:
        return jsonify({"error": "Complaint not found."}), 404

    return jsonify(
        {
            "complaint": serialize_complaint(complaint),
            "history": [
                {
                    "event_type": row["event_type"],
                    "message": row["message"],
                    "created_at": row["created_at"],
                }
                for row in get_complaint_history(complaint["id"])
            ],
        }
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


scheduler = None
runtime_initialized = False


def initialize_runtime():
    global scheduler, runtime_initialized

    if runtime_initialized:
        return

    migrate_database()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=auto_escalation, trigger="interval", minutes=5)
    scheduler.start()
    runtime_initialized = True


if __name__ == "__main__":
    debug_mode = True
    if not debug_mode or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        initialize_runtime()
    app.run(debug=debug_mode)
