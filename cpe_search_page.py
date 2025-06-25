import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from apis.nvd_api import NVD_API
from cpe_list_page import SearchResultsPage

class MyApp:
    def __init__(self, master):
        self.master = master
        master.title("Search Application")
        master.geometry("500x300")
        master.resizable(True, True)

        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)
        master.grid_columnconfigure(0, weight=1)

        self.main_frame = ttk.Frame(master, padding="20 20 20 20")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=3)
        self.main_frame.grid_columnconfigure(2, weight=1)



        self.header_label = ttk.Label(self.main_frame, text="Hello! Enter a CPE keyword please", font=("Arial", 18, "bold"))
        self.header_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="n")


        # --- Search Bar ---
        self.search_label = ttk.Label(self.main_frame, text="CPE keyword:")
        self.search_label.grid(row=1, column=0, padx=(0, 10), sticky="e")

        self.search_entry = ttk.Entry(self.main_frame, width=40)
        self.search_entry.grid(row=1, column=1, padx=5, sticky="ew")

        self.search_entry.insert(0, "Enter a CPE keyword...")
        self.search_entry.bind("<FocusIn>", self.clear_placeholder)
        self.search_entry.bind("<FocusOut>", self.add_placeholder)


        # --- Button ---
        self.search_button = ttk.Button(self.main_frame, text="Search", command=self.perform_search)
        self.search_button.grid(row=1, column=2, padx=(10, 0), sticky="w")


        self.status_label = ttk.Label(self.main_frame, text="", font=("Arial", 10, "italic"))
        self.status_label.grid(row=2, column=0, columnspan=3, pady=10)

    def clear_placeholder(self, event):
        if self.search_entry.get() == "Enter a CPE keyword...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(foreground='black')

    def add_placeholder(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Enter a CPE keyword...")
            self.search_entry.config(foreground='grey')

    def perform_search(self):
        search_query = self.search_entry.get().strip()
        results = NVD_API.get_CPEs_by_keyword(search_query)

        if search_query and search_query != "Enter a CPE keyword...":
            SearchResultsPage(self.master, search_query, results)
            self.status_label.config(text=f"Last search: '{search_query}'")
        else:
            messagebox.showwarning("No Query", "Please enter a search query.")
            self.status_label.config(text="No search performed.")
