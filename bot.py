import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config import MESSAGE_TEXT
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import (
    MESSAGE_TEXT,
    EMAIL_SENDER,
    EMAIL_RECEIVER,
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL_SUBJECT
)
import os
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# ==============================
# TEMP CONFIG (dummy for now)
# ==============================
LINKEDIN_EMAIL = "mohankrishna9217@gmail.com"
LINKEDIN_PASSWORD = "Mohankrishna@2429"
EMAIL_PASSWORD = "qshk cfvp rjlb dgpb"


CONNECTIONS_FILE = "connections.json"

# ==============================
# SETUP BROWSER
# ==============================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")


service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# ==============================
# LOGIN
# ==============================
def login():
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    time.sleep(5)
    print("✅ Logged into LinkedIn")

# ==============================
# READ CURRENT CONNECTIONS
# ==============================
def read_connections():
    driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
    time.sleep(5)

    profiles = set()
    links = driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")

    for link in links:
        url = link.get_attribute("href")
        if url:
            profiles.add(url.split("?")[0])

    return profiles


# ==============================
# LOAD / SAVE CONNECTIONS
# ==============================
def load_saved_connections():
    try:
        with open(CONNECTIONS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_connections(connections):
    with open(CONNECTIONS_FILE, "w") as f:
        json.dump(list(connections), f, indent=2)

def send_email_notification(profile_url):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = EMAIL_SUBJECT

        body = f"""
A LinkedIn message was successfully sent.

Profile URL:
{profile_url}

Time:
{time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("📧 Email notification sent")

    except Exception as e:
        print("⚠️ Email notification failed:", e)

# ==============================
# SEND MESSAGE
# ==============================
def send_message(profile_url):
    driver.get(profile_url)
    time.sleep(4)

    try:
        # Try direct Message button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        message_button = None

        for btn in buttons:
            if btn.text.strip().lower() == "message":
                message_button = btn
                break

        # If not found, try "More" → Message
        if not message_button:
            for btn in buttons:
                if btn.text.strip().lower() == "more":
                    btn.click()
                    time.sleep(2)
                    break

            options = driver.find_elements(By.XPATH, "//span[text()='Message']")
            if options:
                options[0].click()
                time.sleep(2)
            else:
                raise Exception("Message option not available")

        else:
            message_button.click()
            time.sleep(2)

        textbox = driver.find_element(
            By.XPATH, "//div[contains(@class,'msg-form__contenteditable')]"
        )
        textbox.send_keys(MESSAGE_TEXT)
        time.sleep(1)

        send_btn = driver.find_element(
            By.XPATH, "//button[contains(@class,'msg-form__send-button')]"
        )
        send_btn.click()

        print("📨 Message sent →", profile_url)
        send_email_notification(profile_url)
        time.sleep(3)

    except Exception as e:
        print("⚠️ Could not message:", profile_url)

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    login()

    current_connections = read_connections()
    saved_connections = load_saved_connections()

    new_connections = current_connections - saved_connections
    print(f"🆕 New connections to message: {len(new_connections)}")

    for profile in new_connections:
        send_message(profile)

    updated_connections = saved_connections | current_connections
    save_connections(updated_connections)

    driver.quit()
