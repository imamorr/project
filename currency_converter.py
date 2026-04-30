import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime, timedelta

API_KEY = "ВАШ_API_КЛЮЧ"
BASE_URL = "https://v6.exchangerate-api.com/v6/"
HISTORY_FILE = "conversion_history.json"

cache = {}

def is_cache_valid(timestamp):
    return datetime.now() - timestamp < timedelta(seconds=30)

currency_list = ["USD", "EUR", "RUB"]

def load_currency_list():
    global currency_list
    try:
        url = f"{BASE_URL}{API_KEY}/latest/USD"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data["result"] == "success":
            currency_list = sorted(data["conversion_rates"].keys())
            return currency_list
    except Exception:
        pass
    return currency_list

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, IOError):
            pass
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_exchange_rate(from_currency, to_currency):
    cache_key = (from_currency, to_currency)
    if cache_key in cache and is_cache_valid(cache[cache_key]["timestamp"]):
        return cache[cache_key]["rate"]

    try:
        url = f"{BASE_URL}{API_KEY}/latest/{from_currency}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["result"] == "success":
            rate = data["conversion_rates"].get(to_currency)
            if rate:
                cache[cache_key] = {"rate": rate, "timestamp": datetime.now()}
                return rate
            else:
                raise ValueError(f"Валюта {to_currency} не найдена")
        else:
            raise ValueError("Ошибка API: " + data.get("error-type", "Unknown"))
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось получить курс:\n{e}")
        return None

def convert():
    try:
        amount_str = entry_amount.get().strip().replace(",", ".")
        if not amount_str:
            raise ValueError("Пустое поле")
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")
    except ValueError:
        messagebox.showerror("Ошибка ввода", "Введите положительное число (можно использовать запятую или точку)")
        return

    from_cur = combo_from.get()
    to_cur = combo_to.get()
    if not from_cur or not to_cur:
        messagebox.showerror("Ошибка", "Выберите обе валюты")
        return

    rate = get_exchange_rate(from_cur, to_cur)
    if rate is None:
        return

    converted = amount * rate
    result_text = f"{amount:.2f} {from_cur} = {converted:.2f} {to_cur}"
    label_result.config(text=result_text)

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "from_currency": from_cur,
        "to_currency": to_cur,
        "amount": amount,
        "converted": converted,
        "rate": rate
    }
    history.append(record)
    save_history(history)
    update_history_table()
    entry_amount.delete(0, tk.END)

def update_history_table():
    for row in history_table.get_children():
        history_table.delete(row)
    for rec in history[::-1]:
        history_table.insert("", "end", values=(
            rec["timestamp"],
            f"{rec['amount']} {rec['from_currency']}",
            f"{rec['converted']:.2f} {rec['to_currency']}",
            f"{rec['rate']:.4f}"
        ))

def clear_history():
    if messagebox.askyesno("Подтверждение", "Удалить всю историю конвертаций?"):
        global history
        history = []
        save_history(history)
        update_history_table()

root = tk.Tk()
root.title("Currency Converter")
root.geometry("850x500")
root.resizable(True, True)

try:
    currency_list = load_currency_list()
except:
    currency_list = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "CAD", "CHF", "TRY", "INR", "BRL", "AUD"]

frame_conv = ttk.LabelFrame(root, text="Конвертация", padding=10)
frame_conv.pack(fill="x", padx=10, pady=10)

ttk.Label(frame_conv, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_amount = ttk.Entry(frame_conv, width=15)
entry_amount.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(frame_conv, text="Из валюты:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
combo_from = ttk.Combobox(frame_conv, values=currency_list, width=8, state="readonly")
combo_from.grid(row=0, column=3, padx=5, pady=5)
combo_from.set("USD" if "USD" in currency_list else currency_list[0])

ttk.Label(frame_conv, text="В валюту:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
combo_to = ttk.Combobox(frame_conv, values=currency_list, width=8, state="readonly")
combo_to.grid(row=0, column=5, padx=5, pady=5)
combo_to.set("EUR" if "EUR" in currency_list else currency_list[1] if len(currency_list) > 1 else currency_list[0])

btn_convert = ttk.Button(frame_conv, text="Конвертировать", command=convert)
btn_convert.grid(row=0, column=6, padx=10, pady=5)

label_result = ttk.Label(frame_conv, text="", font=("Arial", 10, "bold"))
label_result.grid(row=1, column=0, columnspan=7, pady=10)

frame_history = ttk.LabelFrame(root, text="История конвертаций", padding=10)
frame_history.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("timestamp", "from_to", "result", "rate")
history_table = ttk.Treeview(frame_history, columns=columns, show="headings")
history_table.heading("timestamp", text="Дата/время")
history_table.heading("from_to", text="Исходная сумма")
history_table.heading("result", text="Результат")
history_table.heading("rate", text="Курс")
history_table.column("timestamp", width=140)
history_table.column("from_to", width=130)
history_table.column("result", width=130)
history_table.column("rate", width=100)

scrollbar = ttk.Scrollbar(frame_history, orient="vertical", command=history_table.yview)
history_table.configure(yscrollcommand=scrollbar.set)
history_table.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

btn_clear = ttk.Button(frame_history, text="Очистить историю", command=clear_history)
btn_clear.pack(pady=5)

history = load_history()
update_history_table()

root.mainloop()
