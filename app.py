import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import datetime


# ============================================================
# DATABASE SETTINGS
# ============================================================

DATABASE = "expenses.db"

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Fees",
    "Others"
]


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

        self.root.geometry("1150x760")

        self.root.minsize(1000, 650)

        self.root.configure(
            bg="#F4F2FF"
        )

        self.create_styles()

        self.create_header()

        self.create_summary()

        self.create_input_section()

        self.create_search_section()

        self.create_table()

        self.create_buttons()

        self.refresh_all()


    # ========================================================
    # STYLES
    # ========================================================

    def create_styles(self):

        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "Treeview",
            rowheight=32,
            font=("Arial", 10)
        )

        style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold")
        )

        style.configure(
            "TButton",
            font=("Arial", 10, "bold"),
            padding=7
        )


    # ========================================================
    # HEADER
    # ========================================================

    def create_header(self):

        header = tk.Frame(
            self.root,
            bg="#6C5CE7",
            height=85
        )

        header.pack(
            fill="x"
        )

        title = tk.Label(
            header,
            text="PERSONAL EXPENSE TRACKER",
            bg="#6C5CE7",
            fg="white",
            font=("Arial", 25, "bold")
        )

        title.pack(
            pady=(15, 2)
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
            pady=12
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
                pady=(0, 8)
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
            pady=10
        )

        input_frame.pack(
            fill="x",
            padx=15,
            pady=5
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
            pady=8
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
            pady=10
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


        expense_id = values[0]


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


        current_month = datetime.now().strftime(
            "%m-%Y"
        )


        total = 0

        count = 0


        for record in records:

            try:

                expense_date = datetime.strptime(
                    record[1],
                    "%d-%m-%Y"
                )


                if expense_date.strftime(
                    "%m-%Y"
                ) == current_month:

                    total += record[2]

                    count += 1


            except ValueError:

                continue


        messagebox.showinfo(
            "Monthly Summary",
            f"Month: {current_month}\n\n"
            f"Number of Expenses: {count}\n"
            f"Total Spent: ₹{total:.2f}"
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
    # SHOW CHART
    # ========================================================

    def show_chart(self):

        records = get_all_expenses()


        totals = {

            "Food": 0,
            "Travel": 0,
            "Shopping": 0,
            "Fees": 0,
            "Others": 0
        }


        for record in records:

            category = record[3]

            amount = record[2]


            if category in totals:

                totals[category] += amount


        chart_window = tk.Toplevel(
            self.root
        )

        chart_window.title(
            "Expense Category Chart"
        )

        chart_window.geometry(
            "800x450"
        )

        chart_window.configure(
            bg="white"
        )


        tk.Label(
            chart_window,
            text="Category-wise Expense Chart",
            bg="white",
            font=("Arial", 18, "bold")
        ).pack(
            pady=15
        )


        canvas = tk.Canvas(
            chart_window,
            width=750,
            height=350,
            bg="white"
        )

        canvas.pack()


        values = list(
            totals.values()
        )


        maximum = max(
            values
        ) if values else 0


        if maximum == 0:

            canvas.create_text(
                375,
                170,
                text="No expense data available",
                font=("Arial", 14)
            )

            return


        categories = list(
            totals.keys()
        )


        bar_width = 75

        gap = 50

        start_x = 45

        bottom_y = 280

        max_height = 210


        for i, category in enumerate(
            categories
        ):

            amount = totals[
                category
            ]


            bar_height = (
                amount / maximum
            ) * max_height


            x1 = (
                start_x
                + i * (bar_width + gap)
            )

            y1 = (
                bottom_y
                - bar_height
            )

            x2 = x1 + bar_width

            y2 = bottom_y


            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#6C5CE7",
                outline=""
            )


            canvas.create_text(
                (x1 + x2) / 2,
                y1 - 12,
                text=f"₹{amount:.0f}",
                font=("Arial", 10, "bold")
            )


            canvas.create_text(
                (x1 + x2) / 2,
                bottom_y + 20,
                text=category,
                font=("Arial", 10)
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