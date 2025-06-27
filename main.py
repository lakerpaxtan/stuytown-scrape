"""
StuyTown Apartment Scraper
Monitors StuyTown website for new apartment listings and sends email notifications.
"""
import argparse
import json
import logging
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from config import SMTP_SERVER, SMTP_PORT, EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO
except ImportError:
    print("ERROR: config.py not found!")
    print("Please copy config.example.py to config.py and update with your email settings")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Configuration
STUYTOWN_URL = "https://www.stuytown.com/nyc-apartments-for-rent/?Order=low-price&Bedrooms=1-2"
APARTMENTS_FILE = "apartments.json"
CHECK_INTERVAL = 30  # seconds


class StuyTownScraper:
    def __init__(self):
        self.apartments_file = Path(APARTMENTS_FILE)
        self.known_apartments = self.load_existing_apartments()
        self.driver = None
        
    def load_existing_apartments(self) -> Dict[str, Dict]:
        """Load existing apartments from JSON file."""
        if self.apartments_file.exists():
            try:
                with open(self.apartments_file, 'r') as f:
                    data = json.load(f)
                LOGGER.info(f"Loaded {len(data)} existing apartments from {APARTMENTS_FILE}")
                return data
            except Exception as e:
                LOGGER.error(f"Error loading apartments file: {e}")
                return {}
        else:
            LOGGER.info(f"No existing apartments file found, starting fresh")
            return {}
    
    def save_apartments(self, apartments: Dict[str, Dict]):
        """Save apartments to JSON file."""
        try:
            with open(self.apartments_file, 'w') as f:
                json.dump(apartments, f, indent=2)
            LOGGER.info(f"Saved {len(apartments)} apartments to {APARTMENTS_FILE}")
        except Exception as e:
            LOGGER.error(f"Error saving apartments: {e}")
    
    def setup_driver(self):
        """Setup Chrome driver with options."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            LOGGER.info("Chrome driver initialized successfully")
        except Exception as e:
            LOGGER.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def scroll_to_load_all(self):
        """Scroll down to load all apartment listings."""
        LOGGER.info("Starting to scroll to load all apartments")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        
        while True:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scroll_count += 1
            
            # Wait for new content to load
            time.sleep(2)
            
            # Calculate new scroll height and compare with last height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            LOGGER.info(f"Scroll {scroll_count}: height {last_height} -> {new_height}")
            
            if new_height == last_height:
                LOGGER.info("No more content to load, scrolling complete")
                break
                
            last_height = new_height
            
            # Safety check - don't scroll forever
            if scroll_count > 50:
                LOGGER.warning("Reached maximum scroll attempts")
                break
    
    def extract_apartments(self) -> List[Dict]:
        """Extract apartment data from the page."""
        apartments = []
        
        try:
            # Wait for listings to load - look for apartment containers
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".bG_cM"))
            )
            
            # Find apartment container elements
            apartment_containers = self.driver.find_elements(By.CSS_SELECTOR, ".bG_cM")
            
            LOGGER.info(f"Found {len(apartment_containers)} apartment containers")
            
            for container in apartment_containers:
                try:
                    # Extract data using specific CSS classes
                    # Bedrooms/bath info
                    try:
                        bedrooms_elem = container.find_element(By.CSS_SELECTOR, ".bG_2")
                        bedrooms = bedrooms_elem.get_attribute('textContent')
                    except Exception as e:
                        LOGGER.warning(f"Could not find bedrooms element: {e}")
                        bedrooms = "Unknown"
                    
                    # Address (full address including apartment number) - REQUIRED
                    try:
                        address_elem = container.find_element(By.CSS_SELECTOR, ".bG_cQ")
                        address = address_elem.get_attribute('textContent')
                    except Exception as e:
                        LOGGER.warning(f"Could not find address element: {e}")
                        address = ""
                    
                    # Availability 
                    try:
                        availability_elem = container.find_element(By.CSS_SELECTOR, ".bG_bz")
                        availability = availability_elem.get_attribute('textContent')
                    except Exception as e:
                        LOGGER.warning(f"Could not find availability element: {e}")
                        availability = "Unknown"
                    
                    # Price - REQUIRED
                    try:
                        price_elem = container.find_element(By.CSS_SELECTOR, ".bG_jY")
                        price = price_elem.get_attribute('textContent')
                    except Exception as e:
                        LOGGER.warning(f"Could not find price element: {e}")
                        price = ""
                    
                    # Unit URL
                    try:
                        url_elem = container.find_element(By.CSS_SELECTOR, ".bG_ct")
                        unit_url = url_elem.get_attribute('href')
                        if unit_url and not unit_url.startswith('http'):
                            unit_url = "https://www.stuytown.com" + unit_url
                    except Exception as e:
                        LOGGER.warning(f"Could not find unit URL: {e}")
                        unit_url = STUYTOWN_URL
                    
                    # Validate required fields
                    if not address or not price:
                        LOGGER.warning(f"Skipping apartment due to missing required data - Address: '{address}', Price: '{price}'")
                        continue
                    
                    apartment = {
                        "address": address,
                        "price": price,
                        "bedrooms": bedrooms,
                        "availability": availability,
                        "discovered_at": datetime.now().isoformat(),
                        "url": unit_url
                    }
                    
                    apartments.append(apartment)
                    LOGGER.info(f"Extracted apartment: {address} - {price}")
                    
                except Exception as e:
                    LOGGER.warning(f"Error extracting apartment data from container: {e}")
                    continue
            
        except Exception as e:
            LOGGER.error(f"Error finding apartment containers: {e}")
        
        LOGGER.info(f"Successfully extracted {len(apartments)} apartments")
        return apartments
    
    def send_email_notification(self, new_apartments: List[Dict] = None, test_mode: bool = False):
        """Send email notification for new apartments or test email."""
        if not new_apartments and not test_mode:
            return
            
        try:
            if test_mode:
                subject = "🧪 StuyTown Scraper Test Email"
                body = "This is a test email from your StuyTown apartment scraper.\n\nIf you received this, email notifications are working correctly!"
            else:
                subject = f"🏠 {len(new_apartments)} New StuyTown Apartment(s) Found!"
                body = "New apartments available at StuyTown:\n\n"
                for apt in new_apartments:
                    body += f"📍 {apt['address']}\n"
                    body += f"💰 {apt['price']}\n"
                    body += f"🛏️ {apt['bedrooms']}\n"
                    body += f"🕐 Discovered: {apt['discovered_at']}\n"
                    body += f"🔗 {apt['url']}\n\n"
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = EMAIL_FROM
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_FROM, EMAIL_PASSWORD)
                
                server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
                LOGGER.info(f"Email sent to {EMAIL_TO}")
            
            if test_mode:
                LOGGER.info(f"Test email sent to {len(EMAIL_TO)} recipients")
            else:
                LOGGER.info(f"Email notification sent for {len(new_apartments)} new apartments to {len(EMAIL_TO)} recipients")
            
        except Exception as e:
            LOGGER.error(f"Error sending email notification: {e}")
    
    def check_for_new_apartments(self):
        """Check for new apartments and update known listings."""
        LOGGER.info("Starting apartment check")
        
        try:
            # Load the page
            self.driver.get(STUYTOWN_URL)
            LOGGER.info(f"Loaded page: {STUYTOWN_URL}")
            
            # Scroll to load all apartments
            self.scroll_to_load_all()
            
            # Extract apartments
            current_apartments = self.extract_apartments()
            
            if not current_apartments:
                LOGGER.warning("No apartments found - check selectors")
                return
            
            # Check for new apartments
            new_apartments = []
            updated_apartments = {}
            
            for apt in current_apartments:
                address = apt['address']
                updated_apartments[address] = apt
                
                if address not in self.known_apartments:
                    new_apartments.append(apt)
                    LOGGER.info(f"New apartment found: {address} - {apt['price']}")
            
            # Update known apartments
            self.known_apartments = updated_apartments
            self.save_apartments(self.known_apartments)
            
            # Send notifications for new apartments
            if new_apartments:
                LOGGER.info(f"Found {len(new_apartments)} new apartments!")
                self.send_email_notification(new_apartments)
            else:
                LOGGER.info("No new apartments found")
                
        except Exception as e:
            LOGGER.error(f"Error during apartment check: {e}")
    
    def save_initial_apartments(self):
        """Save apartments without checking for new ones - for initial setup."""
        LOGGER.info("Saving initial apartments (no notifications)")
        
        try:
            self.setup_driver()
            
            # Load the page
            self.driver.get(STUYTOWN_URL)
            LOGGER.info(f"Loaded page: {STUYTOWN_URL}")
            
            # Scroll to load all apartments
            self.scroll_to_load_all()
            
            # Extract apartments
            current_apartments = self.extract_apartments()
            
            if not current_apartments:
                LOGGER.warning("No apartments found - check selectors")
                return
            
            # Save all apartments as known
            apartments_dict = {apt['address']: apt for apt in current_apartments}
            self.known_apartments = apartments_dict
            self.save_apartments(self.known_apartments)
            
            LOGGER.info(f"Saved {len(current_apartments)} apartments as initial baseline")
                
        except Exception as e:
            LOGGER.error(f"Error during initial apartment save: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                LOGGER.info("Driver closed")
    
    def test_email(self):
        """Send a test email to verify email configuration."""
        LOGGER.info("Sending test email")
        self.send_email_notification(test_mode=True)
    
    def run(self):
        """Main monitoring loop."""
        LOGGER.info("Starting StuyTown apartment scraper")
        
        try:
            self.setup_driver()
            
            while True:
                self.check_for_new_apartments()
                LOGGER.info(f"Waiting {CHECK_INTERVAL} seconds before next check..... time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            LOGGER.info("Scraper stopped by user")
        except Exception as e:
            LOGGER.error(f"Critical error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                LOGGER.info("Driver closed")


def main():
    parser = argparse.ArgumentParser(description='StuyTown Apartment Scraper')
    parser.add_argument('--save-apartments', action='store_true', 
                        help='Save current apartments without checking for new ones (initial setup)')
    parser.add_argument('--test-email', action='store_true',
                        help='Send a test email to verify email configuration')
    
    args = parser.parse_args()
    
    scraper = StuyTownScraper()
    
    if args.save_apartments:
        scraper.save_initial_apartments()
    elif args.test_email:
        scraper.test_email()
    else:
        scraper.run()


if __name__ == "__main__":
    main()