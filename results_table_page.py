import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import random

# Tooltip helper class
class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def showtip(self, text):
        self.hidetip()
        if not text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=text, justify='left',
            background="#ffffe0", relief='solid', borderwidth=1,
            font=("tahoma", 8, "normal"), wraplength=500
        )
        label.pack(ipadx=1)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class SearchResultsTablePage:
    def __init__(self, master, parent_result_text, table_data):
        self.top = tk.Toplevel(master)
        self.top.title(f"Details for: {parent_result_text}")
        self.top.geometry("900x450")
        self.top.transient(master)
        self.top.grab_set()
        self.top.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.top.grid_rowconfigure(0, weight=0)
        self.top.grid_rowconfigure(1, weight=1)
        self.top.grid_rowconfigure(2, weight=0)
        self.top.grid_columnconfigure(0, weight=1)

        table_header = ttk.Label(self.top, text=f"CVE Results for: {parent_result_text}", font=("Arial", 14, "bold"))
        table_header.grid(row=0, column=0, pady=(15, 10), sticky="n")

        tree_frame = ttk.Frame(self.top, padding=(10,0,10,10))
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, show="headings")
        columns_ids = ("CVE_ID", "Severity", "Description", "Relevant_Repositories") 
        self.tree["columns"] = columns_ids

        self.tree.heading("CVE_ID", text="CVE-ID", anchor=tk.W)
        self.tree.heading("Severity", text="Severity", anchor=tk.CENTER)
        self.tree.heading("Description", text="Description", anchor=tk.W)
        self.tree.heading("Relevant_Repositories", text="Relevant Repositories", anchor=tk.W)

        self.tree.column("CVE_ID", width=120, minwidth=100, stretch=tk.NO)
        self.tree.column("Severity", width=80, minwidth=70, stretch=tk.NO, anchor=tk.CENTER)
        self.tree.column("Description", width=400, minwidth=300, stretch=tk.YES)
        self.tree.column("Relevant_Repositories", width=400, minwidth=350, stretch=tk.YES)

        if table_data:
            for row_data in table_data:
                values = [row_data.get(column_id.lower(), "N/A") for column_id in columns_ids]
                self.tree.insert("", tk.END, values=values)
        else:
            self.tree.insert("", tk.END, values=("", "", "No detailed results available.", ""))

        vsb_tree = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb_tree.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb_tree.set)

        hsb_tree = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb_tree.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=hsb_tree.set)

        self.tree.grid(row=0, column=0, sticky="nsew")

        close_button = ttk.Button(self.top, text="Close Table", command=self._on_closing)
        close_button.grid(row=2, column=0, pady=10)

        # Tooltip integration
        self.tooltip = ToolTip(self.tree)
        self.tree.bind("<Motion>", self._on_tree_hover)
        self.last_row_col = (None, None)

        # Center the new window
        self.top.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        
        self.top.wait_window(self.top)

    def _on_tree_hover(self, event):
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        col_index = int(col_id.replace("#", "")) - 1 if col_id else None

        if not row_id or col_index is None:
            self.tooltip.hidetip()
            self.last_row_col = (None, None)
            return

        if (row_id, col_id) == self.last_row_col:
            return  # Don't update tooltip if still over same cell

        self.last_row_col = (row_id, col_id)

        values = self.tree.item(row_id, "values")
        if col_index < len(values):
            self.tooltip.showtip(str(values[col_index]))
        else:
            self.tooltip.hidetip()

    def _on_closing(self):
        self.top.grab_release()
        self.top.destroy()
