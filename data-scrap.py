import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from lxml import html
import pandas as pd
from datetime import datetime
import pywhatkit
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred, {"databaseURL": "https://console.firebase.google.com/project/db-scrap/database/db-scrap-default-rtdb/data/~2F"})

def scroll_down(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_khaadi_data(url):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(5)
    scroll_down(driver)
    page_source = driver.page_source
    driver.quit()
    tree = html.fromstring(page_source)

    brands = tree.xpath('//div[@class="product-brand"]/div[@class="text-truncate"]/text()')
    links = tree.xpath('//div[@class="pdp-link"]/a[@class="link"]/@href')
    prices = tree.xpath('//div[@class="price"]//span[@class="value cc-price"]/text()')

    df = pd.DataFrame({'brand': [brand.strip() for brand in brands],
                       'link': links,
                       'price': [price.strip() for price in prices]})

    return df

def save_to_csv_pandas(data, filename_prefix='khaadi_data'):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"
    
    if data is not None and not data.empty:
        data.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return filename 
    else:
        print("No data to save")
        return None

def send_whatsapp_message(data_filename):
    if data_filename:
        with open(data_filename, 'r') as file:
            data = file.read()

        print(f"Extracted Data:\n{data}")

        pywhatkit.sendwhatmsg_instantly("+920000000000", f"Data:\n{data}", wait_time=5)
        print("WhatsApp message sent.")
    else:
        print("No data file available to send.")

# Store data on Firebase
def store_data_on_firebase(data):
    db = firestore.client()
    data_dict = data.to_dict(orient='records')

    # Create a Firestore collection reference
    collection_ref = db.collection('khaadi_data')

    # Add each item to Firestore with a generated document ID
    for item in data_dict:
        doc_ref = collection_ref.add(item)
        print(f"Document added with ID: {doc_ref[1].id}")

    print("Data stored on Firebase.")

# Main execution
url = 'https://pk.khaadi.com/new-in/fabrics/'
khaadi_data_df = scrape_khaadi_data(url)
data_filename = save_to_csv_pandas(khaadi_data_df)
send_whatsapp_message(data_filename)

# Optionally store data on Firebase
store_data_on_firebase(khaadi_data_df)