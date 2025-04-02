import requests
import time
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Command(BaseCommand):
    help = 'Fetch open projects from Planhub API'

    def handle(self, *args, **options):

        # Set up headless Chrome
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)

        project_url = "https://supplier.planhub.com/project/429642"
        driver.get(project_url)

        # Wait for the JavaScript to load the content inside <planhub-main>
        time.sleep(5)  # Adjust the sleep time as needed

        # Get the rendered HTML and parse it with BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Access the <planhub-main> element
        planhub_main = soup.find('planhub-main')
        if planhub_main:
            print(planhub_main.text)
        else:
            print("Could not find the <planhub-main> element.")

        driver.quit()
