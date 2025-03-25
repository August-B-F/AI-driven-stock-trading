from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from datetime import date, timedelta, datetime
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome
from time import sleep
from re import findall
import csv
import os

from components.logging.logging import write_to_log
from components.misc.progress_bar import print_progress_bar

# import plotly.express as px
# from pyvirtualdisplay import Display

def get_latest_price(driver):
    try:
        price_element = driver.find_element(By.XPATH, "//table[@class='table']/tbody/tr[1]/td[2]")
        return float(price_element.text)
    
    except Exception as e:
        write_to_log(f"""Error getting latest price for commodity:{e}""")
        return None

def transform_price(latest_price, data_points):
    max_y = max(y for _, y in data_points)
    inverted_points = [(x, max_y - y + 1) for x, y in data_points]
    scale_factor = latest_price / inverted_points[-1][1]
    
    return [(x, y * scale_factor) for x, y in inverted_points]

def get_date(x, end_date, num_points):
    return end_date - timedelta(days=int(num_points - x - 1))

def save_to_csv(data, filename):
    file_exists = os.path.isfile(filename)
    
    if file_exists:
        with open(filename, "r") as csvfile:
            existing_dates = set(row[0] for row in csv.reader(csvfile) if row)
        
        new_data = [row for row in data if row[0] not in existing_dates]
        
        if new_data:
            with open(filename, "a", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerows(new_data)
                
    else:
        with open(filename, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Date", "Price"])
            csv_writer.writerows(data)

def get_commodity_data(commodities):
    write_to_log(f"Commodity scraping start at: {datetime.now()}")
    
    # for os with no gui 
    # display = Display(visible=0, size=(1920, 1080))
    # display.start()

    data = {}
    index = 0 
    fails = 0 
    successes = 0

    options = ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--page-load-strategy=eager")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-position=-1920,0")

    driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    sleep(2)
    
    driver.get(f"https://tradingeconomics.com/commodity/Gold")
    
    try:
        reject_button = driver.find_element(By.XPATH, "//p[@class='fc-button-label']")
        reject_button.click()
    
    except: 
        pass

    for commodity in commodities:
        print_progress_bar(index, len(commodities), description="Scraping commodity: ")
        index += 1 
        
        try:
            commodity_name = commodity.replace(" ", "-").lower()
            driver.get(f"https://tradingeconomics.com/commodity/{commodity_name}")
            
            if driver.find_elements(By.CLASS_NAME, "noDataPlacehoder"):
                write_to_log(f"commodity {commodity} not found")
                continue
            
            latest_price = get_latest_price(driver)
            if latest_price is None:
                raise Exception("failed to get latest price")

            # extract graph data
            graph = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "g.highcharts-series.highcharts-series-0.highcharts-line-series"))
            )
            data_string = graph.find_element(By.TAG_NAME, "path").get_attribute("d")
            data_points = [(float(x), float(y)) for _, x, y in findall(r"([ML]) (-?\d+\.?\d*) (-?\d+\.?\d*)", data_string)]

            # transform and save data
            end_date = date.today()
            transformed_data = [
                (get_date(i, end_date, len(data_points)).strftime("%Y-%m-%d"), y)
                for i, (_, y) in enumerate(transform_price(latest_price, data_points))
            ]

            csv_filename = f"data/raw_data/raw_commodity/{commodity_name}.csv"
            save_to_csv(transformed_data, csv_filename)
            
            data[commodity] = transformed_data
            sleep(1)
            
            successes += 1 
            
        except Exception as e:
            write_to_log(f"""Error getting commodity data for {commodity}
Error: {e}
At: {datetime.now()}""")
            sleep(2)
            
            fails += 1 
            continue            

    driver.quit()

    write_to_log(f"Commodity scraping done with {fails} fails and {successes} successes")

    if successes + fails != len(commodities): 
        write_to_log(f"""Something is wrong in commodity scraping, the times scraped do not match the number of companies. 
Scrapes done: {successes + fails}
Total commodities: {len(commodities)}""")
        
    return data