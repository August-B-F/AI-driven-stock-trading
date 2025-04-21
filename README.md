# AI-Driven Stock Trading Program 📈

**An AI-powered stock trading system that predicts stock prices and executes trades using web-scraped data and the Alpaca API.**

***

## Overview

This project is an AI-driven stock trading system designed to predict stock prices and execute trades automatically. It scrapes web data (e.g., news from Google) and historical stock data, preprocesses it, makes predictions using a trained Keras model, and executes trades via the [Alpaca API](https://alpaca.markets/). The system is optimized for maximum returns with configurable settings like diversification, stop-loss, and risk tolerance.

### ✨ Features
- **Web Scraping**: Collects news and historical stock data.
- **Machine Learning**: Uses a custom trained LSTM model for predictions.
- **Automated Trading**: Executes trades via the Alpaca API.
- **Optimized Settings**: Fine-tuned for risk management and profitability.
- **Logging**: Detailed logs for debugging and performance tracking.

---

## 🚀 Requirements

- **Python**: 3.8 or higher
- **Dependencies** In requirements.txt
- **Alpaca API Account**: Required for trading ([sign up here](https://alpaca.markets/)).
- **Pre-trained Model**: A `model.h5` file in the `assets/` directory.
- **OS**: Windows 10 or higher 

---

## 🛠️ Setup

Follow these steps to get the project up and running:

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/Bob1883/AI-driven-stock-trading
   cd AI-driven-stock-trading
   ```

2. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**  
   - Create a `.env` file in the root directory.
   - Add your Alpaca API credentials:
     ```
     ALPACA_KEY=your_alpaca_key
     ALPACA_SECRET=your_alpaca_secret
     ```

4. **Prepare Data and Model**  
   - Ensure the `assets/` directory contains:
     - `model.h5` (pre-trained Keras model)
     - `companies.json` (list of companies to trade)
     - `commodities.json` (list of commodities for data scraping)

---

## 📖 Usage

1. **Run the Program**  
   ```bash
   python main.py
   ```
   The program will:
   - Scrape data for the specified period (Minimum 20, if you already have 20 days worth of data you can run it with 1).
   - Preprocess the data and make predictions.
   - Execute trades based on predictions and settings.

2. **Output**  
   - Logs are written to `log.txt` for debugging and tracking.
   - Console output shows the runtime and trade summary (e.g., "Trading done, time run: 5.23 min").

3. **Customization**  
   - Modify settings in `main.py` (e.g., `DIVERSIFICATION`, `STOP_LOSS`) to adjust trading behavior.
   - Update `PERIOD` to scrape data for a different time range.

---

## 📂 Project Structure

```
├── main.py                 # Main script to run the program
├── config.py               # Configuration settings (optional, if created)
├── assets/                 # Model and data files
│   ├── backtesting/        # Some testing files 
│   ├── model.h5            # Pre-trained Keras model
│   ├── companies.json
│   ├── log.txt
│   ├── portfolio.json      # Old portfolio, used for trading 
│   ├── predictions_log.txt
│   ├── transaction_log.txt
│   └── commodities.json
├── components/             # Modular components for scraping, preprocessing, etc.
│   ├── misc/
│   ├── logging/trade.log
│   ├── get_data/
│   ├── preprocess/
│   ├── prediction/
│   └── execute_trades/
├── LICENSE                 # License file (GPL-3.0)
└── README.md               # Project documentation
```

---

## 📜 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details. For commercial use, please contact the author at [august.frigo@gmail.com](mailto:august.frigo@gmail.com) for permission.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

---

## ⚠️ Limitations

- The model is pre-trained and may not generalize to all market conditions.
- Requires a stable internet connection for web scraping and API calls.
- Hardcoded settings (e.g., `HISTORICAL_DAYS`) may need adjustments for different use cases.

---

## 🔮 Future Improvements

- Add unit tests for core components.
- Implement data visualization for predictions.
- Support for command-line arguments to adjust settings dynamically.
- Add linux support.

---

## 📬 Contact

For questions, commercial use permission, or collaboration, reach out to the author at [august.frigo@gmail.com](mailto:august.frigo@gmail.com).

---