import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from apis.github_api import GITHUB_API
from apis.nvd_api import NVD_API
from search_result import SearchResultsPage # For showing messages to the user

class SearchApp:
    def __init__(self, master):
        """
        Initializes the Tkinter Search Application.

        Args:
            master (tk.Tk): The root Tkinter window.
        """
        self.master = master
        master.title("Search Application") # Set the window title
        master.geometry("500x300") # Set initial window size
        master.resizable(True, True) # Allow window resizing

        # Configure column and row weights for responsive layout
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # Create a frame to hold the widgets for better organization and padding
        # Use ttk.Frame for themed widget
        self.main_frame = ttk.Frame(master, padding="20 20 20 20")
        self.main_frame.grid(row=0, column=0, sticky="nsew") # Make frame expand

        # Configure columns within the frame
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=3) # Search bar wider
        self.main_frame.grid_columnconfigure(2, weight=1)


        # --- Header ---
        # ttk.Label is a themed widget, often looks better
        self.header_label = ttk.Label(self.main_frame, text="Hello! Enter a CPE keyword please", font=("Arial", 18, "bold"))
        self.header_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="n") # Centered, spans all columns


        # --- Search Bar ---
        self.search_label = ttk.Label(self.main_frame, text="CPE keyword:")
        self.search_label.grid(row=1, column=0, padx=(0, 10), sticky="e") # Align label to the right

        self.search_entry = ttk.Entry(self.main_frame, width=40) # Entry widget for input
        self.search_entry.grid(row=1, column=1, padx=5, sticky="ew") # Expand horizontally

        # Set a placeholder for the search bar
        self.search_entry.insert(0, "Enter a CPE keyword...")
        self.search_entry.bind("<FocusIn>", self.clear_placeholder)
        self.search_entry.bind("<FocusOut>", self.add_placeholder)


        # --- Button ---
        self.search_button = ttk.Button(self.main_frame, text="Search", command=self.perform_search)
        self.search_button.grid(row=1, column=2, padx=(10, 0), sticky="w") # Align button to the left


        # Optional: Add a status label
        self.status_label = ttk.Label(self.main_frame, text="", font=("Arial", 10, "italic"))
        self.status_label.grid(row=2, column=0, columnspan=3, pady=10)

    def clear_placeholder(self, event):
        """Clears the placeholder text when the entry widget gets focus."""
        if self.search_entry.get() == "Enter a CPE keyword...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(foreground='black') # Change text color to normal

    def add_placeholder(self, event):
        """Adds the placeholder text back if the entry widget is empty."""
        if not self.search_entry.get():
            self.search_entry.insert(0, "Enter a CPE keyword...")
            self.search_entry.config(foreground='grey') # Change text color to grey

    def perform_search(self):
        """
        This function is called when the Search button is clicked.
        It retrieves the text from the search bar and displays a message.
        """
        search_query = self.search_entry.get().strip() # Get text and remove leading/trailing whitespace
        results = NVD_API.get_CPEs_by_keyword(search_query)

        if search_query and search_query != "Enter a CPE keyword...":
            SearchResultsPage(self.master, search_query, results)
            self.status_label.config(text=f"Last search: '{search_query}'")
        else:
            messagebox.showwarning("No Query", "Please enter a search query.")
            self.status_label.config(text="No search performed.")


# --- Main Application Loop ---
if __name__ == "__main__":
    root = tk.Tk() # Create the main window instance
    app = SearchApp(root) # Create an instance of our SearchApp
    root.mainloop() # Start the Tkinter event loop