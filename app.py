import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import math
import os
import sys
import traceback
from datetime import datetime


# ============================================================
# DATABASE SETTINGS
# ============================================================

# Keep the database next to the script so the app works no matter
# from which folder it is launched.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(BASE_DIR, "expenses.db")

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Fees",
    "Others"
]


# ============================================================
# CHART SETTINGS
# ============================================================

CHART_COLORS = {
    "Food": "#FF6B6B",
    "Travel": "#4ECDC4",
    "Shopping": "#FFD166",
    "Fees": "#6C5CE7",
    "Others": "#9B8AFB"
}

CHART_BG = "#FFFFFF"
CHART_GRID = "#EAE7F7"
CHART_AXIS = "#8B8AA3"
CHART_TEXT = "#3D3B5C"
CHART_FONT = "Segoe UI"

TREND_COLORS = [
    "#6C5CE7",
    "#4ECDC4",
    "#FF6B6B",
    "#FFD166",
    "#9B8AFB",
    "#00B894",
    "#E17055",
    "#0984E3"
]

# Any chart problem is written here so it can be inspected even when
# the app was started from VS Code without a visible console.

CHART_LOG = os.path.join(BASE_DIR, "chart_debug.log")


def log_debug(message):
    """
    Append a timestamped line to chart_debug.log.
    """

    try:

        with open(CHART_LOG, "a", encoding="utf-8") as log_file:

            log_file.write(
                f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n"
            )

    except Exception:

        pass


def nice_ceiling(value, steps=5):
    """
    Round a raw maximum up to a friendly axis maximum so that the
    chart gets evenly spaced, readable grid lines.
    """

    if value <= 0:
        return float(steps)

    raw = value / steps

    exponent = math.floor(math.log10(raw))

    base = 10 ** exponent

    for factor in (1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10):

        if raw <= factor * base:

            return factor * base * steps

    return 10 * base * steps


def format_compact(amount):
    """
    Short money format used for axis labels and bar captions.
    """

    amount = float(amount)

    if abs(amount) >= 10000000:
        return f"₹{amount / 10000000:.2f}Cr"

    if abs(amount) >= 100000:
        return f"₹{amount / 100000:.2f}L"

    if abs(amount) >= 1000:
        return f"₹{amount / 1000:.1f}K"

    return f"₹{amount:.0f}"


def connect_database():
    return sqlite3.connect(DATABASE)


