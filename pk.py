import json
import time
import logging
import os  # To use environment variables
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv  # To load environment variables from .env file

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables from .env file
load_dotenv()

# Facebook Group URL from environment variable
GROUP_URL = os.getenv("FACEBOOK_GROUP_URL")

# Function to setup WebDriver
def setup_driver():
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
    options.add_argument("--headless")  # Running in detached mode, so no UI needed

    # Chrome user data directory from environment variable
    chrome_user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
    options.add_argument(f"--user-data-dir={chrome_user_data_dir}")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def load_cookies(driver, cookie_file="fb_cookies.json"):
    """Loads cookies from a manually exported JSON file."""
    try:
        with open(cookie_file, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        logging.info("[+] Cookies loaded successfully.")
    except FileNotFoundError:
        print("[-] Cookie file not found.")
    except json.JSONDecodeError:
        print("[-] Error parsing the cookie file.")
    except Exception as e:
        print(f"[-] Unexpected error: {e}")

def access_group(driver):
    """Opens the Facebook group page after loading cookies."""
    load_cookies(driver)
    driver.get(GROUP_URL)
    time.sleep(5)  # Give time for the page to load
    print("[+] Accessed Facebook group.")

def get_latest_post(driver):
    """Scrapes the sender's name and the main content of the second post."""
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
        )
        
        # Find all posts in the feed
        posts = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div")
        
        if len(posts) > 1:  # Ensure there is a second post
            second_post = posts[1]  # Select the second post
            
            # Extract the sender's name from the div with role="profile_name"
            sender_name = second_post.find_element(By.CSS_SELECTOR, "div[data-ad-rendering-role='profile_name']").text.strip()

            # Extract the main content of the post
            post_content = second_post.find_element(By.CSS_SELECTOR, "div[data-ad-rendering-role='story_message']").text.strip()

            return sender_name, post_content
        return None, None
    except Exception as e:
        print(f"[-] Error fetching posts: {e}")
        return None, None

def monitor_group():
    """Continuously checks for new posts every minute."""
    last_sender = None  # To store the sender of the last detected post
    last_post_content = None  # To store the content of the last detected post

    while True:
        # Setup a new driver instance each time to avoid cache
        driver = setup_driver()

        # Access the group and load cookies
        access_group(driver)

        sender_name, post_content = get_latest_post(driver)

        # Check if the current post is different from the last detected post
        if sender_name and post_content:
            if sender_name != last_sender or post_content != last_post_content:
                # If different, display the new post and update the last post info
                print(f"\n[+] New Post Detected:\nSender: {sender_name}\nPost: {post_content}\n")
                last_sender = sender_name  # Update last sender
                last_post_content = post_content  # Update last post content
            else:
                print("[-] No new post detected. Same post as last time.")
        else:
            logging.warning("[-] No new post found.")
        
        # Close the driver session after each iteration
        driver.quit()

        time.sleep(60)  # Wait for 1 minute before checking again

if __name__ == "__main__":
    monitor_group()
