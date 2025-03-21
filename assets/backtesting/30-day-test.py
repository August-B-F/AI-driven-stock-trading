from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import json
import os

from components.prediction.prediction import make_predictions
from components.preprocess.preprocess_data import preprocess_data

# Move file to main if run. 

################
### settings ###
################

# DO NOT CHANGE, have been tested +1m times to be the best 
DIVERSIFICATION = 6                        # number of stocks to invest in each day
STOP_LOSS = 0.17591568344978034            # stop loss percentage
TAKE_PROFIT = 0.2656486232205517           # take profit percentage
RISK_TOLERANCE = 0.19140403603152611       # maximum acceptable risk level
MONEY_TO_INVEST = 0.3392394782708459       # % that can be invested per day
CONFIDENCE_THRESHOLD = 0.71149793900788    # minimum confidence level required for investment
TRAILING_STOP_LOSS = 0.010217685163146514  # trailing stop loss percentage
REBALANCE_THRESHOLD = 0.28232967833124156  # portfolio rebalance threshold

# time settings for ai internals 
# changing these will crash the ai 
DAYS = 30             # the number of days that the backtesting will run 
PREDICTION_DAYS = 1   # number of days forward it will predict, hardcoded in the ai to be one, DO NOT CHANGE  
HISTORICAL_DAYS = 20  # the number of data points in the past it predicts with, ie data from the past 20 days for all data points, also hardcoded, DO NOT CHANGE

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
ALPACA_KEY = "PKD4OIUF9BVHZG3NQZXD"
ALPACA_SECRET = "UkGCWups5S1hsmiTAJtgbNUXybLTOiG977wtNRPo"
ALPACA_ENDPOINT = "https://paper-api.alpaca.markets/v2"

# trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
# data_client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)

###################
### model setup ###
###################

# model vars, also do not change
model = load_model("assets/model.h5")

price_scaler = MinMaxScaler()
volume_scaler = MinMaxScaler()
news_scaler = MinMaxScaler()
commodity_scaler = MinMaxScaler()

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # suppress TensorFlow logs
os.environ['KMP_AFFINITY'] = 'noverbose'  # suppress OpenMP logs

# get all predictions 
if os.path.exists(f"assets/backtesting/predictions.json"):
    with open('assets/backtesting/predictions.json', 'r') as file:
        predictions = json.load(file)
        file.close()
        
else: 
    predictions = {}

    # Initialize the predictions dictionary
    for company in company_names:
        predictions[company] = {
            "mean": [], 
            "std": []
        }

    # Loop over the days to make predictions
    for i in range(DAYS): 
        date = datetime.datetime.now() - datetime.timedelta(days=(DAYS - i))
        TODAYS_DATE = date.strftime('%Y-%m-%d')
            
        price_data, news_data, commodity_1_data, commodity_2_data, commodity_3_data, name_data, rsi_data, macd_data, obv_data = preprocess_data(company_names, commodity_names, company_index, HISTORICAL_DAYS, TODAYS_DATE)
        prediction = make_predictions(price_data, news_data, commodity_1_data, commodity_2_data, commodity_3_data, name_data, rsi_data, macd_data, obv_data, model, company_names)

        # Process predictions for each company
        for company in prediction: 
            # Extract scalar values from NumPy arrays
            mean_value = prediction[company]["mean"].item()
            std_value = prediction[company]["std"].item()
            
            # Append to the correct lists
            predictions[company]["mean"].append(mean_value)
            predictions[company]["std"].append(std_value)

    # Save to JSON file
    with open("assets/backtesting/predictions.json", "w") as file:
        json.dump(predictions, file, indent=4)
        file.close()
        
day = 0
money = 2000
money_graph = []
portfolio = {}

