
import importlib.util
import queue
import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


CONNECTOR_FILENAME = (
    "anaconda_projects_"
    "b8df4445-ea07-4128-80ec-0f75bcd0d2a0_"
    "data_connector.py"
)


def load_connector_class():
    module_path = Path(__file__).parent / CONNECTOR_FILENAME

    spec = importlib.util.spec_from_file_location(
        "data_connector",
        module_path
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.AlpacaDataConnector


AlpacaDataConnector = load_connector_class()


class RealTimeQuoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alpaca Real-Time Quote Terminal")
        self.root.geometry("620x420")

        self.connector = AlpacaDataConnector()
        self.stream = None
        self.stream_thread = None
        self.message_queue = queue.Queue()

        self.symbol_var = tk.StringVar(value="TQQQ")
        self.current_symbol_var = tk.StringVar(value="No symbol selected")
        self.bid_var = tk.StringVar(value="—")
        self.ask_var = tk.StringVar(value="—")
        self.last_trade_var = tk.StringVar(value="—")
        self.status_var = tk.StringVar(value="Ready")

        self.build_ui()

        self.root.after(100, self.process_messages)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def build_ui(self):
        main = ttk.Frame(self.root, padding=24)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Alpaca Real-Time Quote Terminal",
            font=("Arial", 21, "bold")
        ).pack(pady=(0, 20))

        search = ttk.Frame(main)
        search.pack(pady=(0, 20))

        ttk.Label(
            search,
            text="Ticker:",
            font=("Arial", 13)
        ).pack(side="left")

        entry = ttk.Entry(
            search,
            textvariable=self.symbol_var,
            font=("Arial", 14),
            width=15
        )
        entry.pack(side="left", padx=10)
        entry.bind(
            "<Return>",
            lambda event: self.start_stream()
        )

        ttk.Button(
            search,
            text="Connect",
            command=self.start_stream
        ).pack(side="left")

        ttk.Label(
            main,
            textvariable=self.current_symbol_var,
            font=("Arial", 18, "bold")
        ).pack(pady=(0, 15))

        prices = ttk.Frame(main)
        prices.pack(fill="x", pady=10)

        self.add_metric(prices, "Current bid", self.bid_var, 0)
        self.add_metric(prices, "Current ask", self.ask_var, 1)
        self.add_metric(prices, "Last trade", self.last_trade_var, 2)

        for column in range(3):
            prices.columnconfigure(column, weight=1)

        ttk.Label(
            main,
            textvariable=self.status_var,
            font=("Arial", 12)
        ).pack(pady=20)

    def add_metric(self, parent, title, variable, column):
        frame = ttk.LabelFrame(
            parent,
            text=title,
            padding=15
        )
        frame.grid(
            row=0,
            column=column,
            padx=6,
            sticky="nsew"
        )

        ttk.Label(
            frame,
            textvariable=variable,
            font=("Arial", 18, "bold")
        ).pack()

    def validate_symbol(self):
        symbol = self.symbol_var.get().strip().upper()

        if not re.fullmatch(r"[A-Z0-9.\-]{1,15}", symbol):
            messagebox.showwarning(
                "Invalid ticker",
                "Enter a ticker such as AAPL, TSLA, or TQQQ."
            )
            return None

        return symbol

    def start_stream(self):
        symbol = self.validate_symbol()

        if symbol is None:
            return

        self.stop_stream()

        self.current_symbol_var.set(symbol)
        self.bid_var.set("Waiting...")
        self.ask_var.set("Waiting...")
        self.last_trade_var.set("Waiting...")
        self.status_var.set(f"Connecting to {symbol}...")

        new_stream = self.connector.create_quote_stream()

        async def quote_handler(quote):
            self.message_queue.put(
                (
                    "quote",
                    quote.bid_price,
                    quote.bid_size,
                    quote.ask_price,
                    quote.ask_size
                )
            )

        async def trade_handler(trade):
            self.message_queue.put(
                (
                    "trade",
                    trade.price,
                    trade.size
                )
            )

        new_stream.subscribe_quotes(
            quote_handler,
            symbol
        )

        new_stream.subscribe_trades(
            trade_handler,
            symbol
        )

        self.stream = new_stream

        self.stream_thread = threading.Thread(
            target=self.run_stream,
            args=(new_stream, symbol),
            daemon=True
        )

        self.stream_thread.start()

    def run_stream(self, stream, symbol):
        try:
            self.message_queue.put(
                ("status", f"Connected — waiting for {symbol} data")
            )

            stream.run()

        except Exception as error:
            self.message_queue.put(
                ("error", str(error))
            )

    def process_messages(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                message_type = message[0]

                if message_type == "quote":
                    _, bid, bid_size, ask, ask_size = message

                    self.bid_var.set(
                        f"${bid:,.2f}\nSize: {bid_size}"
                        if bid and bid > 0
                        else "Unavailable"
                    )

                    self.ask_var.set(
                        f"${ask:,.2f}\nSize: {ask_size}"
                        if ask and ask > 0
                        else "Unavailable"
                    )

                    self.status_var.set("Receiving live quote data")

                elif message_type == "trade":
                    _, price, size = message

                    self.last_trade_var.set(
                        f"${price:,.2f}\nSize: {size}"
                        if price and price > 0
                        else "Unavailable"
                    )

                elif message_type == "status":
                    self.status_var.set(message[1])

                elif message_type == "error":
                    self.status_var.set("Streaming error")
                    messagebox.showerror(
                        "Streaming error",
                        message[1]
                    )

        except queue.Empty:
            pass

        self.root.after(100, self.process_messages)

    def stop_stream(self):
        if self.stream is not None:
            try:
                self.stream.stop_ws()
            except Exception:
                pass

            self.stream = None

    def close_app(self):
        self.stop_stream()
        self.root.destroy()


root = tk.Tk()
app = RealTimeQuoteApp(root)
root.mainloop()
