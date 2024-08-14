import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import json
import os
import csv
import matplotlib.dates as mdates
import pyttsx3
import threading  # Import threading module

# Replace with your actual API key from Financial Modeling Prep
API_KEY = 'f82jf30vQfR7dXiua70DXVoadssYMBVF'

portfolio = []

# Initialize the text-to-speech engine
engine = pyttsx3.init()

def speak_text(text):
    """Function to handle text-to-speech in a separate thread."""
    def _speak():
        engine.setProperty('rate', 150)  # Set the speaking rate to a slower value
        engine.say(text)
        engine.runAndWait()

    thread = threading.Thread(target=_speak)
    thread.start()

def get_stock_price(symbol):
    try:
        response = requests.get(f'https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={API_KEY}')
        data = response.json()
        if data:
            stock_info = data[0]
            return (stock_info['price'], {
                'company_name': stock_info.get('name', 'N/A'),
                'market_cap': stock_info.get('marketCap', 'N/A'),
                'pe_ratio': stock_info.get('pe', 'N/A')
            })
    except requests.RequestException as e:
        print(f"Request error: {e}")
    return None, None

def get_stock_historical_data(symbol, days=30):
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        response = requests.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={start_date}&to={end_date}&apikey={API_KEY}')
        data = response.json()
        if 'historical' in data:
            return [(entry['date'], entry['close']) for entry in data['historical']]
    except requests.RequestException as e:
        print(f"Request error: {e}")
    return []

def add_stock():
    symbol = symbol_entry.get().upper()
    quantity = int(quantity_entry.get())
    
    price, stock_data = get_stock_price(symbol)
    if price is None:
        messagebox.showerror("Error", f"Stock symbol {symbol} not found.")
        return

    total_value = price * quantity
    portfolio.append({
        'symbol': symbol,
        'quantity': quantity,
        'current_price': price,
        'total_value': total_value,
        'company_name': stock_data.get('company_name', 'N/A'),
        'market_cap': stock_data.get('market_cap', 'N/A'),
        'pe_ratio': stock_data.get('pe_ratio', 'N/A')
    })
    
    # Announce the stock addition using text-to-speech
    announcement = (f"Added {quantity} shares of {symbol} from {stock_data.get('company_name', 'the company')} "
                    f"at ${price:.2f} each. Total value is ${total_value:.2f}.")
    speak_text(announcement)

    messagebox.showinfo("Success", announcement)
    update_portfolio()

def remove_stock():
    symbol = symbol_entry.get().upper()
    global portfolio
    portfolio = [stock for stock in portfolio if stock['symbol'] != symbol]
    messagebox.showinfo("Success", f"Removed all shares of {symbol} from portfolio.")
    update_portfolio()

def clear_all_stocks():
    global portfolio
    portfolio.clear()
    messagebox.showinfo("Success", "All stocks have been cleared from the portfolio.")
    update_portfolio()

def update_portfolio():
    for widget in portfolio_frame.winfo_children():
        widget.destroy()

    if not portfolio:
        label = tk.Label(portfolio_frame, text="Your portfolio is empty.", font=('Helvetica', 12), bg="#f0f0f0", padx=10, pady=10)
        label.pack()
        # Clear and remove the old chart if any
        for widget in chart_frame.winfo_children():
            widget.destroy()
        for widget in performance_chart_frame.winfo_children():
            widget.destroy()
        return

    header = tk.Label(portfolio_frame, text=f"{'Symbol':<10} {'Company Name':<20} {'Quantity':<10} {'Price':<10} {'Total Value':<15} {'Market Cap':<20} {'P/E Ratio':<10} {'Details':<10}", font=('Helvetica', 12, 'bold'), bg="#d3d3d3", padx=10, pady=5)
    header.pack()

    for stock in portfolio:
        symbol = stock.get('symbol', 'N/A')
        company_name = stock.get('company_name', 'N/A')
        quantity = stock.get('quantity', 0)
        current_price = stock.get('current_price', 0.0)
        total_value = stock.get('total_value', 0.0)
        market_cap = stock.get('market_cap', 'N/A')
        pe_ratio = stock.get('pe_ratio', 'N/A')

        stock_text = f"{symbol:<10} {company_name:<20} {quantity:<10} ${current_price:<10.2f} ${total_value:<15.2f} {market_cap:<20} {pe_ratio:<10}"
        label = tk.Label(portfolio_frame, text=stock_text, font=('Helvetica', 12), bg="#f9f9f9", padx=10, pady=5)
        label.pack()

        details_button = ttk.Button(portfolio_frame, text="View Details", command=lambda s=symbol: show_stock_details(s))
        details_button.pack(pady=5)

    create_pie_chart()
    create_stock_performance_chart()

def show_stock_details(symbol):
    data = get_stock_historical_data(symbol)
    if not data:
        messagebox.showerror("Error", f"No historical data found for {symbol}.")
        return

    details_window = tk.Toplevel(root)
    details_window.title(f"Stock Details - {symbol}")

    fig, ax = plt.subplots(figsize=(8, 6))
    dates, prices = zip(*data)
    dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]  # Convert to datetime objects
    ax.plot(dates, prices, label=symbol)
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.set_title(f'{symbol} Historical Performance')
    ax.legend()
    ax.grid(True)
    
    # Format the date axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    canvas = FigureCanvasTkAgg(fig, master=details_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def create_pie_chart():
    for widget in chart_frame.winfo_children():
        widget.destroy()

    fig, ax = plt.subplots(figsize=(6, 4))
    symbols = [stock['symbol'] for stock in portfolio]
    values = [stock['total_value'] for stock in portfolio]

    ax.pie(values, labels=symbols, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def create_stock_performance_chart():
    for widget in performance_chart_frame.winfo_children():
        widget.destroy()

    fig, ax = plt.subplots(figsize=(8, 5))
    for stock in portfolio:
        symbol = stock['symbol']
        data = get_stock_historical_data(symbol)
        if data:
            dates, prices = zip(*data)
            dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]  # Convert to datetime objects
            ax.plot(dates, prices, label=symbol)

    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.set_title('Stock Performance Over Time')
    ax.legend()
    ax.grid(True)

    # Format the date axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    canvas = FigureCanvasTkAgg(fig, master=performance_chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

