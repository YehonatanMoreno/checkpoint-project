import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from apis.nvd_api import NVD_API
from results_table_page import SearchResultsTablePage

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.canvas = tk.Canvas(self, borderwidth=0, background="#F0F0F0")
        self.viewport = ttk.Frame(self.canvas)

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.viewport, anchor="nw",
                                                      tags="self.viewport")

        self.viewport.bind("<Configure>", self._on_frame_configure)

        self.canvas.itemconfigure(self.canvas_window, width=self.canvas.winfo_width()) 
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)


    def _on_frame_configure(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfigure(self.canvas_window, width=canvas_width)

    def _on_mouse_wheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")


class SearchResultsPage:
    def __init__(self, master, query, results):
        self.master = master
        self.top = tk.Toplevel(master)
        self.top.title(f"Results for: {query}")
        self.top.geometry("600x500")
        self.top.transient(master)
        self.top.protocol("WM_DELETE_WINDOW", self._on_closing)


        self.all_results = results
        self.results_per_page = 20
        self.current_page = 0
        self._active_inline_dropdown_frames = {}
        self._current_dropdown_button = None


        self.top.grid_rowconfigure(0, weight=0)  
        self.top.grid_rowconfigure(1, weight=1)
        self.top.grid_rowconfigure(2, weight=0)
        self.top.grid_rowconfigure(3, weight=0)
        self.top.grid_columnconfigure(0, weight=1)


        results_header = ttk.Label(self.top, text=f"Search Results for: '{query}'", font=("Arial", 16, "bold"))
        results_header.grid(row=0, column=0, pady=(20, 10), sticky="n")

        self.results_scroll_frame = ScrollableFrame(self.top)
        self.results_scroll_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.results_scroll_frame.viewport.grid_columnconfigure(0, weight=1)
        self.results_scroll_frame.viewport.grid_columnconfigure(1, weight=0)


        self.pagination_frame = ttk.Frame(self.top)
        self.pagination_frame.grid(row=2, column=0, pady=(0, 10))
        
        self.prev_button = ttk.Button(self.pagination_frame, text="Previous", command=self._prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.page_info_label = ttk.Label(self.pagination_frame, text="Page 1/1")
        self.page_info_label.pack(side=tk.LEFT, padx=10)

        self.next_button = ttk.Button(self.pagination_frame, text="Next", command=self._next_page)
        self.next_button.pack(side=tk.LEFT, padx=5)


        close_button = ttk.Button(self.top, text="Close", command=self._on_closing)
        close_button.grid(row=3, column=0, pady=10)
        
        self.top.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        
        self._display_results()

    def _clear_results_display(self):
        for widget in self.results_scroll_frame.viewport.winfo_children():
            widget.destroy()
        self._active_inline_dropdown_frames = {}
        self._current_dropdown_button = None

    def _display_results(self):
        self._clear_results_display()

        start_index = self.current_page * self.results_per_page
        end_index = start_index + self.results_per_page
        
        results_to_display = self.all_results[start_index:end_index]

        if results_to_display:
            for i, item in enumerate(results_to_display):
                serial_number = start_index + i + 1 
                display_text = f"{serial_number}. {item}"

                row_container_frame = ttk.Frame(self.results_scroll_frame.viewport, relief="groove", borderwidth=1, padding=(5,5,5,5))
                row_container_frame.grid(row=i*2, column=0, pady=5, sticky="ew", columnspan=2) # Occupies 2 columns for label and button
                row_container_frame.grid_columnconfigure(0, weight=1)
                row_container_frame.grid_columnconfigure(1, weight=0)
                result_label = ttk.Label(row_container_frame, text=display_text, wraplength=450, justify=tk.LEFT,
                                         font=("Arial", 10))
                result_label.grid(row=0, column=0, sticky="nw")
                
                arrow_button = ttk.Button(row_container_frame, text="▶", width=3,
                                          command=lambda rcf=row_container_frame, rt=item, btn=None: self._toggle_inline_dropdown(rcf, rt, btn))
                arrow_button.grid(row=0, column=1, padx=(5,0), sticky="e")
                arrow_button.config(command=lambda rcf=row_container_frame, rt=item, btn=arrow_button: self._toggle_inline_dropdown(rcf, rt, btn))


                inline_dropdown_frame = ttk.Frame(self.results_scroll_frame.viewport, padding=(10, 5, 10, 5), relief="raised", borderwidth=1)
                self._active_inline_dropdown_frames[item] = {
                    "frame": inline_dropdown_frame,
                    "button": arrow_button,
                    "visible": False
                }

                ttk.Label(inline_dropdown_frame, text="Enter minimum CVSS score to filter by:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
                entry_var = tk.StringVar()
                number_entry = ttk.Entry(inline_dropdown_frame, textvariable=entry_var, width=15)
                number_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
                inline_dropdown_frame.grid_columnconfigure(1, weight=1)

                process_button = ttk.Button(inline_dropdown_frame, text="Search for vulnerabilities",
                                            command=lambda num_val=entry_var, res_text=item: self._search_for_CVEs(num_val.get(), res_text[res_text.index('(') + 1: -1])) # Modified
                process_button.grid(row=0, column=2, padx=5, pady=2, sticky="e")
                
                self._active_inline_dropdown_frames[item]["number_entry_ref"] = number_entry


        else:
            no_results_label = ttk.Label(self.results_scroll_frame.viewport, text="No results found for this page.", font=("Arial", 12, "italic"))
            no_results_label.grid(row=0, column=0, pady=20)
            
        self._update_pagination_buttons()

    def _update_pagination_buttons(self):
        total_pages = (len(self.all_results) + self.results_per_page - 1) // self.results_per_page
        
        self.prev_button.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_page < total_pages - 1 else tk.DISABLED)
        
        if total_pages == 0:
            self.page_info_label.config(text="Page 0/0")
        else:
            self.page_info_label.config(text=f"Page {self.current_page + 1}/{total_pages}")


    def _next_page(self):
        total_pages = (len(self.all_results) + self.results_per_page - 1) // self.results_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._display_results()
            self._close_all_inline_dropdowns()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._display_results()
            self._close_all_inline_dropdowns()

    def _toggle_inline_dropdown(self, parent_row_container_frame, result_text, clicked_button):
        if self._current_dropdown_button and self._current_dropdown_button != clicked_button:
            prev_result_text = next(key for key, value in self._active_inline_dropdown_frames.items() if value["button"] == self._current_dropdown_button)
            self._hide_inline_dropdown(prev_result_text)

        dropdown_info = self._active_inline_dropdown_frames.get(result_text)

        if dropdown_info:
            dropdown_frame = dropdown_info["frame"]
            is_visible = dropdown_info["visible"]
            
            if is_visible:
                dropdown_frame.grid_forget()
                clicked_button.config(text="▶")
                dropdown_info["visible"] = False
                self._current_dropdown_button = None
            else:
                parent_row = parent_row_container_frame.grid_info()['row']
                dropdown_frame.grid(row=parent_row + 1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0,5))
                self._active_inline_dropdown_frames[result_text]["number_entry_ref"].focus_set() # Focus on the entry
                clicked_button.config(text="▼")
                dropdown_info["visible"] = True
                self._current_dropdown_button = clicked_button

        self.results_scroll_frame._on_frame_configure(None)

    def _hide_inline_dropdown(self, result_text_to_hide):
        dropdown_info = self._active_inline_dropdown_frames.get(result_text_to_hide)
        if dropdown_info and dropdown_info["visible"]:
            dropdown_info["frame"].grid_forget()
            dropdown_info["button"].config(text="▶")
            dropdown_info["visible"] = False

    def _close_all_inline_dropdowns(self):
        for result_text in list(self._active_inline_dropdown_frames.keys()):
            self._hide_inline_dropdown(result_text)
        self._current_dropdown_button = None

    def _search_for_CVEs(self, entered_number_str, result_text_context):
        try:
            entered_number = float(entered_number_str) if entered_number_str != "" else 0
            CVEs = NVD_API.get_vulnerability_by_cpe_and_severity(result_text_context, entered_number)
            for cve in CVEs:
                cve.set_relevant_repositories()
                            
            SearchResultsTablePage(self.top, f"{result_text_context} (Minimum Severity: {entered_number})", map(lambda cve: cve.model_dump(), CVEs))
            
            self._close_all_inline_dropdowns()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Error occured while searching for CVEs: {e}")
            if self._current_dropdown_button:
                current_result_text = next(
                    (key for key, value in self._active_inline_dropdown_frames.items() 
                     if value["button"] == self._current_dropdown_button), 
                    None
                )
                if current_result_text:
                    self._active_inline_dropdown_frames[current_result_text]["number_entry_ref"].focus_set()

    def _on_closing(self):
        self._close_all_inline_dropdowns()
        self.top.destroy()
