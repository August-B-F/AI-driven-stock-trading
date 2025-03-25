from keras.models import load_model
import datetime
import time
import json
import os

from components.misc.clear_console import clear_console
from components.logging.logging import write_to_log 
from components.get_data.get_news_data import get_news_data
from components.get_data.get_commodity_data import get_commodity_data
from components.get_data.get_historical_data import get_historical_data
from components.preprocess.json_to_csv import json_to_csv
from components.preprocess.preprocess_data import preprocess_data
from components.prediction.prediction import make_predictions
from components.execute_trades.execute_trades import execute_trades

# TODO 
# Check so that we do not borrow money
# Test make trade
# Check if new news scraper data work for ai, and if runs better on title. 4% with title
# Fix the loging a bit 

# TODO later 
# Change file system to Linux
# Activate tor and VPN if needed 

################
### settings ###
################

# DO NOT CHANGE, have been tested +1m times to be the best. Maybe make so that it runs that every month? 
DIVERSIFICATION = 6                        # number of stocks to invest in each day
STOP_LOSS = 0.17591568344978034            # stop loss percentage
TAKE_PROFIT = 0.2656486232205517           # take profit percentage
MONEY_TO_INVEST = 0.3392394782708459       # % that can be invested per day
RISK_TOLERANCE = 0.19140403603152611       # % that can be invested per day
CONFIDENCE_THRESHOLD = 0.71149793900788    # minimum confidence level required for investment
TRAILING_STOP_LOSS = 0.010217685163146514  # trailing stop loss percentage
REBALANCE_THRESHOLD = 0.28232967833124156  # portfolio rebalance threshold

# time settings for ai internals. Changing these will crash the ai 
PERIOD = 1            # the days it will scrape, can be changed if you want more data 
PREDICTION_DAYS = 1   # number of days forward it will predict, hardcoded in the ai to be one, DO NOT CHANGE  
HISTORICAL_DAYS = 20  # the number of data points in the past it predicts with, ie data from the past 20 days for all data points, also hardcoded, DO NOT CHANGE
TODAYS_DATE = datetime.datetime.now().strftime('%Y-%m-%d')

####################
### data loading ###
####################

# getting the company names, tickers and index value to use
with open("assets/companies.json") as file: 
    company_info = json.load(file)
    file.close()
    
company_names = []
company_tickers = []
company_index = []

for n in range(len(company_info)):
    company_names.append(company_info[f"{n}"]["name"])
    company_tickers.append(company_info[f"{n}"]["ticker"])
    
    # the value that the AI uses to recognize the stock, calc with sum(ord(c) for c in "company name")
    # the names have changed since training so thats why they are hardcoded  
    company_index.append(company_info[f"{n}"]["index"])
    
# loading the commodity names 
with open("assets/commodities.json") as file: 
    commodity_names = json.load(file)
    file.close()

#################
### api setup ###    
#################

# alpaca API setup, .env does not work 
ALPACA_KEY = "PKD10M16C6OGGW10V2LP"
ALPACA_SECRET = "hDYaaplNQdFzB4AdgxpNQUjFhVJRqagiD4IvbDJP"
ALPACA_ENDPOINT = "https://paper-api.alpaca.markets"

###################
### model setup ###
###################

# model vars, also do not change
model = load_model("assets/model.h5")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # suppress TensorFlow logs
os.environ['KMP_AFFINITY'] = 'noverbose'  # suppress OpenMP logs

def main(): 
    try: 
        write_to_log(f"""===================
Program started at: {datetime.datetime.now()}
===================""")
        
        ### webscraping
        get_news_data(company_names, PERIOD)
        get_commodity_data(commodity_names)
        get_historical_data(company_tickers, company_names, "1y") 
        
        ### preprocessing 
        json_to_csv() # turning all the json data files to csv for better processing  
        price_data, news_data, commodity_1_data, commodity_2_data, commodity_3_data, name_data, rsi_data, macd_data, obv_data = preprocess_data(company_names, commodity_names, company_index, HISTORICAL_DAYS, TODAYS_DATE)
        
        ### predicting 
        predictions = make_predictions(price_data, news_data, commodity_1_data, commodity_2_data, commodity_3_data, name_data, rsi_data, macd_data, obv_data, model, company_names)
                  
        ### executing trades 
        execute_trades(predictions, ALPACA_KEY, ALPACA_SECRET, 
                            ALPACA_ENDPOINT, company_tickers, company_names,
                            RISK_TOLERANCE, DIVERSIFICATION, STOP_LOSS, 
                            TAKE_PROFIT, TRAILING_STOP_LOSS, REBALANCE_THRESHOLD, 
                            CONFIDENCE_THRESHOLD, MONEY_TO_INVEST)
        
    except Exception as e:
        write_to_log(f"""------------------
A fatal error happened at: {datetime.datetime.now()}
Error: {e}
------------------""")
        
    finally: 
        write_to_log(f""" 
===================
Program ended at: {datetime.datetime.now()}
===================""")   
    
if __name__ == "__main__": 
    start_time = time.time()
    clear_console()
    
    main()
    
    clear_console()
    elapsed_time_minutes = (time.time() - start_time) / 60
    
    print(f"Trading done, time run: {elapsed_time_minutes:.2f} min")