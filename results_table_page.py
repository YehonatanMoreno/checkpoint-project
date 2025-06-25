import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import textwrap

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def showtip(self, text, x, y):
        self.hidetip()
        if not text:
            return
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x+20}+{y+20}")
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
        DESCRIPTION_CHAR_LENGTH: int = 50 
        
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

        style = ttk.Style()
        style.configure("Treeview", rowheight=120) 

        self.tree = ttk.Treeview(tree_frame, show="headings", style="Treeview")
        columns_ids = ("CVE_ID", "Severity", "Description", "Relevant_Repositories") 
        self.tree["columns"] = columns_ids

        self.tree.heading("CVE_ID", text="CVE-ID", anchor=tk.W)
        self.tree.heading("Severity", text="Severity", anchor=tk.CENTER)
        self.tree.heading("Description", text="Description", anchor=tk.W)
        self.tree.heading("Relevant_Repositories", text="Relevant Repositories", anchor=tk.W)

        temp_label_cve_id = ttk.Label(self.top, text="CVE ID")
        self.tree.column("CVE_ID", width=temp_label_cve_id.winfo_reqwidth() + 20, minwidth=100, stretch=tk.NO)
        temp_label_cve_id.destroy()

        temp_label_severity = ttk.Label(self.top, text="Severity")
        self.tree.column("Severity", width=temp_label_severity.winfo_reqwidth() + 20, minwidth=70, stretch=tk.NO, anchor=tk.CENTER)
        temp_label_severity.destroy()


        temp_label_description = ttk.Label(self.top, text="Description")
        self.tree.column("Description", width=temp_label_description.winfo_reqwidth() + 300, minwidth=300, stretch=tk.YES)
        temp_label_description.destroy()
        
        temp_label_repos = ttk.Label(self.top, text="Relevant Repositories")
        self.tree.column("Relevant_Repositories", width=temp_label_repos.winfo_reqwidth() + 300, minwidth=350, stretch=tk.YES)
        temp_label_repos.destroy()

        if table_data:
            for row_data in table_data:
                values = [row_data.get(column_id.lower(), "N/A") for column_id in columns_ids]
                values[2] = textwrap.fill(values[2], width=DESCRIPTION_CHAR_LENGTH) # pack description text

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

        self.tooltip = ToolTip(self.tree)
        self.tree.bind("<Motion>", self._on_tree_hover)
        self.last_row_col = (None, None)

        self.top.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.top.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.top.winfo_height() // 2)
        self.top.geometry(f'+{x}+{y}')
        
        self.top.wait_window(self.top)

    def _on_tree_hover(self, event):
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        
        if col_id and col_id.startswith("#"):
            try:
                col_index = self.tree["columns"].index(self.tree.column(col_id, option="id"))
            except ValueError:
                col_index = None
        else:
            col_index = None

        if not row_id or col_index is None:
            self.tooltip.hidetip()
            self.last_row_col = (None, None)
            return

        if (row_id, col_id) == self.last_row_col:
            return

        self.last_row_col = (row_id, col_id)

        values = self.tree.item(row_id, "values")
        if col_index < len(values):
            cell_text = str(values[col_index])
            self.tooltip.showtip(cell_text, event.x_root, event.y_root)
        else:
            self.tooltip.hidetip()

    def _on_closing(self):
        self.top.destroy()
        self.tooltip.hidetip()
        self.top.grab_release()
