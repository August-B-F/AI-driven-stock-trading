import numpy as np
import datetime

from components.logging.logging import write_to_log
from components.logging.prediction_logging import write_to_prediction_log
from components.misc.progress_bar import print_progress_bar  

# test if uncertainty is needed or if the ai is not that random. 
def make_predictions(price_data, news_data, commodity_1_data, commodity_2_data, 
                     commodity_3_data, name_data, rsi_data, macd_data, obv_data, 
                     model, company_names):
    write_to_log(f"Model prediction start at: {datetime.datetime.now()}")
    write_to_prediction_log(f"""===================
Model prediction start at: {datetime.datetime.now()}
===================""")
    
    predictions = {}
    index = 0 
    
    for company in company_names:
        print_progress_bar(index, len(company_names), description="Model predicting: ")
        index += 1 
        
        num_iterations = 100 # how many times the ai is run, we then find how big the difference is each time and then check how sure the ai is of the prediction 
        company_predictions = []
        
        X = [
            np.array(price_data[company]).reshape(1, -1, 1),       # (1, 20, 1)
            np.array(news_data[company]).reshape(1, -1, 1),        # (1, 20, 1)
            np.array(commodity_1_data[company]).reshape(1, -1, 1), # (1, 20, 1)
            np.array(commodity_2_data[company]).reshape(1, -1, 1), # (1, 20, 1)
            np.array(commodity_3_data[company]).reshape(1, -1, 1), # (1, 20, 1)
            np.array([name_data[company]]).reshape(1, 1),          # (1, 1)
            np.array(rsi_data[company]).reshape(1, -1, 1),         # (1, 20, 1)
            np.array(macd_data[company]).reshape(1, -1, 1),        # (1, 20, 1)
            np.array(obv_data[company]).reshape(1, -1, 1)          # (1, 20, 1)
        ]
        
        for _ in range(num_iterations):
             company_predictions.append(model.predict(X, verbose=0))
            
        company_predictions  = np.array(company_predictions)
        mean_prediction = np.mean(company_predictions , axis=0)
        std_prediction = np.std(company_predictions, axis=0)
        
        predictions[company] = {
            "mean": mean_prediction.flatten(),
            "std": std_prediction.flatten()
        }
    
    write_to_prediction_log(f"""
===================
Prediction end at: {datetime.datetime.now()}
Predictions: {predictions}
===================""")
    write_to_log(f"Prediction done with {len(predictions)} predictions at: {datetime.datetime.now()}")
    
    return predictions