import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config import MESSAGE_TEXT, EMAIL_SENDER, EMAIL_RECEIVER, SMTP_SERVER, SMTP_PORT, EMAIL_SUBJECT
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

CONNECTIONS_FILE = "connections.json"
MESSAGED_FILE = "messaged.json"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def login():
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)
    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(5)

def read_connections():
    driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
    time.sleep(5)
    links = driver.find_elements(By.XPATH, "//a[contains(@href,'/in/')]")
    return {l.get_attribute("href").split("?")[0] for l in links if l.get_attribute("href")}

def load_json(file):
    if os.path.exists(file):
        return set(json.load(open(file)))
    return set()

def save_json(file, data):
    json.dump(list(data), open(file, "w"), indent=2)

def send_message(profile):
    try:
        driver.get(profile)
        time.sleep(4)
        driver.find_element(By.XPATH, "//button[.//span[text()='Message']]").click()
        time.sleep(2)
        box = driver.find_element(By.XPATH, "//div[contains(@class,'msg-form__contenteditable')]")
        box.send_keys(MESSAGE_TEXT)
        driver.find_element(By.XPATH, "//button[contains(@class,'msg-form__send-button')]").click()
        return True
    except:
        return False

if _name_ == "_main_":
    login()
    current = read_connections()
    saved = load_json(CONNECTIONS_FILE)
    messaged = load_json(MESSAGED_FILE)

    new = current - saved
    for p in new:
        if p not in messaged and send_message(p):
            messaged.add(p)

    save_json(CONNECTIONS_FILE, current)
    save_json(MESSAGED_FILE, messaged)
    driver.quit()
