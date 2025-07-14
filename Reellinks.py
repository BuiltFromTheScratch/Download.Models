from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import os
import shutil
import random
import time
from selenium_stealth import stealth
import pandas as pd

# initializing a list with two User Agents
useragentarray = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
]

def setup_stealth_browser(driver):
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    
    return driver

# Function to close Instagram login pop-up
def close_login_popup(driver):
    try:
        close_button = driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'x1110hf1') and contains(@class, 'x972fbf') and contains(@class, 'xcfux61')]")
        close_button.click()
        print("Instagram login pop-up closed.")
    except Exception as e:
        print("No login pop-up found or could not close it:", e)

# Function to scroll and capture page sources
def scroll_and_capture_page_sources(url,driver, max_scrolls=10000):
    driver.get(url)
    page_sources = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    count = 1
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)  # Increased wait time for content to load
        print("Scroll = ",count)
        
        # Capture the page source
        page_source = driver.page_source
        page_sources.append(page_source)
        
        # Get new scroll height and check if it's the same as the last height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        count = count + 1
    
    return page_sources

# Function to extract Instagram reel links from a single page source
def extract_links_from_page_source(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        if '/reel/' in a_tag['href']:
            full_url = "https://www.instagram.com" + a_tag['href']
            links.append(full_url)
    print("Extracted links including duplicates = ",len(links))
    return links

# Setup Selenium WebDriver to use Brave with automatic download settings
def setup_selenium(download_folder):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    Chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # Update this path with your Brave installation path
    options = webdriver.ChromeOptions()
    options.binary_location = Chrome_path
    
    prefs = {
        "download.default_directory": os.path.abspath(download_folder),  # Set the download folder
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    options.add_experimental_option("useAutomationExtension", False) 
    driver = webdriver.Chrome(options=options)
    return driver

# Function to log in to Instagram
def login_to_instagram(driver, username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        username_input = driver.find_element(By.NAME, "username")
        username_input.send_keys(username)
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        time.sleep(10)
        print("Logged in successfully.")
    except Exception as e:
        print("Failed to log in:", e)
        
def extract_reel_date(driver, url):
    # Open the reel link
    driver.get(url)
    # time.sleep(10)  # Wait for the page to fully load (adjust the time as necessary)

    try:
        # Find the date element in the HTML structure
        # date_element = driver.find_element(By.XPATH, "//time[@class='x1p4m5qa']")
        date_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//time[@class='x1p4m5qa']"))
        )
        date_text = date_element.get_attribute('datetime')  # Extract the date value from 'datetime' attribute
        return date_text
    except Exception as e:
        print(f"Error extracting date from {url}: {e}")
        return None

def ordering_reels(driver, input_file):
    
    # Set up Selenium WebDriver (Make sure to provide the correct path to your WebDriver)
    # Chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # Update this path with your Chrome installation path
    # options = webdriver.ChromeOptions()
    # options.binary_location = Chrome_path

    # options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # # driver = webdriver.Chrome(options=options)
    # Read reel links from the .txt file
    with open(input_file, 'r') as file:
        reel_links = [line.strip() for line in file.readlines()]

    # List to store extracted data
    data = []
    
    count = 1
    # Loop through each reel link and extract the date
    for reel_link in reel_links:
        print("Reel link = {} , Reel Number = {}".format(count,reel_link))
        date = extract_reel_date(driver, reel_link)
        if date:
            data.append([reel_link, date])
        count+=1

    # Close the WebDriver
    driver.quit()

    # Create a DataFrame and sort it by date
    df = pd.DataFrame(data, columns=['Reel Link', 'Date'])
    df['Date'] = pd.to_datetime(df['Date'])  # Convert date strings to datetime objects for sorting
    df = df.sort_values(by='Date')  # Set ascending=False for reverse order

    # Save to CSV
    df.to_csv('reel_dates.csv', index=False)

    # Save ordered reel links to .txt file
    with open('ordered_reel_links.txt', 'w') as file:
        for link in df['Reel Link']:
            file.write(link + '\n')
            
# Main function to automate the process
def main():
    
    # STEP 1
    
    username = "jhonybhai_5"  # Replace with your Instagram username
    password = "jhonybhai@#@#19996"  # Replace with your Instagram password
    website_url = 'https://www.instagram.com/libbyvalentini/reels/'  # Replace with actual website URL
    download_folder = "VIDEOS"  # Set this to your desired download folder

    driver = setup_selenium(download_folder)

    login_to_instagram(driver, username, password)

    # Scroll down and capture page sources
    page_sources = scroll_and_capture_page_sources(website_url,driver)

    # Extract reel links from each page source
    all_reel_links = []
    
    for page_source in page_sources:
        reel_links = extract_links_from_page_source(page_source)
        all_reel_links.extend(reel_links)

    # Remove duplicates
    all_reel_links = list(set(all_reel_links))
    
    # Save all reel links to .txt file
    with open('all_reel_links.txt', 'w') as file:
        for link in all_reel_links:
            file.write(link + '\n')
    
    # driver.quit()
    
    # STEP 2
    
    ordering_reels(driver, input_file="all_reel_links.txt")

if __name__ == "__main__":
    main()
