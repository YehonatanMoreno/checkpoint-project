from functools import reduce
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Re-enabled: The SearchResultsTablePage will now be opened by the dropdown button
from apis.github_api import GITHUB_API
from apis.nvd_api import NVD_API
from results_table_page import SearchResultsTablePage

class ScrollableFrame(ttk.Frame):
    """
    A custom Tkinter Frame that provides a scrollbar for its content.
    Widgets placed inside this frame will be scrollable if they exceed
    the frame's visible area.
    """
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create a Canvas widget which is the only natively scrollable container
        self.canvas = tk.Canvas(self, borderwidth=0, background="#F0F0F0") # Light grey background
        self.viewport = ttk.Frame(self.canvas) # This frame will hold the scrollable content

        # Create a vertical scrollbar and link it to the canvas
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        # Place the scrollbar and canvas
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Create a window in the canvas to contain the viewport frame
        # The (0,0) coordinates and 'nw' anchor place the viewport at the top-left
        self.canvas_window = self.canvas.create_window((0, 0), window=self.viewport, anchor="nw",
                                                      tags="self.viewport")

        # Bind events to configure scrolling
        # When the viewport's size changes, update the scroll region of the canvas
        self.viewport.bind("<Configure>", self._on_frame_configure)
        # When the canvas's size changes, update the canvas window's width
        # Ensure initial width is set for correct rendering
        self.canvas.itemconfigure(self.canvas_window, width=self.canvas.winfo_width()) 
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Enable mouse wheel scrolling (cross-platform)
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel) # Windows/macOS
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)   # Linux (scroll up)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)   # Linux (scroll down)


    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Reset the canvas window width to match canvas width"""
        canvas_width = event.width
        self.canvas.itemconfigure(self.canvas_window, width=canvas_width)

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        # For Windows/macOS, event.delta is typically +/-120 per scroll click
        if event.delta:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        # For Linux, event.num is 4 for scroll up, 5 for scroll down
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")


class SearchResultsPage:
    def __init__(self, master, query, results):
        """
        Initializes the Search Results Page.

        Args:
            master (tk.Tk): The parent Tkinter window (usually the main app root).
            query (str): The search query.
            results (list): A list of strings representing the search results.
        """
        self.master = master # Store master for centering
        self.top = tk.Toplevel(master) # Create a new top-level window
        self.top.title(f"Results for: {query}")
        self.top.geometry("600x500") # Increased initial size for better result display
        self.top.transient(master) # Make it appear on top of the master window
        self.top.protocol("WM_DELETE_WINDOW", self._on_closing) # Handle close button

        # Store all results and pagination settings
        self.all_results = results
        self.results_per_page = 20 # Changed from 10 to 20
        self.current_page = 0 # 0-indexed page number

        # Dictionary to hold references to currently open inline dropdown frames
        # Key: Unique identifier for the result (e.g., serial number or result text itself)
        # Value: The ttk.Frame containing the dropdown elements
        self._active_inline_dropdown_frames = {}
        # Variable to keep track of the button that opened the current dropdown
        self._current_dropdown_button = None


        # Configure grid for the Toplevel window
        self.top.grid_rowconfigure(0, weight=0)  # Header row
        self.top.grid_rowconfigure(1, weight=1)  # Scrollable results frame row
        self.top.grid_rowconfigure(2, weight=0)  # Pagination buttons row
        self.top.grid_rowconfigure(3, weight=0)  # Close button row
        self.top.grid_columnconfigure(0, weight=1) # Main column for content


        # Header for the results page
        results_header = ttk.Label(self.top, text=f"Search Results for: '{query}'", font=("Arial", 16, "bold"))
        results_header.grid(row=0, column=0, pady=(20, 10), sticky="n")

        # Create the scrollable frame for results
        self.results_scroll_frame = ScrollableFrame(self.top)
        self.results_scroll_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # Configure the viewport frame within the scrollable frame for result labels
        self.results_scroll_frame.viewport.grid_columnconfigure(0, weight=1)
        self.results_scroll_frame.viewport.grid_columnconfigure(1, weight=0) # For the arrow button column


        # --- Pagination Controls ---
        self.pagination_frame = ttk.Frame(self.top)
        self.pagination_frame.grid(row=2, column=0, pady=(0, 10))
        
        self.prev_button = ttk.Button(self.pagination_frame, text="Previous", command=self._prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.page_info_label = ttk.Label(self.pagination_frame, text="Page 1/1")
        self.page_info_label.pack(side=tk.LEFT, padx=10)

        self.next_button = ttk.Button(self.pagination_frame, text="Next", command=self._next_page)
        self.next_button.pack(side=tk.LEFT, padx=5)


        # Close button for the results page
        close_button = ttk.Button(self.top, text="Close", command=self._on_closing)
        close_button.grid(row=3, column=0, pady=10)
        
        # Center the new window relative to its parent
        self.top.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        
        # Display the first page of results
        self._display_results()

    def _clear_results_display(self):
        """Clears all widgets from the scrollable viewport."""
        for widget in self.results_scroll_frame.viewport.winfo_children():
            widget.destroy()
        self._active_inline_dropdown_frames = {} # Clear dropdown references
        self._current_dropdown_button = None

    def _display_results(self):
        """Displays the results for the current_page."""
        self._clear_results_display() # This also clears dropdown references

        start_index = self.current_page * self.results_per_page
        end_index = start_index + self.results_per_page
        
        results_to_display = self.all_results[start_index:end_index]

        if results_to_display:
            for i, item in enumerate(results_to_display):
                # Calculate the global serial number
                serial_number = start_index + i + 1 
                display_text = f"{serial_number}. {item}" # Prepend serial number to the text

                # Outer frame for each result row, including label and dropdown area
                row_container_frame = ttk.Frame(self.results_scroll_frame.viewport, relief="groove", borderwidth=1, padding=(5,5,5,5))
                row_container_frame.grid(row=i*2, column=0, pady=5, sticky="ew", columnspan=2) # Occupies 2 columns for label and button
                row_container_frame.grid_columnconfigure(0, weight=1) # For result label
                row_container_frame.grid_columnconfigure(1, weight=0) # For arrow button

                result_label = ttk.Label(row_container_frame, text=display_text, wraplength=450, justify=tk.LEFT,
                                         font=("Arial", 10))
                result_label.grid(row=0, column=0, sticky="nw")
                
                # Arrow button to toggle dropdown
                arrow_button = ttk.Button(row_container_frame, text="▶", width=3,
                                          command=lambda rcf=row_container_frame, rt=item, btn=None: self._toggle_inline_dropdown(rcf, rt, btn))
                arrow_button.grid(row=0, column=1, padx=(5,0), sticky="e")
                # Update the lambda to pass the button itself after it's created
                arrow_button.config(command=lambda rcf=row_container_frame, rt=item, btn=arrow_button: self._toggle_inline_dropdown(rcf, rt, btn))


                # Create the inline dropdown frame (initially hidden)
                inline_dropdown_frame = ttk.Frame(self.results_scroll_frame.viewport, padding=(10, 5, 10, 5), relief="raised", borderwidth=1)
                # It will be gridded at row i*2 + 1, spanning both columns below the result_frame
                # Store it in our dictionary with the original result text as key (needs to be unique)
                self._active_inline_dropdown_frames[item] = {
                    "frame": inline_dropdown_frame,
                    "button": arrow_button,
                    "visible": False # Track visibility state
                }

                # Widgets for the inline dropdown
                ttk.Label(inline_dropdown_frame, text="Enter minimum CVSS score to filter by:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
                entry_var = tk.StringVar()
                number_entry = ttk.Entry(inline_dropdown_frame, textvariable=entry_var, width=15)
                number_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
                inline_dropdown_frame.grid_columnconfigure(1, weight=1) # Allow entry to expand

                process_button = ttk.Button(inline_dropdown_frame, text="Search for vulnerabilities",
                                            command=lambda num_val=entry_var, res_text=item: self._search_for_CVEs(num_val.get(), res_text[res_text.index('(') + 1: -1])) # Modified
                process_button.grid(row=0, column=2, padx=5, pady=2, sticky="e")
                
                # Store reference to entry for focusing
                self._active_inline_dropdown_frames[item]["number_entry_ref"] = number_entry


        else:
            no_results_label = ttk.Label(self.results_scroll_frame.viewport, text="No results found for this page.", font=("Arial", 12, "italic"))
            no_results_label.grid(row=0, column=0, pady=20)
            
        self._update_pagination_buttons()

    def _update_pagination_buttons(self):
        """Updates the state of pagination buttons and page info label."""
        total_pages = (len(self.all_results) + self.results_per_page - 1) // self.results_per_page
        
        self.prev_button.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_page < total_pages - 1 else tk.DISABLED)
        
        # Handle case where there are no results to prevent division by zero or negative page numbers
        if total_pages == 0:
            self.page_info_label.config(text="Page 0/0")
        else:
            self.page_info_label.config(text=f"Page {self.current_page + 1}/{total_pages}")


    def _next_page(self):
        """Navigates to the next page of results."""
        total_pages = (len(self.all_results) + self.results_per_page - 1) // self.results_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._display_results()
            self._close_all_inline_dropdowns() # Close any open dropdowns when changing page

    def _prev_page(self):
        """Navigates to the previous page of results."""
        if self.current_page > 0:
            self.current_page -= 1
            self._display_results()
            self._close_all_inline_dropdowns() # Close any open dropdowns when changing page

    def _toggle_inline_dropdown(self, parent_row_container_frame, result_text, clicked_button):
        """
        Toggles the visibility of the inline dropdown for a specific result.
        Closes any other open dropdowns.
        """
        # Ensure only one dropdown is open at a time
        if self._current_dropdown_button and self._current_dropdown_button != clicked_button:
            # If a different button opened the previous dropdown, close it
            prev_result_text = next(key for key, value in self._active_inline_dropdown_frames.items() if value["button"] == self._current_dropdown_button)
            self._hide_inline_dropdown(prev_result_text)

        # Get the dropdown frame and its state for the current result_text
        dropdown_info = self._active_inline_dropdown_frames.get(result_text)

        if dropdown_info:
            dropdown_frame = dropdown_info["frame"]
            is_visible = dropdown_info["visible"]
            
            if is_visible:
                # Hide the dropdown
                dropdown_frame.grid_forget()
                clicked_button.config(text="▶")
                dropdown_info["visible"] = False
                self._current_dropdown_button = None
            else:
                # Show the dropdown
                # Determine the row where the dropdown should be placed
                # It should be directly below its parent row_container_frame
                parent_row = parent_row_container_frame.grid_info()['row']
                dropdown_frame.grid(row=parent_row + 1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0,5))
                self._active_inline_dropdown_frames[result_text]["number_entry_ref"].focus_set() # Focus on the entry
                clicked_button.config(text="▼")
                dropdown_info["visible"] = True
                self._current_dropdown_button = clicked_button

        # Update the canvas scroll region as new widgets might have appeared/disappeared
        self.results_scroll_frame._on_frame_configure(None) # Pass None as event is not used

    def _hide_inline_dropdown(self, result_text_to_hide):
        """Hides a specific inline dropdown if it's open."""
        dropdown_info = self._active_inline_dropdown_frames.get(result_text_to_hide)
        if dropdown_info and dropdown_info["visible"]:
            dropdown_info["frame"].grid_forget()
            dropdown_info["button"].config(text="▶")
            dropdown_info["visible"] = False

    def _close_all_inline_dropdowns(self):
        """Closes all currently open inline dropdowns."""
        for result_text in list(self._active_inline_dropdown_frames.keys()): # Iterate over a copy
            self._hide_inline_dropdown(result_text)
        self._current_dropdown_button = None # Reset reference

    def _search_for_CVEs(self, entered_number_str, result_text_context):
        """
        Processes the number entered in the inline dropdown and opens a new
        table page with results based on the number and the context.
        """
        try:
            print(entered_number_str)
            entered_number = float(entered_number_str) if entered_number_str != "" else 0
            # You can use entered_number and result_text_context to fetch/generate
            # more specific data for your table.
            
            # Generate dummy table data based on the entered number and result context
            # Modifying _get_dummy_table_data to accept the number for more varied data
            CVEs = NVD_API.get_vulnerability_by_cpe_and_severity(result_text_context, entered_number)
            for cve in CVEs:
                cve.set_relevant_repositories()
                
            print(CVEs)
            
            # Open the new table results page
            # The master for the new table page is the current results page (self.top)
            SearchResultsTablePage(self.top, f"{result_text_context} (Minimum Severity: {entered_number})", map(lambda cve: cve.model_dump(), CVEs))
            
            self._close_all_inline_dropdowns() # Close the dropdown after opening the new page
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please enter a valid integer number.:::{e}")
            # If invalid, try to find the active entry and focus it again
            if self._current_dropdown_button:
                current_result_text = next(
                    (key for key, value in self._active_inline_dropdown_frames.items() 
                     if value["button"] == self._current_dropdown_button), 
                    None
                )
                if current_result_text:
                    self._active_inline_dropdown_frames[current_result_text]["number_entry_ref"].focus_set()

    def _on_closing(self):
        """Handles the closing of the results window."""
        self._close_all_inline_dropdowns() # Close any open dropdowns
        self.top.destroy()
