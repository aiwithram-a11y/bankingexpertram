#!/usr/bin/env python3
"""
daily_script.py
Generate script.md for the day from the content calendar.
Usage: python3 daily_script.py
Prompts for date (ddmmyyyy) → looks up topic → generates script.md via Abacus.AI
"""
import sys
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).parent

# Content calendar: ddmmyyyy → (category, title, hook)
CALENDAR = {
    "19052026": ("Cybersecurity",   "₹52,000 Crore Cyber Fraud — India Ka Sabse Bada Digital Loot",           "Fresh DoT data — UPI, digital arrest, OTP, phishing covered in one video"),
    "20052026": ("Banking rights",  "ATM Se Paisa Gaya — Chargeback Kaise Karein",                             "RBI rules, 1930 helpline, reversal timeline explained"),
    "21052026": ("Govt schemes",    "Aadhaar Update — Fake Agents Se Kaise Bachein",                           "UIDAI official process + fake agent cyber scam angle"),
    "22052026": ("Digital tools",   "DigiLocker — Driving Licence Se Degree Tak, Sab Digital",                 "Setup walkthrough, supported documents list"),
    "23052026": ("Consumer rights", "Amazon/Flipkart Refund Nahin Mila — Consumer Court Tak Kaise Jaayein",   "Escalation ladder: seller → platform → consumer forum"),
    "24052026": ("Cybersecurity",   "Digital Arrest Scam — Asli Police Kabhi Phone Nahin Karti",               "Psychological warfare angle, Prof. Triveni Singh warning"),
    "25052026": ("Banking rights",  "Banking Ombudsman — Bank Ke Against Complaint Kaise Karein",              "RBI grievance portal step-by-step walkthrough"),
    "26052026": ("Govt schemes",    "Sanchar Saathi — Khoya Phone Ghar Baithe Block Aur Dhundhein",            "IMEI blocking, CEIR portal walkthrough"),
    "27052026": ("Cybersecurity",   "UPI Fraud Ho Gaya — Paise Wapas Kaise Milenge",                           "NPCI dispute, bank complaint, 24-hour golden window"),
    "28052026": ("Digital tools",   "UMANG App — 100 Government Services Ek Jagah",                           "PF balance, Aadhaar, DigiLocker, Ayushman — all in one demo"),
    "29052026": ("Consumer rights", "Insurance Claim Reject Hua — IRDAI Bima Bharosa Se Kaise Ladein",        "Online complaint portal, escalation to ombudsman"),
    "30052026": ("Cybersecurity",   "Deepfake Voice Scam — Aapke Ghar Walon Ki Awaaz Clone Ho Sakti Hai",     "AI voice cloning fraud cases, verification tips"),
    "31052026": ("Govt schemes",    "EPF/PF Withdrawal — Online Kaise Karein, Common Errors Fix Karein",       "EPFO portal, UAN activation, rejection reasons"),
    "01062026": ("Banking rights",  "Loan Recovery Agents Harassment — RBI Ke Rules Kya Kehte Hain",           "What banks legally cannot do, where to complain"),
    "02062026": ("Cybersecurity",   "Fake Trading App Scam — ₹100 Crore Fraud Ka Parda Faash",                "Real case, WhatsApp group lure, red flags to spot"),
    "03062026": ("Govt schemes",    "Passport Apply/Renew Ghar Baithe — DigiSeva Se Appointment Kaise Lein",  "Step-by-step, documents needed, common mistakes"),
    "04062026": ("Consumer rights", "Railway Ticket Refund — TDR Kaise File Karein IRCTC Par",                "Sister video to viral lost baggage video — same audience"),
    "05062026": ("Cybersecurity",   "OTP Fraud — Yeh 6 Situations Mein Kabhi Share Mat Karna",                "Fake bank, fake courier, fake KYC, SIM swap scenarios"),
    "06062026": ("Govt schemes",    "PM Kisan Status Check — Aur Fake PM Kisan Sites Se Kaise Bachein",       "Phishing sites mimicking govt portals — dual niche hit"),
    "07062026": ("Banking rights",  "Bank Ne Wrong Charge Kaata — Step-by-Step Complaint Guide",              "Processing fee, EMI bounce charge, SMS charge reversal"),
    "08062026": ("Cybersecurity",   "WhatsApp Scam — 16.97 Lakh Accounts Band Kyun Kiye Sarkar Ne",           "DoT crackdown data, what to check in your own chats"),
    "09062026": ("Consumer rights", "Consumer Forum — ₹500 Mein Court Jaana, Process Kya Hai",               "E-daakhil portal, filing fee, qualifying cases explained"),
    "10062026": ("Govt schemes",    "Ayushman Bharat — Fake Hospitals Ki List Aur Asli Check Karne Ka Tarika","NHA portal verification + hospital fraud scam angle"),
    "11062026": ("Cybersecurity",   "SIM Swap Fraud — Aapka Number Haijack Ho Sakta Hai",                     "How it works, telecom complaint, Sanchar Saathi protection"),
    "12062026": ("Consumer rights", "Flight Delay Compensation — DGCA Rules Jo Airlines Nahin Batate",        "What you're legally owed, AirSewa complaint portal"),
    "13062026": ("Cybersecurity",   "Mule Account Scam — Teenagers Ko Kaise Faansa Ja Raha Hai",              "Delhi bust case, what parents must tell their children"),
    "14062026": ("Banking rights",  "CIBIL Score Gira Hua Hai — Free Mein Kaise Theek Karein",                "Dispute process, RBI free credit report entitlement"),
    "15062026": ("Cybersecurity",   "Fake Customer Care Numbers — Google Par Dhundna Kab Khatarnak Hai",      "SEO poisoning, how fraudsters rank fake helpline numbers"),
    "16062026": ("Banking rights",  "EPF Pension — Nominee Update Online Kaise Karein",                       "Very high search, often neglected — step-by-step EPFO guide"),
    "17062026": ("Govt schemes",    "Telecom Act 2024 — Biometric SIM Rule Aapko Kaise Affect Karega",        "New law explainer, 3-year jail for fake SIM"),
}