def save_portfolio():
    with open('portfolio.json', 'w') as f:
        json.dump(portfolio, f)
    messagebox.showinfo("Success", "Portfolio saved successfully.")

def load_portfolio():
    global portfolio
    if os.path.exists('portfolio.json'):
        with open('portfolio.json', 'r') as f:
            portfolio = json.load(f)
        update_portfolio()
    else:
        messagebox.showwarning("Warning", "No saved portfolio found.")

def export_portfolio():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile="portfolio.csv"
    )
    if file_path:
        try:
            with open(file_path, 'w', newline='') as csvfile:
                fieldnames = ['symbol', 'company_name', 'quantity', 'current_price', 'total_value', 'market_cap', 'pe_ratio']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for stock in portfolio:
                    writer.writerow({
                        'symbol': stock.get('symbol', ''),
                        'company_name': stock.get('company_name', ''),
                        'quantity': stock.get('quantity', 0),
                        'current_price': stock.get('current_price', 0.0),
                        'total_value': stock.get('total_value', 0.0),
                        'market_cap': stock.get('market_cap', 'N/A'),
                        'pe_ratio': stock.get('pe_ratio', 'N/A')
                    })
            messagebox.showinfo("Success", f"Portfolio exported to CSV successfully at {file_path}.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while exporting the portfolio: {e}")

def import_portfolio():
    global portfolio
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                portfolio = []
                for row in reader:
                    portfolio.append({
                        'symbol': row['symbol'],
                        'company_name': row['company_name'],
                        'quantity': int(row['quantity']),
                        'current_price': float(row['current_price']),
                        'total_value': float(row['total_value']),
                        'market_cap': row['market_cap'],
                        'pe_ratio': row['pe_ratio']
                    })
            update_portfolio()
            messagebox.showinfo("Success", "Portfolio imported from CSV successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while importing the portfolio: {e}")

def main():
    global symbol_entry, quantity_entry, portfolio_frame, chart_frame, performance_chart_frame

    global root
    root = tk.Tk()
    root.title("Stock Portfolio Tracker")
    root.geometry("1200x900")
    root.resizable(True, True)

    style = ttk.Style()
    style.configure("TLabel", font=("Helvetica", 12))
    style.configure("TButton", font=("Helvetica", 12))
    style.configure("TFrame", background="#e0e0e0")
    
    main_frame = ttk.Frame(root, padding="20", style="TFrame")
    main_frame.pack(fill="both", expand=True)

    input_frame = ttk.Frame(main_frame, padding="10", style="TFrame")
    input_frame.pack(fill="x")

    ttk.Label(input_frame, text="Stock Symbol:", background="#e0e0e0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    symbol_entry = ttk.Entry(input_frame, width=20)
    symbol_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(input_frame, text="Quantity:", background="#e0e0e0").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    quantity_entry = ttk.Entry(input_frame, width=20)
    quantity_entry.grid(row=1, column=1, padx=5, pady=5)

    button_frame = ttk.Frame(main_frame, padding="10", style="TFrame")
    button_frame.pack(fill="x")

    add_button = ttk.Button(button_frame, text="Add Stock", command=add_stock)
    add_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    add_button.configure(style="Accent.TButton")

    remove_button = ttk.Button(button_frame, text="Remove Stock", command=remove_stock)
    remove_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    remove_button.configure(style="Danger.TButton")

    clear_button = ttk.Button(button_frame, text="Clear All Stocks", command=clear_all_stocks)
    clear_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
    clear_button.configure(style="Warning.TButton")

    save_button = ttk.Button(button_frame, text="Save Portfolio", command=save_portfolio)
    save_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
    save_button.configure(style="Success.TButton")

    load_button = ttk.Button(button_frame, text="Load Portfolio", command=load_portfolio)
    load_button.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
    load_button.configure(style="Info.TButton")

    export_button = ttk.Button(button_frame, text="Export to CSV", command=export_portfolio)
    export_button.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
    export_button.configure(style="Success.TButton")

    import_button = ttk.Button(button_frame, text="Import from CSV", command=import_portfolio)
    import_button.grid(row=0, column=6, padx=5, pady=5, sticky="ew")
    import_button.configure(style="Info.TButton")

    portfolio_frame = ttk.Frame(main_frame, padding="10", relief="ridge", borderwidth=2, style="TFrame")
    portfolio_frame.pack(fill="both", expand=True, pady=10)

    chart_frame = ttk.Frame(main_frame, padding="10", relief="ridge", borderwidth=2, style="TFrame")
    chart_frame.pack(fill="both", expand=True, pady=10)

    performance_chart_frame = ttk.Frame(main_frame, padding="10", relief="ridge", borderwidth=2, style="TFrame")
    performance_chart_frame.pack(fill="both", expand=True, pady=10)

    # Add custom styles for buttons with black text color
    style.configure("Accent.TButton", background="#007bff", foreground="black")
    style.configure("Danger.TButton", background="#dc3545", foreground="black")
    style.configure("Warning.TButton", background="#ffc107", foreground="black")
    style.configure("Success.TButton", background="#28a745", foreground="black")
    style.configure("Info.TButton", background="#17a2b8", foreground="black")

    load_portfolio()  # Load portfolio on start

    root.mainloop()

if __name__ == '__main__':
    main()
