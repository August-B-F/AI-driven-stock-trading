from os import path as os_path
from yfinance import download
import pandas as pd
import datetime
import logging

from components.logging.logging import write_to_log
from components.misc.progress_bar import print_progress_bar

def get_historical_data(symbols, names, period):
    write_to_log(f"Historical scraping start at: {datetime.datetime.now()}")
    
    prices = {}
    index = 0 
    fails = 0 
    successes = 0

    for symbol in symbols:
        print_progress_bar(index, len(symbols), description="Scraping historical: ")
        index += 1 
        
        try: 
            prices[symbol] = {}
            
            data = download(symbol, period=period, interval="1d", progress=False)

            if len(data) > 0:
                df = pd.DataFrame({
                    "Date": data.index,
                    "Open": data[("Open", symbol)],
                    "High": data[("High", symbol)],
                    "Low": data[("Low", symbol)],
                    "Close": data[("Close", symbol)],
                    "Volume": data[("Volume", symbol)]
                })

                filename = f"data/raw_data/raw_historical/{names[symbols.index(symbol)]}.csv"

                if os_path.exists(filename):
                    existing_df = pd.read_csv(filename, parse_dates=["Date"])
                    existing_df.set_index("Date", inplace=True)
                    
                    combined_df = pd.concat([existing_df, df.set_index("Date")])
                    combined_df = combined_df[~combined_df.index.duplicated(keep="last")]
                    combined_df.sort_index(inplace=True)
                    
                    combined_df.to_csv(filename)
                    
                else:
                    df.to_csv(filename, index=False)
                    pass

                prices[symbol] = df.to_dict("list")
                
            else:
                prices[symbol] = {
                    "Date": [], "Open": [], "High": [], "Low": [], "Close": [], "Volume": []
                }
            
            successes += 1 

        except Exception as e: 
            write_to_log(f"""Error getting historical data for {symbol}
Error: {e}
At: {datetime.datetime.now()}""")
            fails += 1 
            continue

    write_to_log(f"Historical scraping done with {fails} fails and {successes} successes")

    if successes + fails != len(symbols): 
        write_to_log(f"""Something is wrong in historical scraping, the times scraped do not match the number of companies. 
Scrapes done: {successes + fails}
Total companies: {len(symbols)}""")
        
        if fails > successes: 
            raise Exception("Something is very wrong with historical scraping")
        
    return prices