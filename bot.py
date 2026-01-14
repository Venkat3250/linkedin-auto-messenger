import os
import time
import json
import random
import smtplib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import (
    MESSAGE_TEXT,
    EMAIL_SENDER,
    EMAIL_RECEIVER,
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL_SUBJECT,
)

# ================= ENVIRONMENT VARIABLES =================
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not all([LINKEDIN_EMAIL, LINKEDIN_PASSWORD, EMAIL_PASSWORD]):
    raise EnvironmentError("Missing required environment variables")

# ================= FILES =================
CONNECTIONS_FILE = "connections.json"
MESSAGED_FILE = "messaged.json"

# ================= SELENIUM SETUP =================
options = Options()
# Headless disabled for safety
# options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# ================= UTILS =================
def human_delay(a=8, b=15):
    time.sleep(random.randint(a, b))

def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return set(json.load(f))
    return set()

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(list(data), f, indent=2)

# ================= EMAIL =================
def send_email_notification(count):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = EMAIL_SUBJECT

    body = f"LinkedIn bot successfully sent {count} messages."
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

# ================= LINKEDIN LOGIC =================
def login():
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)

    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    time.sleep(6)
    if "feed" not in driver.current_url:
        raise RuntimeError("Login failed (possible CAPTCHA or verification)")

def read_connections():
    driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
    time.sleep(6)

    links = driver.find_elements(By.XPATH, "//a[@data-control-name='connection_profile']")
    profiles = set()

    for l in links:
        href = l.get_attribute("href")
        if href and "/in/" in href:
            profiles.add(href.split("?")[0])

    return profiles

def send_message(profile_url):
    try:
        driver.get(profile_url)
        time.sleep(6)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        msg_button = next(b for b in buttons if b.text.strip() == "Message")
        msg_button.click()

        time.sleep(3)

        box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
        box.send_keys(MESSAGE_TEXT)

        send_btn = driver.find_element(By.XPATH, "//button[contains(@class,'msg-form__send-button')]")
        send_btn.click()

        return True
    except Exception as e:
        print(f"[ERROR] {profile_url}: {e}")
        return False

# ================= MAIN =================
if _name_ == "_main_":
    sent_count = 0

    try:
        login()

        current_connections = read_connections()
        saved_connections = load_json(CONNECTIONS_FILE)
        messaged_profiles = load_json(MESSAGED_FILE)

        new_connections = current_connections - saved_connections

        for profile in new_connections:
            if profile not in messaged_profiles:
                success = send_message(profile)
                if success:
                    messaged_profiles.add(profile)
                    sent_count += 1
                    human_delay(12, 20)

        save_json(CONNECTIONS_FILE, current_connections)
        save_json(MESSAGED_FILE, messaged_profiles)

        if sent_count > 0:
            send_email_notification(sent_count)

    finally:
        driver.quit()
