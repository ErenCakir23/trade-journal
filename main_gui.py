import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
import webbrowser
import os
from datetime import datetime

# The function you defined in the report_generator.py file
from report_generator import generate_full_report_with_recommendations

class TradeEntryGUI:
    """
    Crypto Trade Tracker GUI application.
    
    This class creates the main window of the application, handling trade entries,
    report generation, and note management.
    """
    def __init__(self, root):
        """
        Initialize the GUI components and setup database connection.

        Parameters:
        root (tk.Tk): The root window of the Tkinter application.
        """
        self.root = root
        self.root.title("Crypto Trade Tracker")
        self.root.geometry("900x600")
        self.root.resizable(False, False)

        # Connect to the SQLite database
        self.conn = sqlite3.connect("trade_data.db")
        self.cursor = self.conn.cursor()

        # Create Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Trade Entry Tab
        self.trade_tab = tk.Frame(self.notebook, bg="#333333")
        self.notebook.add(self.trade_tab, text="Trade Entry")

        # Notes Tab
        self.notes_tab = tk.Frame(self.notebook, bg="#333333")
        self.notebook.add(self.notes_tab, text="Notes")

        # Create content for tabs
        self.create_trade_section()
        self.create_notes_section()

    def create_trade_section(self):
        """
        Create the trade entry section of the GUI, including input fields and report buttons.
        """
        self.main_frame = tk.Frame(self.trade_tab, bg="#333333")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.left_frame = tk.Frame(self.main_frame, bg="#333333")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(self.main_frame, bg="#333333", width=250)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.create_input_fields()

        self.save_button = tk.Button(
            self.left_frame,
            text="Save Trade",
            command=self.save_trade,
            bg="#FFD700",
            fg="black",
            font=("Helvetica", 12, "bold"),
            bd=0,
            activebackground="#FFC300",
            activeforeground="black"
        )
        self.save_button.grid(row=7, column=0, columnspan=2, pady=20, ipadx=10, ipady=5)

        # Reports Section
        self.create_reports_section()

        # Useful Links Section
        self.create_links_section()

    def create_input_fields(self):
        """
        Create input fields for trade entry including Coin Name, Position, Mode, Date, Leverage, Entry and Exit Prices.
        """
        fields = [
            ("Coin Name", "#FFD700"),
            ("Position (long/short)", "#FFD700"),
            ("Mode (real/demo)", "#FFD700"),
            ("Date (YYYY-MM-DD)", "#FFD700"),
            ("Leverage", "#FFD700"),
            ("Entry Price", "#FFD700"),
            ("Exit Price", "#FFD700")
        ]

        self.entries = {}
        for idx, (label, color) in enumerate(fields):
            frame = tk.Frame(
                self.left_frame,
                bg=color,
                bd=2,
                relief="solid",
                padx=10,
                pady=10
            )
            frame.grid(row=idx, column=0, padx=5, pady=5, sticky="ew")

            lbl = tk.Label(
                frame,
                text=label,
                bg=color,
                fg="black",
                font=("Helvetica", 10, "bold")
            )
            lbl.pack(side=tk.LEFT)

            entry = tk.Entry(
                frame,
                width=30,
                bg="white",
                font=("Helvetica", 10)
            )
            entry.pack(side=tk.RIGHT, padx=5)

            # Auto-fill date field with today's date
            if label == "Date (YYYY-MM-DD)":
                entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

            self.entries[label] = entry

    def create_reports_section(self):
        """
        Create the reports section with buttons to generate and view reports.
        """
        report_label = tk.Label(
            self.right_frame,
            text="Reports",
            bg="#333333",
            fg="#FFD700",
            font=("Helvetica", 14, "bold")
        )
        report_label.pack(pady=10)

        create_report_button = tk.Button(
            self.right_frame,
            text="Generate Report",
            command=self.create_report,  
            bg="#FFD700",
            fg="black",
            font=("Helvetica", 12),
            bd=0,
            activebackground="#FFC300",
            activeforeground="black",
            width=20,
            pady=5
        )
        create_report_button.pack(pady=10)

        view_report_button = tk.Button(
            self.right_frame,
            text="View Reports",
            command=self.view_reports,  
            bg="#FFD700",
            fg="black",
            font=("Helvetica", 12),
            bd=0,
            activebackground="#FFC300",
            activeforeground="black",
            width=20,
            pady=5
        )
        view_report_button.pack(pady=10)

    def create_links_section(self):
        """
        Create a section with clickable links to useful cryptocurrency websites.
        """
        link_frame = tk.Frame(self.right_frame, bg="#444444", bd=2, relief="solid")
        link_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(
            link_frame,
            text="Useful Websites",
            bg="#444444",
            fg="#FFD700",
            font=("Helvetica", 14, "bold")
        ).pack(pady=10)

        links = [
            ("TradingView", "https://www.tradingview.com"),
            ("CoinMarketCap", "https://coinmarketcap.com"),
            ("CoinGlass", "https://www.coinglass.com/tr"),
            ("CryptoBubbles", "https://cryptobubbles.net"),
            ("Investing", "https://www.investing.com"),
        ]

        for site_name, site_url in links:
            link_label = tk.Label(
                link_frame,
                text=site_name,
                fg="#FFD700",
                bg="#444444",
                cursor="hand2",
                font=("Helvetica", 12, "underline", "bold")
            )
            link_label.pack(pady=2)
            link_label.bind("<Button-1>", lambda e, url=site_url: webbrowser.open_new(url))

    def save_trade(self):
        """
        Save the trade data entered by the user into the SQLite database.
        """
        trade_data = {
            "coin_name": self.entries["Coin Name"].get(),
            "position": self.entries["Position (long/short)"].get(),
            "mode": self.entries["Mode (real/demo)"].get(),
            "date": self.entries["Date (YYYY-MM-DD)"].get(),
            "leverage": self.entries["Leverage"].get(),
            "entry_price": self.entries["Entry Price"].get(),
            "exit_price": self.entries["Exit Price"].get()
        }

        if not all(trade_data.values()):
            messagebox.showerror("Error", "All fields must be filled!")
            return

        try:
            self.cursor.execute('''
                INSERT INTO trades (coin_name, position, mode, date, leverage, entry_price, exit_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data["coin_name"],
                trade_data["position"],
                trade_data["mode"],
                trade_data["date"],
                float(trade_data["leverage"]),
                float(trade_data["entry_price"]),
                float(trade_data["exit_price"])
            ))
            self.conn.commit()

            messagebox.showinfo("Success", "Trade data saved successfully!")

            # Clear fields
            for key, entry in self.entries.items():
                entry.delete(0, tk.END)
                if key == "Date (YYYY-MM-DD)":
                    entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")

    def create_report(self):
        """
        Generate a comprehensive PDF report and open it if successfully created.
        """
        try:
            # Execute the report generation function
            generate_full_report_with_recommendations(self.conn)

            # Define the path for reports directory
            raporlar_path = os.path.join(os.getcwd(), "reports")
            os.makedirs(raporlar_path, exist_ok=True)  # Create directory if not exists

            # Define the PDF file name and path
            today_str = datetime.now().strftime("%Y-%m-%d")
            pdf_name = f"report_{today_str}.pdf"
            pdf_path = os.path.join(raporlar_path, pdf_name)

            # If PDF exists, open it
            if os.path.exists(pdf_path):
                os.startfile(pdf_path)  # Opens with default PDF viewer on Windows
                messagebox.showinfo("Info", "Report generated and opened successfully.")
            else:
                messagebox.showwarning("Warning", f"Report file not found: {pdf_path}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while generating the report: {e}")

    def view_reports(self):
        """
        Open the reports directory to view existing reports.
        """
        raporlar_path = os.path.join(os.getcwd(), "reports")
        if os.path.exists(raporlar_path):
            os.startfile(raporlar_path)
        else:
            messagebox.showerror("Error", "Reports folder not found!")

    def create_notes_section(self):
        """
        Create the notes management section of the GUI, allowing users to add, update, delete, and view notes.
        """
        notes_frame = tk.Frame(self.notes_tab, bg="#333333")
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.notes_listbox = tk.Listbox(
            notes_frame, 
            width=50, 
            height=20, 
            bg="white",
            fg="black", 
            font=("Helvetica", 10)
        )
        self.notes_listbox.grid(row=0, column=0, rowspan=6, padx=10, pady=10, sticky="n")
        self.notes_listbox.bind('<<ListboxSelect>>', self.display_note)

        ttk.Label(
            notes_frame, 
            text="Note Title", 
            background="#333333", 
            foreground="#FFD700", 
            font=("Helvetica", 12)
        ).grid(row=0, column=1, padx=10, pady=5, sticky="e")
        self.note_title_var = tk.StringVar()
        self.note_title_entry = ttk.Entry(notes_frame, textvariable=self.note_title_var, width=50)
        self.note_title_entry.grid(row=0, column=2, padx=10, pady=5)

        ttk.Label(
            notes_frame, 
            text="Note Content", 
            background="#333333", 
            foreground="#FFD700", 
            font=("Helvetica", 12)
        ).grid(row=1, column=1, padx=10, pady=5, sticky="ne")
        self.note_content_text = tk.Text(
            notes_frame, 
            width=50, 
            height=20, 
            bg="white",
            fg="black", 
            font=("Helvetica", 10)
        )
        self.note_content_text.grid(row=1, column=2, padx=10, pady=5)

        self.save_note_button = tk.Button(
            notes_frame,
            text="Save Note",
            command=self.save_note,
            bg="#FFD700",
            fg="black",
            font=("Helvetica", 12),
            bd=0,
            activebackground="#FFC300",
            activeforeground="black"
        )
        self.save_note_button.grid(row=2, column=2, padx=10, pady=10, sticky="e")

        self.update_note_button = tk.Button(
            notes_frame,
            text="Update Note",
            command=self.update_note,
            bg="#FFD700",
            fg="black",
            font=("Helvetica", 12),
            bd=0,
            activebackground="#FFC300",
            activeforeground="black"
        )
        self.update_note_button.grid(row=3, column=2, padx=10, pady=5, sticky="e")

        self.delete_note_button = tk.Button(
            notes_frame,
            text="Delete Note",
            command=self.delete_note,
            bg="#FFD700",
            fg="black",
            font=("Helvetica", 12),
            bd=0,
            activebackground="#FFC300",
            activeforeground="black"
        )
        self.delete_note_button.grid(row=4, column=2, padx=10, pady=5, sticky="e")

        self.load_notes()

    def save_note(self):
        """
        Save a new note into the SQLite database.
        """
        title = self.note_title_var.get().strip()
        content = self.note_content_text.get("1.0", tk.END).strip()
        if not title or not content:
            messagebox.showerror("Error", "Title and content cannot be empty!")
            return

        try:
            self.cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
            self.conn.commit()
            self.load_notes()
            self.clear_note_fields()
            messagebox.showinfo("Success", "Note saved successfully!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to save note: {e}")

    def update_note(self):
        """
        Update an existing note in the SQLite database.
        """
        selected_note = self.notes_listbox.curselection()
        if not selected_note:
            messagebox.showerror("Error", "You must select a note to update!")
            return

        old_title = self.notes_listbox.get(selected_note).lstrip("- ")
        new_title = self.note_title_var.get().strip()
        new_content = self.note_content_text.get("1.0", tk.END).strip()

        if not new_title or not new_content:
            messagebox.showerror("Error", "Title and content cannot be empty!")
            return

        try:
            self.cursor.execute("UPDATE notes SET title=?, content=? WHERE title=?", 
                                (new_title, new_content, old_title))
            self.conn.commit()
            self.load_notes()
            self.clear_note_fields()
            messagebox.showinfo("Success", "Note updated successfully!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to update note: {e}")

    def delete_note(self):
        """
        Delete a selected note from the SQLite database.
        """
        selected_note = self.notes_listbox.curselection()
        if not selected_note:
            messagebox.showerror("Error", "You must select a note to delete!")
            return

        title = self.notes_listbox.get(selected_note).lstrip("- ")
        try:
            self.cursor.execute("DELETE FROM notes WHERE title = ?", (title,))
            self.conn.commit()
            self.load_notes()
            self.clear_note_fields()
            messagebox.showinfo("Success", "Note deleted successfully!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to delete note: {e}")

    def load_notes(self):
        """
        Load all notes from the SQLite database and display them in the listbox.
        """
        self.notes_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT title, date FROM notes ORDER BY date DESC")
        notes = self.cursor.fetchall()
        for title, note_date in notes:
            self.notes_listbox.insert(tk.END, f"- {title}")

    def display_note(self, event):
        """
        Display the content of the selected note in the note fields.

        Parameters:
        event (tk.Event): The event object triggered by selecting a note.
        """
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        selected_title = self.notes_listbox.get(selection).lstrip("- ")
        self.cursor.execute("SELECT content FROM notes WHERE title = ?", (selected_title,))
        result = self.cursor.fetchone()
        if result:
            self.clear_note_fields()
            self.note_title_var.set(selected_title)
            self.note_content_text.insert("1.0", result[0])

    def clear_note_fields(self):
        """
        Clear the note title and content fields.
        """
        self.note_title_var.set("")
        self.note_content_text.delete("1.0", tk.END)

if __name__ == "__main__":
    # Ensure the reports directory exists
    raporlar_path = os.path.join(os.getcwd(), "reports")
    os.makedirs(raporlar_path, exist_ok=True)

    root = tk.Tk()
    app = TradeEntryGUI(root)
    root.mainloop()
