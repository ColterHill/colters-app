import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class PlanhubLogin:
    def __init__(self, headless=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.wait = WebDriverWait(self.driver, 20)
        self.auth_token = None

    def login(self, url, username, password):
        self.driver.get(url)

        self.wait.until(EC.presence_of_element_located((By.ID, "mat-input-0"))).send_keys(username)
        password_field = self.wait.until(EC.presence_of_element_located((By.ID, "mat-input-1")))
        password_field.send_keys(password)
        password_field.send_keys(Keys.ENTER)

        self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[span//span[text()='Subcontractors']]")))

        # Click the Subcontractors button
        subcontractors_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[span//span[text()='Subcontractors']]")))
        subcontractors_button.click()

        # Extract Authorization token from network logs
        self.auth_token = self.get_auth_header()
        if not self.auth_token:
            raise ValueError("Auth token not found in network requests.")

        # Save token to a file
        self.cache_auth_token()

    def get_auth_header(self):
        """Extract Authorization header from network logs."""
        logs = self.driver.get_log("performance")
        for entry in logs:
            log_message = json.loads(entry["message"])["message"]
            if log_message.get("method") == "Network.requestWillBeSent":
                request_params = log_message.get("params", {})
                request_data = request_params.get("request", {})
                headers = request_data.get("headers", {})
                auth_header = headers.get("Authorization")
                if auth_header and auth_header != "auth_token undefined":
                    return auth_header
        return None

    def cache_auth_token(self):
        """Save the Authorization token to a JSON file."""
        with open("auth_token.json", "w") as f:
            json.dump({"auth_token": self.auth_token}, f)
        print("Auth token saved to auth_token.json")

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    URL = os.getenv("PLANHUB_URL")
    USERNAME = os.getenv("PLANHUB_USERNAME")
    PASSWORD = os.getenv("PLANHUB_PASSWORD")

    login_manager = PlanhubLogin(headless=False)

    try:
        login_manager.login(URL, USERNAME, PASSWORD)
    finally:
        login_manager.close()