def create_database():

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def add_to_database(date, amount, category, description):

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (date, amount, category, description)
        VALUES (?, ?, ?, ?)
    """, (date, amount, category, description))

    connection.commit()
    connection.close()


def get_all_expenses():

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, date, amount, category, description
        FROM expenses
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    connection.close()

    return records


def delete_from_database(expense_id):

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    connection.commit()
    connection.close()


def clear_database():

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM expenses")

    connection.commit()
    connection.close()


# ============================================================
# MAIN APPLICATION
# ============================================================

class ExpenseTracker:

    def __init__(self, root):

        self.root = root

        self.root.title("Personal Expense Tracker")

        self.root.configure(
            bg="#F4F2FF"
        )

        # Chart window state
        self.chart_window = None
        self.chart_canvases = {}
        self.chart_log_scale = tk.BooleanVar(value=False)
        self.chart_use_filter = tk.BooleanVar(value=True)
        self.chart_redraw_job = None

        self.create_styles()

        self.fit_window_to_screen()

        self.create_menu()

        self.create_header()

        self.create_summary()

        self.create_input_section()

        self.create_search_section()

        # Buttons are packed BEFORE the table so they can never be
        # pushed off screen - the table is the only part that shrinks.

        self.create_buttons()

        self.create_table()

        self.create_shortcuts()

        self.refresh_all()

        # Bring the window to the front so the in-app shortcuts
        # (Ctrl+G, Ctrl+M, F5) work immediately instead of being
        # captured by whichever editor had focus.

        self.root.after(200, self.take_focus)


    # ========================================================
    # FOCUS
    # ========================================================

    def take_focus(self):

        try:

            self.root.deiconify()

            self.root.lift()

            self.root.focus_force()

        except tk.TclError:

            pass


    # ========================================================
    # WINDOW SIZING
    # ========================================================

    def fit_window_to_screen(self):
        """
        Size the window so it always fits the visible screen area.

        The taskbar and the window title bar both eat vertical space,
        so we keep a generous margin. On a 1280x720 display this
        produces roughly 1000x580 - safely above the taskbar.
        """

        screen_width = self.root.winfo_screenwidth()

        screen_height = self.root.winfo_screenheight()

        width = min(1060, screen_width - 80)

        height = min(700, screen_height - 140)

        x = max(0, (screen_width - width) // 2)

        y = max(0, (screen_height - height) // 2 - 22)

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

        self.root.minsize(
            min(860, width),
            min(480, height)
        )


    # ========================================================
    # MENU BAR
    # ========================================================

    def create_menu(self):

        menu_bar = tk.Menu(
            self.root
        )


        file_menu = tk.Menu(
            menu_bar,
            tearoff=0
        )

        file_menu.add_command(
            label="Export to CSV...",
            command=self.export_csv
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Exit",
            command=self.root.destroy
        )

        menu_bar.add_cascade(
            label="File",
            menu=file_menu
        )


        view_menu = tk.Menu(
            menu_bar,
            tearoff=0
        )

        view_menu.add_command(
            label="Show Chart          Ctrl+G",
            command=self.show_chart
        )

        view_menu.add_command(
            label="Monthly Summary     Ctrl+M",
            command=self.monthly_summary
        )

        view_menu.add_separator()

        view_menu.add_command(
            label="Refresh             F5",
            command=self.refresh_all
        )

        menu_bar.add_cascade(
            label="View",
            menu=view_menu
        )


        data_menu = tk.Menu(
            menu_bar,
            tearoff=0
        )

        data_menu.add_command(
            label="Add Demo Data",
            command=self.add_demo_data
        )

        data_menu.add_command(
            label="Clear All Data",
            command=self.clear_all
        )

        menu_bar.add_cascade(
            label="Data",
            menu=data_menu
        )


        help_menu = tk.Menu(
            menu_bar,
            tearoff=0
        )

        help_menu.add_command(
            label="About",
            command=self.show_about
        )

        menu_bar.add_cascade(
            label="Help",
            menu=help_menu
        )


        self.root.config(
            menu=menu_bar
        )


    # ========================================================
    # KEYBOARD SHORTCUTS
    # ========================================================

    def create_shortcuts(self):

        self.root.bind(
            "<Control-g>",
            lambda event: self.show_chart()
        )

        self.root.bind(
            "<Control-G>",
            lambda event: self.show_chart()
        )

        self.root.bind(
            "<Control-m>",
            lambda event: self.monthly_summary()
        )

        self.root.bind(
            "<F5>",
            lambda event: self.refresh_all()
        )


    def show_about(self):

        messagebox.showinfo(
            "About",
            "Personal Expense Tracker\n\n"
            "Keep track of your daily expenses and\n"
            "view category and monthly charts.\n\n"
            "Shortcuts:\n"
            "  Ctrl+G  - Show charts\n"
            "  Ctrl+M  - Monthly summary\n"
            "  F5      - Refresh table"
        )


    # ========================================================
    # STYLES
    # ========================================================

    def create_styles(self):

        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "Treeview",
            rowheight=28,
            font=("Arial", 10)
        )

        style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold")
        )

        style.configure(
            "TButton",
            font=("Arial", 10, "bold"),
            padding=5
        )


    # ========================================================
    # HEADER
    # ========================================================

    def create_header(self):

        header = tk.Frame(
            self.root,
            bg="#6C5CE7",
            height=70
        )

        header.pack(
            fill="x"
        )

        title = tk.Label(
            header,
            text="PERSONAL EXPENSE TRACKER",
            bg="#6C5CE7",
            fg="white",
            font=("Arial", 21, "bold")
        )

        title.pack(
            pady=(8, 1)
        )

        subtitle = tk.Label(
            header,
            text="Manage your daily expenses easily",
            bg="#6C5CE7",
            fg="white",
            font=("Arial", 10)
        )

        subtitle.pack()


    # ========================================================
    # SUMMARY CARDS
    # ========================================================

    def create_summary(self):

        summary_frame = tk.Frame(
            self.root,
            bg="#F4F2FF"
        )

        summary_frame.pack(
            fill="x",
            padx=15,
            pady=8
        )

        self.summary_labels = {}

        summary_items = [
            "Total",
            "Food",
            "Travel",
            "Shopping",
            "Fees",
            "Others"
        ]

        for i, item in enumerate(summary_items):

            summary_frame.columnconfigure(
                i,
                weight=1
            )

            card = tk.Frame(
                summary_frame,
                bg="white",
                bd=1,
                relief="solid"
            )

            card.grid(
                row=0,
                column=i,
                padx=4,
                sticky="nsew"
            )

            tk.Label(
                card,
                text=item,
                bg="white",
                fg="#555555",
                font=("Arial", 10, "bold")
            ).pack(
                pady=(8, 2)
            )

            value = tk.Label(
                card,
                text="₹0.00",
                bg="white",
                fg="#6C5CE7",
                font=("Arial", 14, "bold")
            )

            value.pack(
                pady=(0, 6)
            )

            self.summary_labels[item] = value


    # ========================================================
    # ADD EXPENSE SECTION
    # ========================================================

    def create_input_section(self):

        input_frame = tk.LabelFrame(
            self.root,
            text=" Add New Expense ",
            bg="#F4F2FF",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=6
        )

        input_frame.pack(
            fill="x",
            padx=15,
            pady=4
        )


        # DATE

        tk.Label(
            input_frame,
            text="Date",
            bg="#F4F2FF"
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )

        self.date_entry = ttk.Entry(
            input_frame,
            width=15
        )

        self.date_entry.grid(
            row=0,
            column=1,
            padx=5
        )

        self.date_entry.insert(
            0,
            datetime.now().strftime("%d-%m-%Y")
        )


        # AMOUNT

        tk.Label(
            input_frame,
            text="Amount",
            bg="#F4F2FF"
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        self.amount_entry = ttk.Entry(
            input_frame,
            width=15
        )

        self.amount_entry.grid(
            row=0,
            column=3,
            padx=5
        )


        # CATEGORY

        tk.Label(
            input_frame,
            text="Category",
            bg="#F4F2FF"
        ).grid(
            row=0,
            column=4,
            padx=5
        )

        self.category_combo = ttk.Combobox(
            input_frame,
            values=CATEGORIES,
            state="readonly",
            width=15
        )

        self.category_combo.grid(
            row=0,
            column=5,
            padx=5
        )

        self.category_combo.set("Food")


        # DESCRIPTION

        tk.Label(
            input_frame,
            text="Description",
            bg="#F4F2FF"
        ).grid(
            row=0,
            column=6,
            padx=5
        )

        self.description_entry = ttk.Entry(
            input_frame,
            width=25
        )

        self.description_entry.grid(
            row=0,
            column=7,
            padx=5
        )


        # ADD BUTTON

        ttk.Button(
            input_frame,
            text="➕ Add Expense",
            command=self.add_expense
        ).grid(
            row=0,
            column=8,
            padx=10
        )


    # ========================================================
    # SEARCH SECTION
    # ========================================================

    def create_search_section(self):

        search_frame = tk.Frame(
            self.root,
            bg="#F4F2FF"
        )

        search_frame.pack(
            fill="x",
            padx=15,
            pady=6
        )


        tk.Label(
            search_frame,
            text="Search Expense:",
            bg="#F4F2FF",
            font=("Arial", 10, "bold")
        ).pack(
            side="left"
        )


        self.search_entry = ttk.Entry(
            search_frame,
            width=30
        )

        self.search_entry.pack(
            side="left",
            padx=7
        )


        # SEARCH BUTTON

        ttk.Button(
            search_frame,
            text="🔍 Search",
            command=self.search_expense
        ).pack(
            side="left",
            padx=3
        )


        # SHOW ALL BUTTON

        ttk.Button(
            search_frame,
            text="🔄 Show All",
            command=self.refresh_all
        ).pack(
            side="left",
            padx=3
        )


        tk.Label(
            search_frame,
            text="Filter Category:",
            bg="#F4F2FF",
            font=("Arial", 10, "bold")
        ).pack(
            side="left",
            padx=(25, 5)
        )


        self.filter_combo = ttk.Combobox(
            search_frame,
            values=["All"] + CATEGORIES,
            state="readonly",
            width=15
        )

        self.filter_combo.pack(
            side="left"
        )

        self.filter_combo.set("All")


        self.filter_combo.bind(
            "<<ComboboxSelected>>",
            self.filter_category
        )


        # PRESS ENTER TO SEARCH

        self.search_entry.bind(
            "<Return>",
            lambda event: self.search_expense()
        )


    # ========================================================
    # TABLE
    # ========================================================

    def create_table(self):

        table_frame = tk.Frame(
            self.root,
            bg="#F4F2FF"
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=5
        )


        columns = (
            "ID",
            "Date",
            "Amount",
            "Category",
            "Description"
        )


        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )


        self.tree.heading(
            "ID",
            text="ID"
        )

        self.tree.heading(
            "Date",
            text="Date"
        )

        self.tree.heading(
            "Amount",
            text="Amount"
        )

        self.tree.heading(
            "Category",
            text="Category"
        )

        self.tree.heading(
            "Description",
            text="Description"
        )


        self.tree.column(
            "ID",
            width=60,
            anchor="center"
        )

        self.tree.column(
            "Date",
            width=130,
            anchor="center"
        )

        self.tree.column(
            "Amount",
            width=120,
            anchor="center"
        )

        self.tree.column(
            "Category",
            width=150,
            anchor="center"
        )

        self.tree.column(
            "Description",
            width=400
        )


        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )


        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )


    # ========================================================
    # BOTTOM BUTTONS
    # ========================================================

    def create_buttons(self):

        button_frame = tk.Frame(
            self.root,
            bg="#F4F2FF"
        )

        button_frame.pack(
            fill="x",
            padx=15,
            pady=8
        )


        ttk.Button(
            button_frame,
            text="🗑 Delete Selected",
            command=self.delete_selected
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            button_frame,
            text="📊 Show Chart",
            command=self.show_chart
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            button_frame,
            text="📅 Monthly Summary",
            command=self.monthly_summary
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            button_frame,
            text="📁 Export CSV",
            command=self.export_csv
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            button_frame,
            text="🧪 Add Demo Data",
            command=self.add_demo_data
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            button_frame,
            text="🧹 Clear All",
            command=self.clear_all
        ).pack(
            side="left",
            padx=3
        )


        ttk.Button(
            button_frame,
            text="❌ Exit",
            command=self.root.destroy
        ).pack(
            side="right",
            padx=3
        )


    # ========================================================
    # ADD EXPENSE
    # ========================================================

    def add_expense(self):

        date = self.date_entry.get().strip()

        amount = self.amount_entry.get().strip()

        category = self.category_combo.get().strip()

        description = self.description_entry.get().strip()


        # DATE VALIDATION

        try:

            datetime.strptime(
                date,
                "%d-%m-%Y"
            )

        except ValueError:

            messagebox.showerror(
                "Invalid Date",
                "Please enter date in DD-MM-YYYY format."
            )

            return


        # AMOUNT VALIDATION

        try:

            amount_value = float(amount)

            if amount_value <= 0:

                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Invalid Amount",
                "Please enter a valid amount greater than 0."
            )

            return


        # CATEGORY VALIDATION

        if category not in CATEGORIES:

            messagebox.showerror(
                "Invalid Category",
                "Please select a category."
            )

            return


        # DESCRIPTION VALIDATION

        if not description:

            messagebox.showerror(
                "Missing Description",
                "Please enter a description."
            )

            return


        # SAVE

        add_to_database(
            date,
            amount_value,
            category,
            description
        )


        messagebox.showinfo(
            "Success",
            "Expense added successfully!"
        )


        # CLEAR INPUTS

        self.amount_entry.delete(
            0,
            tk.END
        )

        self.description_entry.delete(
            0,
            tk.END
        )


        self.refresh_all()


    # ========================================================
    # REFRESH / SHOW ALL
    # ========================================================

    def refresh_all(self):

        self.search_entry.delete(
            0,
            tk.END
        )

        self.filter_combo.set(
            "All"
        )

        records = get_all_expenses()

        self.load_table(
            records
        )

        self.update_summary()

        # Keep an open chart window in sync with the table

        if self.chart_window is not None and self.chart_window.winfo_exists():

            self.refresh_charts()


    # ========================================================
    # LOAD TABLE
    # ========================================================

    def load_table(self, records):

        for item in self.tree.get_children():

            self.tree.delete(item)


        for record in records:

            self.tree.insert(
                "",
                tk.END,
                values=(
                    record[0],
                    record[1],
                    f"₹{record[2]:.2f}",
                    record[3],
                    record[4]
                )
            )


    # ========================================================
    # UPDATE SUMMARY
    # ========================================================

    def update_summary(self):

        records = get_all_expenses()


        totals = {
            "Total": 0,
            "Food": 0,
            "Travel": 0,
            "Shopping": 0,
            "Fees": 0,
            "Others": 0
        }


        for record in records:

            amount = record[2]

            category = record[3]

            totals["Total"] += amount


            if category in totals:

                totals[category] += amount


        for key in totals:

            self.summary_labels[key].config(
                text=f"₹{totals[key]:.2f}"
            )


    # ========================================================
    # SEARCH EXPENSE
    # ========================================================

    def search_expense(self):

        keyword = self.search_entry.get().strip().lower()


        # Empty search = show everything

        if keyword == "":

            self.load_table(
                get_all_expenses()
            )

            if self.chart_window is not None and self.chart_window.winfo_exists():

                self.refresh_charts()

            return


        records = get_all_expenses()

        matching_records = []


        # SEARCH THROUGH EVERY FIELD

        for record in records:

            record_id = str(
                record[0]
            ).lower()

            record_date = str(
                record[1]
            ).lower()

            record_amount = str(
                record[2]
            ).lower()

            record_category = str(
                record[3]
            ).lower()

            record_description = str(
                record[4]
            ).lower()


            if (
                keyword in record_id
                or keyword in record_date
                or keyword in record_amount
                or keyword in record_category
                or keyword in record_description
            ):

                matching_records.append(
                    record
                )


        # DISPLAY SEARCH RESULTS

        self.load_table(
            matching_records
        )

        if self.chart_window is not None and self.chart_window.winfo_exists():

            self.refresh_charts()


        # NO RESULTS

        if len(matching_records) == 0:

            messagebox.showinfo(
                "Search Result",
                f"No expense found for '{keyword}'."
            )


    # ========================================================
    # CATEGORY FILTER
    # ========================================================

    def filter_category(self, event=None):

        category = self.filter_combo.get()


        if category == "All":

            self.load_table(
                get_all_expenses()
            )

            if self.chart_window is not None and self.chart_window.winfo_exists():

                self.refresh_charts()

            return


        records = get_all_expenses()


        filtered_records = []


        for record in records:

            if record[3] == category:

                filtered_records.append(
                    record
                )


        self.load_table(
            filtered_records
        )

        if self.chart_window is not None and self.chart_window.winfo_exists():

            self.refresh_charts()


    # ========================================================
    # DELETE SELECTED
    # ========================================================

    def delete_selected(self):

        selected = self.tree.selection()


        if not selected:

            messagebox.showwarning(
                "No Selection",
                "Please select an expense from the table first."
            )

            return


        item = self.tree.item(
            selected[0]
        )


        values = item["values"]


        if not values:

            messagebox.showwarning(
                "No Selection",
                "That row has no usable data."
            )

            return


        # Treeview always returns strings, but the id column is an
        # INTEGER PRIMARY KEY - cast it back so the delete always matches.

        expense_id = values[0]

        try:

            expense_id = int(expense_id)

        except (TypeError, ValueError):

            pass


        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete expense ID {expense_id}?"
        )


        if confirm:

            delete_from_database(
                expense_id
            )


            messagebox.showinfo(
                "Deleted",
                "Expense deleted successfully."
            )


            self.refresh_all()


    # ========================================================
    # CLEAR ALL
    # ========================================================

    def clear_all(self):

        records = get_all_expenses()


        if not records:

            messagebox.showinfo(
                "No Data",
                "There are no expenses to delete."
            )

            return


        confirm = messagebox.askyesno(
            "Clear All Data",
            "Are you sure you want to delete ALL expenses?"
        )


        if confirm:

            clear_database()


            messagebox.showinfo(
                "Success",
                "All expenses have been deleted."
            )


            self.refresh_all()


    # ========================================================
    # DEMO DATA
    # ========================================================

    def add_demo_data(self):

        today = datetime.now().strftime(
            "%d-%m-%Y"
        )


        demo_records = [

            (
                today,
                150,
                "Food",
                "Lunch"
            ),

            (
                today,
                80,
                "Travel",
                "Bus fare"
            ),

            (
                today,
                500,
                "Shopping",
                "Clothes"
            ),

            (
                today,
                1000,
                "Fees",
                "College fees"
            ),

            (
                today,
                200,
                "Others",
                "Stationery"
            )
        ]


        for record in demo_records:

            add_to_database(
                record[0],
                record[1],
                record[2],
                record[3]
            )


        messagebox.showinfo(
            "Demo Data",
            "Demo expenses added successfully!"
        )


        self.refresh_all()


    # ========================================================
    # MONTHLY SUMMARY
    # ========================================================

    def monthly_summary(self):

        records = get_all_expenses()


        buckets = {}


        for record in records:

            try:

                expense_date = datetime.strptime(
                    record[1],
                    "%d-%m-%Y"
                )

            except (ValueError, TypeError):

                continue


            key = expense_date.strftime("%m-%Y")


            if key not in buckets:

                buckets[key] = {
                    "label": expense_date.strftime("%B %Y"),
                    "total": 0.0,
                    "count": 0
                }


            buckets[key]["total"] += record[2]

            buckets[key]["count"] += 1


        if not buckets:

            messagebox.showinfo(
                "Monthly Summary",
                "There are no expenses yet."
            )

            return


        current_month = datetime.now().strftime(
            "%m-%Y"
        )


        # Show the current month, but fall back to the newest month
        # that actually has data instead of showing a useless zero.

        if current_month in buckets:

            key = current_month

        else:

            key = max(
                buckets,
                key=lambda month: datetime.strptime(
                    month,
                    "%m-%Y"
                )
            )


        data = buckets[key]


        message = (
            f"Month: {data['label']}\n\n"
            f"Number of Expenses: {data['count']}\n"
            f"Total Spent: ₹{data['total']:,.2f}"
        )


        if key != current_month:

            message += (
                "\n\n(No expenses recorded in the current month,"
                "\nso the latest month with data is shown.)"
            )


        messagebox.showinfo(
            "Monthly Summary",
            message
        )


    # ========================================================
    # EXPORT CSV
    # ========================================================

    def export_csv(self):

        records = get_all_expenses()


        if not records:

            messagebox.showwarning(
                "No Data",
                "There are no expenses to export."
            )

            return


        file_path = filedialog.asksaveasfilename(

            defaultextension=".csv",

            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ],

            title="Save Expense Report"
        )


        if not file_path:

            return


        try:

            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(
                    file
                )


                writer.writerow([
                    "ID",
                    "Date",
                    "Amount",
                    "Category",
                    "Description"
                ])


                for record in records:

                    writer.writerow(
                        record
                    )


            messagebox.showinfo(
                "Export Successful",
                "Expense data exported successfully!"
            )


        except Exception as error:

            messagebox.showerror(
                "Export Error",
                str(error)
            )


    # ========================================================
    # CHART WINDOW
    # ========================================================

    def show_chart(self):
        """
        Safe entry point for opening the chart window. Any failure is
        reported to the user and written to chart_debug.log instead of
        silently showing a blank window.
        """

        try:

            self.build_chart_window()

        except Exception as error:

            log_debug(
                f"show_chart failed: {error}\n{traceback.format_exc()}"
            )

            if self.chart_window is not None:

                try:

                    self.chart_window.destroy()

                except Exception:

                    pass

                self.chart_window = None

                self.chart_canvases = {}

            messagebox.showerror(
                "Chart Error",
                "Could not open the chart window.\n\n"
                f"{error}\n\n"
                "Technical details were saved to:\n"
                f"{CHART_LOG}"
            )


    def build_chart_window(self):

        # Reuse the window if it is already open

        if self.chart_window is not None and self.chart_window.winfo_exists():

            self.chart_window.deiconify()

            self.chart_window.lift()

            self.chart_window.focus_force()

            self.refresh_charts()

            return


        chart_window = tk.Toplevel(self.root)

        chart_window.title("Expense Analytics")

        chart_window.configure(bg=CHART_BG)

        chart_window.transient(self.root)


        # Keep the chart window inside the visible screen area

        screen_width = self.root.winfo_screenwidth()

        screen_height = self.root.winfo_screenheight()

        chart_width = min(980, screen_width - 80)

        chart_height = min(640, screen_height - 140)


        chart_window.geometry(
            f"{chart_width}x{chart_height}"
            f"+{max(0, (screen_width - chart_width) // 2)}"
            f"+{max(0, (screen_height - chart_height) // 2 - 20)}"
        )

        chart_window.minsize(
            min(840, chart_width),
            min(520, chart_height)
        )

        self.chart_window = chart_window

        self.chart_canvases = {}


        # ---------- TITLE ROW ----------

        title_row = tk.Frame(
            chart_window,
            bg=CHART_BG
        )

        title_row.pack(
            fill="x",
            padx=18,
            pady=(16, 8)
        )


        tk.Label(
            title_row,
            text="Expense Analytics",
            bg=CHART_BG,
            fg=CHART_TEXT,
            font=("Arial", 18, "bold")
        ).pack(
            side="left"
        )


        self.chart_info_label = tk.Label(
            title_row,
            text="",
            bg=CHART_BG,
            fg="#6C5CE7",
            font=("Arial", 11, "bold")
        )

        self.chart_info_label.pack(
            side="right"
        )


        # ---------- TABS ----------

        notebook = ttk.Notebook(
            chart_window
        )

        notebook.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 10)
        )


        tabs = [
            ("Category Chart", "bar"),
            ("Pie Chart", "pie"),
            ("Monthly Trend", "trend")
        ]

        for tab_name, key in tabs:

            tab_frame = tk.Frame(
                notebook,
                bg=CHART_BG
            )

            notebook.add(
                tab_frame,
                text=tab_name
            )

            canvas = tk.Canvas(
                tab_frame,
                bg=CHART_BG,
                highlightthickness=0
            )

            canvas.pack(
                fill="both",
                expand=True,
                padx=10,
                pady=10
            )

            canvas.bind(
                "<Configure>",
                self.schedule_chart_redraw
            )

            self.chart_canvases[key] = canvas


        notebook.bind(
            "<<NotebookTabChanged>>",
            self.on_chart_tab_changed
        )


        # ---------- CONTROLS ----------

        control_row = tk.Frame(
            chart_window,
            bg=CHART_BG
        )

        control_row.pack(
            fill="x",
            padx=18,
            pady=(0, 14)
        )


        ttk.Checkbutton(
            control_row,
            text="Log scale (make small categories visible)",
            variable=self.chart_log_scale,
            command=self.refresh_charts
        ).pack(
            side="left"
        )


        ttk.Checkbutton(
            control_row,
            text="Use current filter / search",
            variable=self.chart_use_filter,
            command=self.refresh_charts
        ).pack(
            side="left",
            padx=18
        )


        ttk.Button(
            control_row,
            text="🔄 Refresh Charts",
            command=self.refresh_charts
        ).pack(
            side="left"
        )


        ttk.Button(
            control_row,
            text="❌ Close",
            command=self.close_chart
        ).pack(
            side="right"
        )


        chart_window.protocol(
            "WM_DELETE_WINDOW",
            self.close_chart
        )


        # ---------- FORCE TO FRONT ----------
        #
        # Some Windows setups (high DPI scaling, windowed VS Code)
        # create the window behind the main window, which looks like
        # "the chart does not open". A short topmost pulse fixes that.

        chart_window.deiconify()

        chart_window.update_idletasks()

        chart_window.lift()

        chart_window.focus_force()


        def release_topmost():

            try:

                if chart_window.winfo_exists():

                    chart_window.attributes(
                        "-topmost",
                        False
                    )

            except tk.TclError:

                pass


        try:

            chart_window.attributes(
                "-topmost",
                True
            )

            chart_window.after(
                600,
                release_topmost
            )

        except tk.TclError:

            pass


        log_debug(
            f"chart opened: python={sys.version.split()[0]} "
            f"tk={tk.TkVersion} "
            f"screen={screen_width}x{screen_height} "
            f"scaling={self.root.tk.call('tk', 'scaling'):.2f} "
            f"window={chart_width}x{chart_height} "
            f"records={len(get_all_expenses())}"
        )


        # Draw as soon as the window is on screen

        chart_window.after(
            120,
            self.refresh_charts
        )


    # ========================================================
    # CLOSE CHART WINDOW
    # ========================================================

    def close_chart(self):

        if self.chart_window is not None and self.chart_window.winfo_exists():

            self.chart_window.destroy()

        self.chart_window = None

        self.chart_canvases = {}


    # ========================================================
    # CHART REDRAW HELPERS
    # ========================================================

    def schedule_chart_redraw(self, event=None):

        if self.chart_redraw_job is not None:

            try:

                self.root.after_cancel(
                    self.chart_redraw_job
                )

            except Exception:

                pass


        self.chart_redraw_job = self.root.after(
            120,
            self.refresh_charts
        )


    def on_chart_tab_changed(self, event=None):

        self.schedule_chart_redraw()


    def refresh_charts(self):

        self.chart_redraw_job = None

        if self.chart_window is None or not self.chart_window.winfo_exists():

            return


        records = self.get_chart_records()

        totals = self.get_chart_totals(records)

        total_amount = sum(totals.values())

        if totals:

            top_category = max(
                totals,
                key=totals.get
            )

            self.chart_info_label.config(
                text=(
                    f"Total: ₹{total_amount:,.2f}   |   "
                    f"Records: {len(records)}   |   "
                    f"Top: {top_category}"
                )
            )

        else:

            self.chart_info_label.config(
                text="Total: ₹0.00   |   Records: 0"
            )


        chart_jobs = (
            ("bar", "Category chart", self.draw_bar_chart),
            ("pie", "Pie chart", self.draw_pie_chart),
            ("trend", "Monthly trend", self.draw_trend_chart)
        )


        for key, title, draw in chart_jobs:

            canvas = self.chart_canvases.get(key)

            if canvas is None:

                continue

            try:

                draw(canvas)

            except Exception as error:

                # Never leave a silent blank canvas behind.

                log_debug(
                    f"{key} chart failed: {error}\n"
                    f"{traceback.format_exc()}"
                )

                self.draw_error_chart(
                    canvas,
                    title,
                    error
                )


    # ========================================================
    # CHART DATA
    # ========================================================

    def get_chart_records(self):
        """
        Records used for the charts. When the filter option is on,
        the current category filter and search keyword are applied.
        """

        records = get_all_expenses()

        if not self.chart_use_filter.get():

            return records


        category = self.filter_combo.get()

        keyword = self.search_entry.get().strip().lower()


        if category == "All" and keyword == "":

            return records


        filtered = []

        for record in records:

            if category != "All" and record[3] != category:

                continue


            if keyword:

                haystack = " ".join(
                    str(value).lower()
                    for value in record[1:]
                )

                if keyword not in haystack:

                    continue


            filtered.append(record)


        return filtered


    def get_chart_totals(self, records):
        """
        Category wise total of the given records.
        """

        totals = {
            category: 0.0
            for category in CATEGORIES
        }


        for record in records:

            category = record[3]

            amount = record[2]


            if category not in totals:

                totals[category] = 0.0


            totals[category] += amount


        # Drop empty categories so the chart stays clean

        return {
            category: amount
            for category, amount in totals.items()
            if amount > 0
        }


    def get_monthly_totals(self, records):
        """
        Month wise totals, sorted from oldest to newest.
        """

        buckets = {}


        for record in records:

            try:

                expense_date = datetime.strptime(
                    record[1],
                    "%d-%m-%Y"
                )

            except (ValueError, TypeError):

                continue


            key = expense_date.strftime("%m-%Y")

            if key not in buckets:

                buckets[key] = {
                    "label": expense_date.strftime("%b %Y"),
                    "amount": 0.0,
                    "count": 0
                }


            buckets[key]["amount"] += record[2]

            buckets[key]["count"] += 1


        ordered = sorted(
            buckets.items(),
            key=lambda item: datetime.strptime(
                item[0],
                "%m-%Y"
            )
        )


        return [
            (
                data["label"],
                data["amount"],
                data["count"]
            )
            for key, data in ordered
        ]


    # ========================================================
    # DRAWING HELPERS
    # ========================================================

    def get_canvas_size(self, canvas):

        width = canvas.winfo_width()

        height = canvas.winfo_height()


        if width < 100 or height < 100:

            width = canvas.winfo_reqwidth()

            height = canvas.winfo_reqheight()


        if width < 100 or height < 100:

            width = 900

            height = 420


        return width, height


    def draw_empty_chart(self, canvas, message):

        canvas.delete("all")

        width, height = self.get_canvas_size(canvas)

        canvas.create_text(
            width / 2,
            height / 2 - 12,
            text=message,
            font=(CHART_FONT, 14, "bold"),
            fill=CHART_AXIS
        )

        canvas.create_text(
            width / 2,
            height / 2 + 16,
            text="Use 'Add Demo Data' or add an expense to get started.",
            font=(CHART_FONT, 10),
            fill="#AAAAAA"
        )


    def draw_error_chart(self, canvas, title, error):
        """
        Show the failure reason on the canvas so it is visible even
        when the app runs without a console (e.g. inside VS Code).
        """

        try:

            canvas.delete("all")

        except Exception:

            return

        width, height = self.get_canvas_size(canvas)

        canvas.create_text(
            width / 2,
            height / 2 - 30,
            text=f"{title} could not be drawn",
            font=(CHART_FONT, 14, "bold"),
            fill="#C0392B"
        )

        canvas.create_text(
            width / 2,
            height / 2 + 2,
            text=f"{type(error).__name__}: {error}",
            font=(CHART_FONT, 10),
            fill=CHART_TEXT,
            width=max(200, width - 80)
        )

        canvas.create_text(
            width / 2,
            height / 2 + 60,
            text=f"Details saved to: {CHART_LOG}",
            font=(CHART_FONT, 9),
            fill=CHART_AXIS
        )


    def draw_axis_label(self, canvas, x, y, text, anchor="center", color=CHART_AXIS, size=9, bold=False):

        canvas.create_text(
            x,
            y,
            text=text,
            anchor=anchor,
            font=(
                CHART_FONT,
                size,
                "bold" if bold else "normal"
            ),
            fill=color
        )


    # ========================================================
    # CATEGORY BAR CHART
    # ========================================================

    def draw_bar_chart(self, canvas):

        canvas.delete("all")

        width, height = self.get_canvas_size(canvas)

        records = self.get_chart_records()

        totals = self.get_chart_totals(records)


        if not totals:

            self.draw_empty_chart(
                canvas,
                "No expense data to plot"
            )

            return


        total_amount = sum(totals.values())

        max_amount = max(totals.values())


        left = 86
        right = 26
        top = 44
        bottom = 76

        plot_width = width - left - right

        plot_height = height - top - bottom


        if plot_width <= 60 or plot_height <= 60:

            return


        axis_max = nice_ceiling(max_amount)

        use_log = self.chart_log_scale.get()


        # ------- HEADER LINE -------

        self.draw_axis_label(
            canvas,
            left,
            18,
            (
                f"Category wise spending   |   "
                f"Axis max ₹{axis_max:,.0f}"
                + ("   |   LOG SCALE" if use_log else "")
            ),
            anchor="w",
            color="#6C5CE7",
            size=10,
            bold=True
        )


        # ------- GRID LINES + Y AXIS LABELS -------

        steps = 5

        for i in range(steps + 1):

            fraction = i / steps

            y = top + plot_height - fraction * plot_height

            canvas.create_line(
                left,
                y,
                left + plot_width,
                y,
                fill=CHART_GRID,
                width=1
            )

            self.draw_axis_label(
                canvas,
                left - 10,
                y,
                format_compact(axis_max * fraction),
                anchor="e"
            )


        # ------- AXES -------

        canvas.create_line(
            left,
            top,
            left,
            top + plot_height,
            fill=CHART_AXIS,
            width=2
        )

        canvas.create_line(
            left,
            top + plot_height,
            left + plot_width,
            top + plot_height,
            fill=CHART_AXIS,
            width=2
        )


        # ------- BARS -------

        categories = list(totals.keys())

        slot = plot_width / len(categories)

        bar_width = max(18, min(96, slot * 0.55))

        if use_log and max_amount > 0:

            denominator = math.log10(max_amount + 1)

            def height_fraction(amount):

                return (
                    math.log10(amount + 1) / denominator
                    if denominator
                    else 0
                )

        else:

            def height_fraction(amount):

                return amount / axis_max if axis_max else 0


        baseline = top + plot_height


        for index, category in enumerate(categories):

            amount = totals[category]

            fraction = height_fraction(amount)

            # Never let a real category collapse into an invisible
            # sliver - the exact value is printed above the bar.

            bar_height = max(fraction * plot_height, 10)

            center_x = left + slot * (index + 0.5)

            x1 = center_x - bar_width / 2

            x2 = center_x + bar_width / 2

            y1 = baseline - bar_height

            color = CHART_COLORS.get(
                category,
                "#6C5CE7"
            )


            # BAR BODY

            canvas.create_rectangle(
                x1,
                y1,
                x2,
                baseline,
                fill=color,
                outline="",
                tags=("bar",)
            )


            # VALUE ON TOP

            self.draw_axis_label(
                canvas,
                center_x,
                y1 - 14,
                format_compact(amount),
                color=CHART_TEXT,
                size=10,
                bold=True
            )


            # PERCENTAGE UNDER THE BAR

            percentage = (
                amount / total_amount * 100
                if total_amount
                else 0
            )

            self.draw_axis_label(
                canvas,
                center_x,
                baseline + 18,
                f"{percentage:.1f}%",
                size=9
            )


            # CATEGORY NAME

            self.draw_axis_label(
                canvas,
                center_x,
                baseline + 40,
                category,
                color=CHART_TEXT,
                size=11,
                bold=True
            )


        # ------- FOOTER -------

        self.draw_axis_label(
            canvas,
            left,
            height - 14,
            (
                f"Total ₹{total_amount:,.2f}   |   "
                f"Entries {len(records)}   |   "
                "Tip: enable log scale to compare small categories"
            ),
            anchor="w",
            size=9
        )


    # ========================================================
    # PIE CHART
    # ========================================================

    def draw_pie_chart(self, canvas):

        canvas.delete("all")

        width, height = self.get_canvas_size(canvas)

        records = self.get_chart_records()

        totals = self.get_chart_totals(records)


        if not totals:

            self.draw_empty_chart(
                canvas,
                "No expense data to plot"
            )

            return


        total_amount = sum(totals.values())

        legend_width = 250

        area_width = width - legend_width

        center_x = area_width / 2

        center_y = height / 2

        radius = max(
            40,
            min(area_width, height) / 2 - 46
        )


        self.draw_axis_label(
            canvas,
            20,
            18,
            "Category share of total spending",
            anchor="w",
            color="#6C5CE7",
            size=10,
            bold=True
        )


        # ------- PIE SLICES -------

        start_angle = 90.0

        for category, amount in totals.items():

            fraction = amount / total_amount if total_amount else 0

            extent = fraction * 360

            if extent >= 360:

                extent = 359.9


            color = CHART_COLORS.get(
                category,
                "#6C5CE7"
            )


            canvas.create_arc(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                start=start_angle,
                extent=-extent,
                fill=color,
                outline="white",
                width=2,
                style="pieslice"
            )


            start_angle -= extent


        # ------- CENTRE TEXT -------

        canvas.create_oval(
            center_x - radius * 0.42,
            center_y - radius * 0.42,
            center_x + radius * 0.42,
            center_y + radius * 0.42,
            fill=CHART_BG,
            outline=""
        )

        self.draw_axis_label(
            canvas,
            center_x,
            center_y - 8,
            "TOTAL",
            color=CHART_AXIS,
            size=10
        )

        self.draw_axis_label(
            canvas,
            center_x,
            center_y + 14,
            format_compact(total_amount),
            color=CHART_TEXT,
            size=13,
            bold=True
        )


        # ------- LEGEND -------

        legend_x = width - legend_width + 24

        legend_top = center_y - len(totals) * 26 + 8

        legend_y = legend_top

        for category, amount in totals.items():

            color = CHART_COLORS.get(
                category,
                "#6C5CE7"
            )

            percentage = (
                amount / total_amount * 100
                if total_amount
                else 0
            )


            canvas.create_rectangle(
                legend_x,
                legend_y - 8,
                legend_x + 16,
                legend_y + 8,
                fill=color,
                outline=""
            )

            self.draw_axis_label(
                canvas,
                legend_x + 26,
                legend_y - 6,
                category,
                anchor="w",
                color=CHART_TEXT,
                size=11,
                bold=True
            )

            self.draw_axis_label(
                canvas,
                legend_x + 26,
                legend_y + 12,
                f"₹{amount:,.0f}   ({percentage:.1f}%)",
                anchor="w",
                size=9
            )

            legend_y += 46


    # ========================================================
    # MONTHLY TREND CHART
    # ========================================================

    def draw_trend_chart(self, canvas):

        canvas.delete("all")

        width, height = self.get_canvas_size(canvas)

        records = self.get_chart_records()

        monthly = self.get_monthly_totals(records)


        if not monthly:

            self.draw_empty_chart(
                canvas,
                "No monthly data to plot"
            )

            return


        left = 86
        right = 26
        top = 44
        bottom = 76

        plot_width = width - left - right

        plot_height = height - top - bottom


        if plot_width <= 60 or plot_height <= 60:

            return


        max_amount = max(
            item[1]
            for item in monthly
        )

        axis_max = nice_ceiling(max_amount)

        total_amount = sum(
            item[1]
            for item in monthly
        )


        self.draw_axis_label(
            canvas,
            left,
            18,
            (
                f"Monthly spending trend   |   "
                f"{len(monthly)} month(s)   |   "
                f"Axis max ₹{axis_max:,.0f}"
            ),
            anchor="w",
            color="#6C5CE7",
            size=10,
            bold=True
        )


        # ------- GRID LINES + Y AXIS -------

        steps = 5

        for i in range(steps + 1):

            fraction = i / steps

            y = top + plot_height - fraction * plot_height

            canvas.create_line(
                left,
                y,
                left + plot_width,
                y,
                fill=CHART_GRID,
                width=1
            )

            self.draw_axis_label(
                canvas,
                left - 10,
                y,
                format_compact(axis_max * fraction),
                anchor="e"
            )


        canvas.create_line(
            left,
            top,
            left,
            top + plot_height,
            fill=CHART_AXIS,
            width=2
        )

        canvas.create_line(
            left,
            top + plot_height,
            left + plot_width,
            top + plot_height,
            fill=CHART_AXIS,
            width=2
        )


        # ------- MONTH BARS -------

        slot = plot_width / len(monthly)

        bar_width = max(14, min(80, slot * 0.5))

        baseline = top + plot_height

        points = []


        for index, (label, amount, count) in enumerate(monthly):

            fraction = amount / axis_max if axis_max else 0

            bar_height = max(fraction * plot_height, 10)

            center_x = left + slot * (index + 0.5)

            x1 = center_x - bar_width / 2

            x2 = center_x + bar_width / 2

            y1 = baseline - bar_height

            color = TREND_COLORS[
                index % len(TREND_COLORS)
            ]


            canvas.create_rectangle(
                x1,
                y1,
                x2,
                baseline,
                fill=color,
                outline=""
            )


            self.draw_axis_label(
                canvas,
                center_x,
                y1 - 14,
                format_compact(amount),
                color=CHART_TEXT,
                size=9,
                bold=True
            )

            self.draw_axis_label(
                canvas,
                center_x,
                baseline + 18,
                label,
                color=CHART_TEXT,
                size=9,
                bold=True
            )

            self.draw_axis_label(
                canvas,
                center_x,
                baseline + 36,
                f"{count} entr{'y' if count == 1 else 'ies'}",
                size=8
            )

            points.append((center_x, y1))


        # ------- TREND LINE -------

        if len(points) > 1:

            flat_points = []

            for x, y in points:

                flat_points.append(x)
                flat_points.append(y)


            canvas.create_line(
                *flat_points,
                fill="#FF6B6B",
                width=2,
                dash=(4, 3)
            )


        # ------- FOOTER -------

        self.draw_axis_label(
            canvas,
            left,
            height - 14,
            (
                f"Total ₹{total_amount:,.2f}   |   "
                f"Monthly average ₹{total_amount / len(monthly):,.2f}"
            ),
            anchor="w",
            size=9
        )


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    create_database()

    root = tk.Tk()

    app = ExpenseTracker(
        root
    )

    root.mainloop()