def get_api_key() -> str:
    key_file = BASE / ".abacus_key"
    if not key_file.exists():
        raise FileNotFoundError(".abacus_key not found in project folder")
    return key_file.read_text().strip()


def build_topic_string(category: str, title: str, hook: str) -> str:
    return f"[Category: {category}]\nTitle: {title}\nAngle/Hook: {hook}"


def generate_script(topic: str, api_key: str) -> str:
    result = subprocess.run(
        [sys.executable, str(BASE / "abacus_script_gen.py"), topic, api_key],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0 and not result.stdout:
        raise RuntimeError(result.stderr or "Script generation failed")
    data = json.loads(result.stdout)
    if not data.get("success"):
        raise RuntimeError(data.get("error", "Unknown error from Abacus.AI"))
    return data["script"]


def format_date(date_str: str) -> str:
    return f"{date_str[:2]}.{date_str[2:4]}.{date_str[4:]}"


def main():
    date_str = input("Enter date (ddmmyyyy): ").strip()

    if len(date_str) != 8 or not date_str.isdigit():
        print("Invalid format. Use ddmmyyyy — e.g. 19052026")
        sys.exit(1)

    entry = CALENDAR.get(date_str)
    if not entry:
        print(f"No content scheduled for {format_date(date_str)}")
        sys.exit(1)

    category, title, hook = entry
    print(f"\nDate:     {format_date(date_str)}")
    print(f"Category: {category}")
    print(f"Title:    {title}")
    print(f"Hook:     {hook}")
    print("\nGenerating script via Abacus.AI...\n")

    try:
        api_key = get_api_key()
        topic = build_topic_string(category, title, hook)
        script = generate_script(topic, api_key)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    script_path = BASE / "script.md"
    script_path.write_text(script, encoding="utf-8")

    print("=" * 60)
    print(script)
    print("=" * 60)
    print(f"\nSaved to script.md")


if __name__ == "__main__":
    main()
