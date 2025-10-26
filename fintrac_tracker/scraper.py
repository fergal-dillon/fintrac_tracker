from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ------------------ SCRAPE FINTRAC ------------------
service = Service("/opt/homebrew/bin/chromedriver")
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # run in background
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://fintrac-canafe.canada.ca/new-neuf/1-eng")
wait = WebDriverWait(driver, 10)
table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))

rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # skip header row
news_items = []

for row in rows:
    cells = row.find_elements(By.TAG_NAME, "td")
    date = cells[0].text.strip("[] ")
    title = cells[1].text.strip()
    link = cells[1].find_element(By.TAG_NAME, "a").get_attribute("href")
    news_items.append({"date": date, "title": title, "link": link})

driver.quit()

# Save to CSV (optional backup)
csv_file = "fintrac_news.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "title", "link"])
    writer.writeheader()
    writer.writerows(news_items)

print(f"✅ Scraped {len(news_items)} FINTRAC news items successfully!")

# ------------------ GOOGLE SHEETS UPLOAD ------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("fintrac-credentials.json", scope)
client = gspread.authorize(creds)

# Make sure this matches the tab you want updated
sheet = client.open("FINTRAC Tracker").worksheet("Fintrac Tracker")  # exact tab name

# Load CSV into DataFrame
df = pd.read_csv(csv_file)

# Write headers in row 2
sheet.update("A2", [df.columns.values.tolist()])

# Write data starting from row 3
start_row = 3
sheet.update(f"A{start_row}", df.values.tolist(), value_input_option="RAW")

# Replace raw links with "Read article"
for i, row in enumerate(df.itertuples(index=False), start=start_row):
    url = row.link
    sheet.update_cell(i, 3, f'=HYPERLINK("{url}", "Read article")')

# Timestamp in top-right cell (E1)
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
sheet.update("E1", f"Last updated: {timestamp}")
sheet.format("E1", {"textFormat": {"bold": True}, "horizontalAlignment": "RIGHT"})

print("✅ Data uploaded and formatted successfully!")





