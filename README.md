Mini Market Data Terminal (HW 1)
A python app that connects to Alpaca’s paper API, getting historical $TQQQ data and streams live bid/ask quotes into a desktop window 
Demo Video

[Watch the demo video here](https://drive.google.com/file/d/1qrmRNFfVVjD-zNpbb_8s4pTr0xgdKrBo/view?usp=sharing
)

What is in here?
anaconda_projects_b8df4445-ea07-4128-80ec-0f75bcd0d2a0_data_connector.py - the connector that handles login, historical bars, latest quotes and the live stream
quote_ui.py - a Tkinter window that shows live bid / ask / last trade for a ticker 
HW1.ipynb - historical data (30 days of 1-minute bars) and the OHLCV chart 
requirements.txt 

Setup:
Install the packages:
pip install -r requirements.txt
Make a file called .env in this folder with your own Alpaca paper keys: 
APCA_API_KEY_ID=your_key_id
APCA_API_SECRET_KEY=your_secret_key
Note: keys are not included in the repo for security reasons, therefore you need to add your own from alpaca (https://app.alpaca.markets) 

Running it:
Historical chart: open HW1.ipynb and run the cells 
Live quotes: 
python quote_ui.py 
1). Type a ticker (defaults to $TQQQ), 
2). Hit Connect 
3). The bid/ask/last update as quotes come in 
Note: Quotes only move while the US market is open - outside market hours and on weekends it connects but no data shows up (which is expected)
The data comes from the IEX feed since that is what the free paper account gets.
