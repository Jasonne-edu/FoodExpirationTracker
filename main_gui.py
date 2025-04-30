import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import csv
import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import cv2

# File paths
RECORDS_FILE = "food_records.csv"
EXPIRY_DATA_FILE = "food_expiry_data_cleaned.csv"

# 👁️‍🗨️ QR code detector
def scan_qr_and_return_text():
    detector = cv2.QRCodeDetector()
    cap = cv2.VideoCapture(0)
    decoded_data = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        data, bbox, _ = detector.detectAndDecode(frame)
        if data:
            decoded_data = data
            break
        cv2.imshow("Scan QR Code (Press Q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    if decoded_data:
        messagebox.showinfo("QR Code Found", f"Decoded Text: {decoded_data}")
        return decoded_data
    else:
        messagebox.showerror("No QR Code", "No QR code was detected.")
        return None

# 🧠 Load expiration reference data
def load_expiry_database():
    df = pd.read_csv(EXPIRY_DATA_FILE)
    expiry_data = {}
    for _, row in df.iterrows():
        food = row["Name"].strip().lower()
        category = row["Type"].strip().lower()
        expiry_data[(food, category)] = {
            "room_temp": int(row["Room Temp Days"]) if not pd.isna(row["Room Temp Days"]) else None,
            "refrigerated": int(row["Refrigerated Days"]) if not pd.isna(row["Refrigerated Days"]) else None,
            "frozen": int(row["Frozen Days"]) if not pd.isna(row["Frozen Days"]) else None,
            "tip": row["Storage Tip"] if not pd.isna(row["Storage Tip"]) else "No tip available"
        }
    return expiry_data

EXPIRY_DB = load_expiry_database()

if not os.path.exists(RECORDS_FILE):
    with open(RECORDS_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Type", "Storage", "Expiry Date", "Storage Tip"])

# Health tip suggestions
HEALTH_TIPS = [
    "💧 Stay hydrated and eat high-water-content fruits like watermelon.",
    "🍽️ Reduce portion size and avoid overeating at night.",
    "🌾 Choose whole grains and fiber-rich foods.",
    "🥦 Include a variety of vegetables in your meals daily.",
    "⚠️ Always refrigerate leftovers promptly to avoid foodborne illness.",
    "❄️ Do not refreeze foods once thawed.",
    "🧼 Wash your hands and utensils before handling food.",
    "🚫 Avoid raw eggs or unpasteurized milk products.",
    "📅 Always check the expiration date before consuming packaged foods."
]

import random
def random_health_tip():
    return random.choice(HEALTH_TIPS)

# 🔍 Estimate expiration date
def estimate_expiration(name, category, storage_method, custom_days=None):
    name = name.lower().strip()
    category = category.lower().strip()
    key = (name, category)
    if key in EXPIRY_DB:
        days = EXPIRY_DB[key].get(storage_method)
        tip = EXPIRY_DB[key].get("tip", "No tip available")
        if days:
            return (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d"), tip
        else:
            return "Unknown", "No storage recommendation available."
    elif category == "cooked" and custom_days:
        return (datetime.today() + timedelta(days=int(custom_days))).strftime("%Y-%m-%d"), "Refrigerate and consume within a few days."
    else:
        return "Unknown", "No information available."

# 💾 Save a new record
def save_food():
    name = name_entry.get()
    category = category_var.get()
    storage = storage_method_var.get()
    custom_days = custom_days_entry.get()
    if not name or not category or not storage:
        messagebox.showwarning("Missing Info", "Please enter all required fields.")
        return
    expiry_date, tip = estimate_expiration(name, category, storage, custom_days)
    with open(RECORDS_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, category, storage, expiry_date, tip])
    health_msg = random_health_tip()
    messagebox.showinfo("Saved", f"✅ Food saved!\n📅 Expires on: {expiry_date}\n📦 Storage: {tip}\n\n💡Health Tip:\n{health_msg}")

# 🛎️ Show reminders
def check_reminders():
    today = datetime.today()
    reminders = []
    if not os.path.exists(RECORDS_FILE):
        messagebox.showinfo("Reminder", "No food records found.")
        return
    with open(RECORDS_FILE, mode="r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                expiry = datetime.strptime(row["Expiry Date"], "%Y-%m-%d")
                days_left = (expiry - today).days
                if 0 < days_left <= 7:
                    reminders.append(f"{row['Name']} expires in {days_left} day(s)!")
            except ValueError:
                continue
    if reminders:
        messagebox.showinfo("Reminder", "\n".join(reminders))
    else:
        messagebox.showinfo("Reminder", "✅ No upcoming expirations in the next 7 days.")

# 📁 View & Delete records
def open_record_viewer():
    if not os.path.exists(RECORDS_FILE):
        messagebox.showinfo("No Records", "No food records found.")
        return
    view_window = tk.Toplevel(root)
    view_window.title("📄 Food Records Viewer")
    view_window.geometry("700x400")
    tree = ttk.Treeview(view_window, columns=("Name", "Type", "Storage", "Expiry", "Tip"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.pack(fill="both", expand=True)
    with open(RECORDS_FILE, mode="r") as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)
        for row in rows:
            tree.insert("", tk.END, values=row)
    def delete_selected():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Select Item", "Please select a row to delete.")
            return
        values = tree.item(selected_item)["values"]
        rows.remove(values)
        tree.delete(selected_item)
        with open(RECORDS_FILE, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Type", "Storage", "Expiry Date", "Storage Tip"])
            writer.writerows(rows)
        messagebox.showinfo("Deleted", f"Deleted record for {values[0]}.")
    tk.Button(view_window, text="Delete Selected", command=delete_selected, bg="red", fg="white").pack(pady=10)

# 📄 Export to PDF
def export_to_pdf():
    if not os.path.exists(RECORDS_FILE):
        messagebox.showerror("Error", "No records to export.")
        return
    try:
        df = pd.read_csv(RECORDS_FILE)
        c = canvas.Canvas("food_report.pdf", pagesize=letter)
        width, height = letter
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, height - 40, "🍎 Food Expiration Tracker Report")
        c.setFont("Helvetica", 10)
        y = height - 70
        for index, row in df.iterrows():
            text = f"{row['Name']} | {row['Type']} | {row['Storage']} | {row['Expiry Date']} | {row['Storage Tip']}"
            c.drawString(30, y, text)
            y -= 15
            if y < 40:
                c.showPage()
                y = height - 40
        c.save()
        messagebox.showinfo("Exported", "✅ PDF report generated as 'food_report.pdf'")
    except Exception as e:
        messagebox.showerror("Error", f"PDF generation failed:\n{str(e)}")

# 🔄 Autofill from QR
def auto_fill_food_name():
    result = scan_qr_and_return_text()
    if result:
        name_entry.delete(0, tk.END)
        name_entry.insert(0, result)

# 🎨 GUI Layout
root = tk.Tk()
root.title("🍎 Food Expiration Tracker")
root.geometry("420x520")

tk.Label(root, text="Food Name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Button(root, text="📷 Scan QR", command=auto_fill_food_name).pack(pady=5)

tk.Label(root, text="Category:").pack()
category_var = tk.StringVar()
category_menu = ttk.Combobox(root, textvariable=category_var, values=["fresh", "cooked", "canned"])
category_menu.pack()

tk.Label(root, text="Storage Method:").pack()
storage_method_var = tk.StringVar()
storage_method_menu = ttk.Combobox(root, textvariable=storage_method_var, values=["room_temp", "refrigerated", "frozen"])
storage_method_menu.pack()

tk.Label(root, text="If Cooked: Days till expiry (optional):").pack()
custom_days_entry = tk.Entry(root)
custom_days_entry.pack()

tk.Button(root, text="💾 Save Food Record", command=save_food, bg="green", fg="white").pack(pady=5)
tk.Button(root, text="📁 View & Delete Records", command=open_record_viewer, bg="blue", fg="white").pack(pady=5)
tk.Button(root, text="🔔 Check for Reminders", command=check_reminders).pack(pady=5)
tk.Button(root, text="📄 Export to PDF", command=export_to_pdf, bg="purple", fg="white").pack(pady=10)

root.mainloop()