for i in range(DAYS): 
    print(f"Day {day + 1}, Money: {money}")
    
    top_stocks = []
    
    for company in company_names:
        predicted_price = predictions[company]['mean'][i]
        predicted_std = predictions[company]['std'][i]
        
        # adjust prediction based on uncertainty
        confidence = 1 / (1 + predicted_std)
        risk_factor = 1 - RISK_TOLERANCE
        adjusted_price = predicted_price * risk_factor * confidence
        
        top_stocks.append((company, adjusted_price, confidence))
    
    top_stocks.sort(key=lambda x: x[1], reverse=True)
    top_stocks = top_stocks[:DIVERSIFICATION]
    
    # update portfolio
    new_portfolio = {}
    
    for company in portfolio:
        try:
            last_price = pd.read_csv(f"data/historical/{company}.csv")["Adj Close"].values[day]
            if not np.isnan(last_price):
                # check stop loss, take profit, and trailing stop loss conditions
                if last_price <= portfolio[company]["price"] * (1 - STOP_LOSS):
                    money += last_price * portfolio[company]["amount"]
                    print(f"Stop loss triggered for {company}. Sold at {last_price}")
                    
                elif last_price >= portfolio[company]["price"] * (1 + TAKE_PROFIT):
                    money += last_price * portfolio[company]["amount"]
                    print(f"Take profit triggered for {company}. Sold at {last_price}")
                    
                elif last_price <= portfolio[company]["trailing_stop"]:
                    money += last_price * portfolio[company]["amount"]
                    print(f"Trailing stop loss triggered for {company}. Sold at {last_price}")
                    
                else:
                    new_portfolio[company] = portfolio[company]
                    new_portfolio[company]["trailing_stop"] = max(portfolio[company]["trailing_stop"], last_price * (1 - TRAILING_STOP_LOSS))
                    
        except IndexError:
            continue
    
    portfolio = new_portfolio
    
    # rebalance portfolio if necessary
    portfolio_value = sum([portfolio[company]["amount"] * portfolio[company]["price"] for company in portfolio])
    
    if portfolio_value > 0:
        for company in portfolio:
            current_weight = portfolio[company]["amount"] * portfolio[company]["price"] / portfolio_value
            target_weight = 1 / len(portfolio)
            
            if abs(current_weight - target_weight) > REBALANCE_THRESHOLD:
                try:
                    last_price = pd.read_csv(f"data/historical/{company}.csv")["Adj Close"].values[day]
                    
                    if not np.isnan(last_price):
                        target_value = portfolio_value * target_weight
                        target_amount = target_value / last_price
                        
                        if target_amount < portfolio[company]["amount"]:
                            sell_amount = portfolio[company]["amount"] - target_amount
                            money += sell_amount * last_price
                            portfolio[company]["amount"] = target_amount
                            print(f"Rebalanced portfolio by selling {sell_amount} shares of {company}")
                            
                        else:
                            buy_amount = target_amount - portfolio[company]["amount"]
                            
                            if buy_amount * last_price <= money:
                                money -= buy_amount * last_price
                                portfolio[company]["amount"] = target_amount
                                print(f"Rebalanced portfolio by buying {buy_amount} shares of {company}")
                                
                except IndexError:
                    continue
    
    # invest in top stocks
    for company, predicted_price, confidence in top_stocks:
        if predicted_price > 0 and confidence > CONFIDENCE_THRESHOLD:
            try:
                last_price = pd.read_csv(f"data/historical/{company}.csv")["Adj Close"].values[day]
                
                if not np.isnan(last_price) and last_price != 0:
                    amount_to_invest = int(MONEY_TO_INVEST * money * confidence / last_price)
                    
                    if company not in portfolio and last_price * amount_to_invest <= money:
                        portfolio[company] = {
                            "price": last_price,
                            "amount": amount_to_invest,
                            "trailing_stop": last_price * (1 - TRAILING_STOP_LOSS)
                        }
                        money -= last_price * amount_to_invest
                        print(f"Invested {last_price * amount_to_invest} in {company} with confidence {confidence:.2f}")
                        
                    elif company in portfolio and last_price * amount_to_invest <= money:
                        portfolio[company]["amount"] += amount_to_invest
                        
                        if portfolio[company]["amount"] != 0:
                            portfolio[company]["price"] = (portfolio[company]["price"] * portfolio[company]["amount"] + last_price * amount_to_invest) / (portfolio[company]["amount"] + amount_to_invest)
                        money -= last_price * amount_to_invest
                        print(f"Invested additional {last_price * amount_to_invest} in {company} with confidence {confidence:.2f}")
                        
            except IndexError:
                continue
    
    day += 1
    total_value = money + sum([portfolio[company]["amount"] * portfolio[company]["price"] for company in portfolio])
    print(f"Total value: {total_value}")
    money_graph.append(total_value)
    
# plot results
plt.figure(figsize=(12, 6))
plt.plot(money_graph)
plt.title('Portfolio Value Over Time')
plt.xlabel('Days')
plt.ylabel('Value')
plt.show()