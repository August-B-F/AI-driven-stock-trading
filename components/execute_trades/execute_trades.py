import alpaca_trade_api as tradeapi
import datetime
import json 
import csv
import os

from components.logging.logging import write_to_log
from components.logging.transaction_logging import write_to_transaction_log

# change how the values are handled so that i gives back company not symbol 
# remove day param 
def execute_trades(predictions, api_key, api_secret, 
                   base_url, company_symbols, company_names,
                   RISK_TOLERANCE=0.1, DIVERSIFICATION=5, 
                   STOP_LOSS=0.05, TAKE_PROFIT=0.1, 
                   TRAILING_STOP_LOSS=0.03, REBALANCE_THRESHOLD=0.05,
                   CONFIDENCE_THRESHOLD=0.7, MONEY_TO_INVEST=0.1):
    
    write_to_log(f"Executing trades start at: {datetime.datetime.now()}")
    write_to_transaction_log(f"""===================
Trading start at: {datetime.datetime.now()}
===================""")
    
    if os.path.exists(f"assets/portfolio.json"):
        with open('assets/portfolio.json', 'r') as file:
            portfolio = json.load(file)
            file.close()
            
    else: 
        portfolio = {}
        
    # initialize Alpaca API
    api = tradeapi.REST(api_key, api_secret, base_url, api_version="v2")
    
    company_to_symbol = dict(zip(company_names, company_symbols))
    money = float(api.get_account().cash)
    print(money)
    current_prices = {}

    # try:
    for company in company_names:
        with open(f"data/historical/{company}.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)  # skip header
            
            symbol = company_symbols[company_names.index(company)]
            
            for row in reader:
                current_prices[symbol] = float(row[1])
                
                break
               
#     except Exception as e:
#         write_to_log(f"Error getting prices: {e}")
#         write_to_prediction_log(f"""
# ===================
# Trading stopt unexpectedly at: {datetime.datetime.now()}
# With error: {e}
# ===================""")
        
#         return portfolio, money

    # update portfolio and check exit conditions
    new_portfolio = {}
    
    for symbol in list(portfolio.keys()):
        position = portfolio[symbol]
        last_price = current_prices.get(symbol, position["price"])
        
        exit_trade = False
        exit_reason = ""
        
        # check exit conditions
        if last_price <= position["price"] * (1 - STOP_LOSS):
            exit_reason = "Stop loss"
            exit_trade = True
            
        elif last_price >= position["price"] * (1 + TAKE_PROFIT):
            exit_reason = "Take profit"
            exit_trade = True
            
        elif last_price <= position["trailing_stop"]:
            exit_reason = "Trailing stop"
            exit_trade = True
            
        if exit_trade:
            try:
                # sell position
                api.close_position(symbol)
                money += last_price * position["amount"]

                # change to show company name, and change in price 
                write_to_transaction_log(f"Sold {symbol} because of '{exit_reason}', with a return of ~${last_price}, at: {datetime.datetime.now()}")
                
            except Exception as e:
                write_to_transaction_log(f"Could not sell {symbol}, error: {e}")
                write_to_log(f"Could not sell {symbol}, error: {e}")
                
        else:
            # update portfolio 
            new_trailing_stop = max(position["trailing_stop"],
                                   last_price * (1 - TRAILING_STOP_LOSS))
            
            new_portfolio[symbol] = {
                "price": position["price"],
                "amount": position["amount"],
                "trailing_stop": new_trailing_stop
            }
    
    portfolio = new_portfolio
    
    money = float(api.get_account().cash)

    # rebalance portfolio
    portfolio_value = sum(pos["amount"] * current_prices.get(sym, pos["price"]) 
                       for sym, pos in portfolio.items())
    
    if portfolio_value > 0:
        for symbol in list(portfolio.keys()):
            current_value = portfolio[symbol]["amount"] * current_prices.get(symbol, portfolio[symbol]["price"])
            target_value = portfolio_value / len(portfolio)
            
            if abs(current_value - target_value) / portfolio_value > REBALANCE_THRESHOLD:
                # try:
                    # Calculate shares to buy/sell
                    current_shares = portfolio[symbol]["amount"]
                    target_shares = target_value / current_prices[symbol]
                    delta = target_shares - current_shares
                    
                    # buy
                    if delta > 0:  
                        api.submit_order(
                            symbol=symbol,
                            qty=round(delta, 2),
                            side="buy",
                            type="market",
                            time_in_force="day"
                        )
                        
                    # sell    
                    elif delta < 0:  
                        api.submit_order(
                            symbol=symbol,
                            qty=round(abs(delta), 2),
                            side="sell",
                            type="market",
                            time_in_force="day"
                        )
                    
                    # update local portfolio tracking
                    portfolio[symbol]["amount"] = target_shares
                    write_to_transaction_log(f"Rebalanced {symbol} to {target_shares} shares from {current_shares}")
                    
                # except Exception as e:
                #     write_to_prediction_log(f"Error rebalancing {symbol}: {e}")
                #     write_to_log(f"Error rebalancing {symbol}: {e}")

    # generate investment targets
    top_stocks = []
    for company in company_names:
        symbol = company_to_symbol[company]
        pred = predictions[company]["mean"][0]
        std = predictions[company]["std"][0]
        confidence = 1 / (1 + std)
        adjusted_price = pred * (1 - RISK_TOLERANCE) * confidence
        
        top_stocks.append((symbol, adjusted_price, confidence))
    
    # select top diversified stocks
    top_stocks = sorted(top_stocks, key=lambda x: x[1], reverse=True)[:DIVERSIFICATION]
    
    money = float(api.get_account().cash)

    # execute new investments
    for symbol, _, confidence in top_stocks:
        if confidence > CONFIDENCE_THRESHOLD:
            # try:
                price = current_prices[symbol]
                max_invest = MONEY_TO_INVEST * money
                shares = round(max_invest * confidence / price, 2)
                
                print(symbol, shares, price)
                print(money)
                
                if shares > 0 and shares * price <= money:
                    api.submit_order(
                        symbol=symbol,
                        qty=shares,
                        side="buy",
                        type="market",
                        time_in_force="day"
                    )
                    
                    # update local portfolio
                    if symbol in portfolio:
                        portfolio[symbol]["amount"] += shares
                        
                    else:
                        portfolio[symbol] = {
                            "price": price,
                            "amount": shares,
                            "trailing_stop": price * (1 - TRAILING_STOP_LOSS)
                        }
                        
                    write_to_transaction_log(f"Invested {shares} shares in {symbol} for ~${price * shares} total")
                    
                    money = float(api.get_account().cash)
                    
            # except Exception as e:
            #     write_to_prediction_log(f"Error investing in {symbol}: {e}")
            #     write_to_log(f"Error investing in {symbol}: {e}")              

    # update cash balance from Alpaca
    portfolio_value = sum(pos["amount"] * current_prices.get(sym, pos["price"]) 
                      for sym, pos in portfolio.items())
    
    # write to log 
    write_to_log(f"Trading done at: {datetime.datetime.now()}")
    
    # add change in price, exactly what we did, and dont give money give total value 
    write_to_transaction_log(f"""
===================
Trading done at: {datetime.datetime.now()}
Executions: 
Portfolio: {portfolio}
Portfolio value: {portfolio_value}
===================""")
    
    with open("assets/portfolio.json", "w") as file:
        json.dump(portfolio, file, indent=4)
        file.close()

    return portfolio, money