import statsmodels.api as sm
import pandas as pd
import datetime
import json
import os

from components.logging.logging import write_to_log
from components.misc.progress_bar import print_progress_bar

# smooths out the data a bit 
use_freq = True

def save_to_processed_file(df, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df.to_csv(filename, index=False)

def load_from_raw_file(filename):
    return pd.read_csv(filename)

def load_json_from_raw_file(filename):
    with open(filename, "r") as f:
        return json.load(f)

def fix_date_gaps(df, clm_name="Score"):
    df["Date"] = pd.to_datetime(df["Date"])
    start_date = df["Date"].min()
    end_date = df["Date"].max()
    all_dates = pd.date_range(start_date, end_date)
    new_df = pd.DataFrame({"Date": all_dates})
    merged_df = pd.merge(new_df, df, on="Date", how="left")
    merged_df[clm_name] = merged_df[clm_name].interpolate()
    
    return merged_df

def monthly_to_daily(df, date_col="Date", value_col="Score"):
    df[date_col] = pd.to_datetime(df[date_col])
    start_date = df[date_col].min()
    end_date = df[date_col].max()
    daily_dates = pd.date_range(start_date, end_date, freq="D")
    daily_df = pd.DataFrame({date_col: daily_dates})
    merged_df = pd.merge(daily_df, df, on=date_col, how="left")
    merged_df[value_col] = merged_df[value_col].ffill()
    
    return merged_df

def add_missing_dates(data, clm_name="Score"):
    last_date = data["Date"].max()
    target_date = pd.to_datetime("2023-10-13")
    
    if last_date < target_date:
        date_range = pd.date_range(start=last_date + pd.Timedelta(days=1), end=target_date)
        missing_dates = pd.DataFrame({"Date": date_range})
        missing_dates[clm_name] = data[clm_name].iloc[-1] 
        data = pd.concat([data, missing_dates], ignore_index=True)
        
    return data

def freq_smooth(data, clm_name="Score"):
    if use_freq:
        lowess = sm.nonparametric.lowess
        z = lowess(data[clm_name], data.index, frac=0.01)
        data[clm_name] = z[:, 1]
        
    return data

def load_day_data(company):
    df = load_from_raw_file(f"data/raw_data/raw_historical/{company}.csv")

    prices = df["Close"].tolist()
    volumes = df["Volume"].tolist()
    dates = df["Date"].tolist()
    
    day_data = pd.DataFrame({"Date": dates, "Adj Close": prices, "Volume": volumes})
    day_data["Date"] = pd.to_datetime(day_data["Date"])

    day_data = fix_date_gaps(day_data, clm_name="Adj Close")
    day_data = fix_date_gaps(day_data, clm_name="Volume")  

    day_data = add_missing_dates(day_data, clm_name="Adj Close")
    day_data = add_missing_dates(day_data, clm_name="Volume")

    if use_freq:
        lowess = sm.nonparametric.lowess
        z = lowess(day_data["Adj Close"], day_data.index, frac=0.005)
        day_data["Adj Close"] = z[:, 1]

    save_to_processed_file(day_data, f"data/historical/{company}.csv")

def load_news(company):
    json_data = load_json_from_raw_file(f"data/raw_data/raw_news/{company}.json")

    scores = []
    dates = []

    for date in json_data:
        weeks_score = 0
        weeks_index = 0  
        
        for article in json_data[date]:
            try:
                probability = json_data[date][article]["score"]
                sentiment = json_data[date][article]["finbert_sentiment"]

                if sentiment == "positive":
                    weeks_score += 100 * probability  
                    weeks_index += 1 
                    
                elif sentiment == "negative":
                    weeks_score -= 100 * probability 
                    weeks_index += 1
                    
                elif sentiment == "neutral":
                    weeks_score += 0
                    weeks_index += 1
                    
            except:
                pass
        
        if weeks_index > 0: 
            weeks_score = weeks_score / weeks_index
            weeks_score = round(weeks_score, 2)
            
        else:
            weeks_score = 0

        scores.append(weeks_score)
        dates.append(date)

    news_data = pd.DataFrame({"Date": dates, "Score": scores})
    news_data["Date"] = pd.to_datetime(news_data["Date"])
    news_data = news_data.sort_values("Date").reset_index(drop=True)

    if not news_data.empty:
        news_data = fix_date_gaps(news_data)
        news_data = add_missing_dates(news_data)

    if use_freq: 
        lowess = sm.nonparametric.lowess
        z = lowess(news_data["Score"], news_data.index, frac=0.015)
        news_data["Score"] = z[:, 1]

    save_to_processed_file(news_data, f"data/news/{company}.csv")

def load_commodities(commodity):
    df = load_from_raw_file(f"data/raw_data/raw_commodity/{commodity}.csv")
    save_to_processed_file(df, f"data/commodity/{commodity}.csv")

def json_to_csv():
    write_to_log(f"Json to CSV conversion start at: {datetime.datetime.now()}")
    
    # process historical data
    index = 0 
    fails = 0 
    successes = 0
    
    for filename in os.listdir("data/raw_data/raw_historical"):
        print_progress_bar(index, len(os.listdir("data/raw_data/raw_historical")), description="Converting historical data to csv")
        index += 1 
        
        try: 
            if filename.endswith(".csv"):
                company = filename.split(".csv")[0]
                load_day_data(company)
                
                successes += 1 
                
        except Exception as e: 
            write_to_log(f"""Failed to convert {company} historical data to csv. 
Error: {e}
AT: {datetime.datetime.now()}""")
            
            fails += 1 
            
    write_to_log(f"Historical data CSV conversion done with {fails} fails and {successes} successes")

    # process news data
    index = 0 
    fails = 0 
    successes = 0
    
    for filename in os.listdir("data/raw_data/raw_news"):
        print_progress_bar(index, len(os.listdir("data/raw_data/raw_news")), description="Converting news data to csv")
        index += 1 
        
        try: 
            if filename.endswith(".json"):
                company = filename.split(".json")[0]
                load_news(company)
                
                successes += 1 
                
        except Exception as e: 
            write_to_log(f"""Failed to convert {company} news data to csv. 
Error: {e}
AT: {datetime.datetime.now()}""")
            
            fails += 1 

    write_to_log(f"News data CSV conversion done with {fails} fails and {successes} successes")

    # process commodity data
    index = 0 
    fails = 0 
    successes = 0
    
    for filename in os.listdir("data/raw_data/raw_commodity"):
        print_progress_bar(index, len(os.listdir("data/raw_data/raw_commodity")), description="Converting commodity data to csv")
        index += 1 
        
        try: 
            if filename.endswith(".csv"):
                commodity = filename.split(".csv")[0]
                load_commodities(commodity)
                
                successes += 1 
                
        except Exception as e: 
            write_to_log(f"""Failed to convert {commodity} commodity data to csv. 
Error: {e}
AT: {datetime.datetime.now()}""")
            
            fails += 1 
            
    write_to_log(f"News data CSV conversion done with {fails} fails and {successes} successes")
    write_to_log(f"All CVS conversion done at: {datetime.datetime.now()}")