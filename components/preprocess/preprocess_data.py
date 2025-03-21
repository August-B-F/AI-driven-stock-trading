from sklearn.preprocessing import StandardScaler
import numpy as np
import datetime
import csv
import os

from components.logging.logging import write_to_log
from components.misc.progress_bar import print_progress_bar

# def write_to_log(text): 
#     print(text)
    
def process_historical(company_name, TODAYS_DATE):
    today_date = datetime.datetime.strptime(TODAYS_DATE, "%Y-%m-%d").date()
    price_data = []
    volume_data = []
    
    with open(f"data/historical/{company_name}.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)  # skip header
        
        for row in reader:
            try:
                date = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
                
                if date <= today_date:
                    price_data.append(float(row[1]))
                    volume_data.append(float(row[2]))
                    
            except (ValueError, IndexError):
                continue
            
        file.close()
        
    return price_data, volume_data

def calculate_rsi(prices, window=14):
    if len(prices) < window + 1:
        raise ValueError("Not enough data points to calculate RSI for the given window.")
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    
    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window
    
    rsi = []
    for i in range(window, len(prices)):
        if i > window:
            delta = deltas[i-1]
            gain = gains[i-1]
            loss = losses[i-1]
            avg_gain = (avg_gain * (window - 1) + gain) / window
            avg_loss = (avg_loss * (window - 1) + loss) / window
        
        if avg_loss == 0:
            rs = float('inf')
        else:
            rs = avg_gain / avg_loss
        
        rsi.append(100 - (100 / (1 + rs)))
    
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    def calculate_ema(data, span):
        ema = []
        multiplier = 2 / (span + 1)
        ema.append(data[0])  # First EMA is just the first data point
        for i in range(1, len(data)):
            ema.append((data[i] - ema[i-1]) * multiplier + ema[i-1])
        return ema
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    macd = [ema_fast[i] - ema_slow[i] for i in range(len(prices))]
    signal_line = calculate_ema(macd, signal)
    histogram = [macd[i] - signal_line[i] for i in range(len(macd))]
    
    return macd, signal_line, histogram

def calculate_obv(prices, volume):
    if len(prices) != len(volume):
        raise ValueError("Prices and volume must have the same length.")
    
    obv = [0]  # Start with OBV = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            obv.append(obv[i-1] + volume[i])
        elif prices[i] < prices[i-1]:
            obv.append(obv[i-1] - volume[i])
        else:
            obv.append(obv[i-1])
    
    return obv

def process_news(company_name, TODAYS_DATE):
    today_date = datetime.datetime.strptime(TODAYS_DATE, "%Y-%m-%d").date()
    score_data = []
    
    with open(f"data/news/{company_name}.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)  # skip header
        
        for row in reader:
            try:
                date = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
                
                if date <= today_date:
                    score_data.append(float(row[1]))
   
            except (ValueError, IndexError):
                continue
            
        file.close()
        
    return score_data

def process_commodity(commodity_names, company_price, HISTORICAL_DAYS, TODAYS_DATE):
    diffs = {}
    commodity_prices = {}
    today_date = datetime.datetime.strptime(TODAYS_DATE, "%Y-%m-%d").date()

    # read and process commodity data
    for commodity in commodity_names:
        commodity = commodity.lower().replace(" ", "-")
        prices = []
        dates = []
        
        with open(f"data/commodity/{commodity}.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)  # skip header
            
            for row in reader:
                try:
                    date = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
                    
                    if date <= today_date:
                        dates.append(date)
                        prices.append(float(row[1]))
                        
                except (ValueError, IndexError):
                    continue
                
            file.close()
        
        # sort by date and store prices
        sorted_prices = [p for _, p in sorted(zip(dates, prices))]
        commodity_prices[commodity] = sorted_prices

    # calculate differences
    for commodity in commodity_names:
        commodity = commodity.lower().replace(" ", "-")
        
        if not commodity_prices[commodity]:
            diffs[commodity] = float('inf')
            continue

        # scale prices
        scaler = StandardScaler()
        commodity_data = np.array(commodity_prices[commodity]).reshape(-1, 1)
        scaled_commodity = scaler.fit_transform(commodity_data).flatten()
        
        company_data = np.array(company_price).reshape(-1, 1)
        scaled_company = scaler.transform(company_data).flatten()

        # align lengths
        min_length = min(len(scaled_commodity), len(scaled_company))
        if min_length == 0:
            diffs[commodity] = float('inf')
            continue

        trunc_commodity = scaled_commodity[:min_length]
        trunc_company = scaled_company[:min_length]

        # calculate RMSE
        diffs[commodity] = np.sqrt(np.mean((trunc_commodity - trunc_company) ** 2))

    # get top 3 commodities
    best_commodities = sorted(diffs, key=lambda x: diffs[x])[:3]
    
    # prepare historical data
    results = []
    for commodity in best_commodities:
        commodity = commodity.lower().replace(" ", "-")
        prices = commodity_prices.get(commodity, [])
        results.append(prices[-HISTORICAL_DAYS:] if len(prices) >= HISTORICAL_DAYS else prices)
    
    return tuple(results)

def preprocess_data(company_names, commodity_names, company_index, HISTORICAL_DAYS, TODAYS_DATE):
    write_to_log(f"Preprocessing data start at: {datetime.datetime.now()}")
    
    scalers = {
        "prices": StandardScaler(),
        "news": StandardScaler(),
        "commodities": StandardScaler(),
        "rsi": StandardScaler(),
        "macd": StandardScaler(),
        "obv": StandardScaler(),
    }
    
    # load and scale commodity data
    index = 0 
    fails = 0 
    successes = 0
    
    price_data = {}
    news_data = {}
    commodity_1_data = {}
    commodity_2_data = {}
    commodity_3_data = {}
    name_data = {}
    rsi_data = {}
    macd_data = {}
    obv_data = {}
    
    for company in company_names:
        print_progress_bar(index, len(company_names), description="Preprocessing data: ")
        index += 1 

        try: 
            price, volume = process_historical(company, TODAYS_DATE)
            news = process_news(company, TODAYS_DATE)
            commodity_1, commodity_2, commodity_3 = process_commodity(commodity_names, price, HISTORICAL_DAYS, TODAYS_DATE)
            rsi = calculate_rsi(price)
            macd, _, _ = calculate_macd(price)
            obv = calculate_obv(price, volume)
            
            # convert lists to NumPy arrays for scaling
            price = np.array(price).reshape(-1, 1)
            news = np.array(news).reshape(-1, 1)
            rsi = np.array(rsi).reshape(-1, 1)
            macd = np.array(macd).reshape(-1, 1)
            obv = np.array(obv).reshape(-1, 1)

            # scale
            price = scalers["prices"].fit_transform(price).flatten().tolist()
            news = scalers["news"].fit_transform(news).flatten().tolist()
            rsi = scalers["rsi"].fit_transform(rsi).flatten().tolist()
            macd = scalers["macd"].fit_transform(macd).flatten().tolist()
            obv = scalers["obv"].fit_transform(obv).flatten().tolist()
            
            price_data[company] = price[-HISTORICAL_DAYS:]
            news_data[company] = news[-HISTORICAL_DAYS:]
            commodity_1_data[company] = commodity_1[-HISTORICAL_DAYS:]
            commodity_2_data[company] = commodity_2[-HISTORICAL_DAYS:]
            commodity_3_data[company] = commodity_3[-HISTORICAL_DAYS:]
            name_data[company] = int(company_index[company_names.index(company)])
            rsi_data[company] = rsi[-HISTORICAL_DAYS:]
            macd_data[company] = macd[-HISTORICAL_DAYS:]
            obv_data[company] = obv[-HISTORICAL_DAYS:]
            
            successes += 1 
        
        except Exception as e: 
            write_to_log(f"""Failed to preprocess {company}:
Error: {e}
At: {datetime.datetime.now()}""")
            
            fails += 1 
            continue

    write_to_log(f"""Preprocessing done with {successes} successes and {fails} fails at: {datetime.datetime.now()}""")
    
    if successes + fails != len(company_names): 
        write_to_log(f"""Something is wrong with preprocessing, the companies processed do not match the number of companies. 
Done: {successes + fails}
Total: {len(company_names)}""")

    return price_data, news_data, commodity_1_data, commodity_2_data, commodity_3_data, name_data, rsi_data, macd_data, obv_data