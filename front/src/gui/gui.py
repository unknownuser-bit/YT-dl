import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys

sys.path.append("..")
import src.gui.bridge as bridge

class TextHandler(logging.Handler):
    """Custom logging handler that writes to a tkinter Text widget"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)

        # Direct insert + force immediate update
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')
        self.text_widget.update_idletasks()  # Force GUI update NOW


class DynamicRow:
    """Represents a single row with dropdown, url, and param fields"""

    def __init__(self, parent, row_index, remove_callback):
        self.parent = parent
        self.row_index = row_index
        self.remove_callback = remove_callback
        self.frame = None
        self.dropdown = None
        self.url_entry = None
        self.param_entry = None
        self.remove_btn = None

        self.create_widgets()

    def create_widgets(self):
        """Create the row widgets"""
        self.frame = ttk.Frame(self.parent)

        # Dropdown menu
        self.dropdown_var = tk.StringVar()
        self.dropdown = ttk.Combobox(
            self.frame,
            textvariable=self.dropdown_var,
            values=["yt-dlp (youtube,...)"],
            state="readonly",
            width=18  # Increased from 15 to better match header
        )
        self.dropdown.set("Select...")

        # URL entry
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(
            self.frame,
            textvariable=self.url_var,
            width=35  # Increased from 30 to better match header
        )

        # Param entry
        self.param_var = tk.StringVar()
        self.param_entry = ttk.Entry(
            self.frame,
            textvariable=self.param_var,
            width=18  # Increased from 15 to better match header
        )

        # Remove button
        self.remove_btn = ttk.Button(
            self.frame,
            text="✕",
            width=3,
            command=self.remove_me
        )

        # Layout - using grid for better alignment
        self.frame.grid_columnconfigure(0, weight=0)  # Dropdown column
        self.frame.grid_columnconfigure(1, weight=1)  # URL column (expandable)
        self.frame.grid_columnconfigure(2, weight=0)  # Param column
        self.frame.grid_columnconfigure(3, weight=0)  # Remove button column

        self.dropdown.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.url_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.param_entry.grid(row=0, column=2, padx=5, sticky="ew")
        self.remove_btn.grid(row=0, column=3, padx=(5, 0))

    def remove_me(self):
        """Remove this row"""
        self.frame.destroy()
        self.remove_callback(self)

    def get_values(self):
        """Return the current values of this row"""
        return {
            "dropdown": self.dropdown_var.get(),
            "url": self.url_var.get(),
            "param": self.param_var.get()
        }

    def pack(self, **kwargs):
        """Pack the row frame"""
        self.frame.pack(**kwargs)


class Gui:
    """Main application window"""

    def __init__(self):
        self.root = tk.Tk()
        self.rows = []
        self.row_counter = 0

        self.setup_logger()
        self.setup_window()
        self.create_widgets()
        self.setup_layout()

        self.add_row()
        self.logger.info("Application started")

    def set_logger(self, logger):
        self.logger = logger
        bridge.set_logger(logger)

    def setup_logger(self):
        """Initialize the logger"""
        logger = logging.getLogger("ATT_DL")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()

        self.set_logger(logger)

    def setup_window(self):
        """Configure the main window"""
        self.root.title("All The Things Downloader")
        self.root.geometry("800x650")
        self.root.minsize(600, 400)

        self.root.update_idletasks()
        width = 800
        height = 650
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Create all GUI widgets"""
        # Header
        self.header_frame = ttk.Frame(self.root)
        self.title_label = ttk.Label(
            self.header_frame,
            text="All The Things Downloader",
            font=("Arial", 16, "bold")
        )

        # Login button frame
        self.login_frame = ttk.Frame(self.root)
        self.login_btn = ttk.Button(
            self.login_frame,
            text="🔑 Login to GitHub",
            command=self.on_github_login
        )

        # Canvas and scrollbar for rows
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self.root,
            orient="vertical",
            command=self.canvas.yview
        )

        # Frame inside canvas for rows
        self.rows_frame = ttk.Frame(self.canvas)
        self.rows_frame.bind("<Configure>", self._on_frame_configure)
        
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.rows_frame,
            anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Column headers - using grid for proper alignment with rows
        self.headers_frame = ttk.Frame(self.rows_frame)

        # Configure grid columns to match DynamicRow layout
        self.headers_frame.grid_columnconfigure(0, weight=0, minsize=150)  # Dropdown column
        self.headers_frame.grid_columnconfigure(1, weight=1)  # URL column (expandable)
        self.headers_frame.grid_columnconfigure(2, weight=0, minsize=150)  # Param column
        self.headers_frame.grid_columnconfigure(3, weight=0, minsize=40)  # Remove button column

        ttk.Label(self.headers_frame, text="Type", font=("Arial", 9, "bold")).grid(
            row=0, column=0, padx=(0, 5), sticky="w"
        )
        ttk.Label(self.headers_frame, text="URL", font=("Arial", 9, "bold")).grid(
            row=0, column=1, padx=5, sticky="w"
        )
        ttk.Label(self.headers_frame, text="Param", font=("Arial", 9, "bold")).grid(
            row=0, column=2, padx=5, sticky="w"
        )
        ttk.Label(self.headers_frame, text="", font=("Arial", 9, "bold")).grid(
            row=0, column=3, padx=(5, 0)
        )

        # Bottom container for buttons and log
        self.bottom_frame = ttk.Frame(self.root)

        # Add row button
        self.add_btn_frame = ttk.Frame(self.bottom_frame)
        self.add_btn = ttk.Button(
            self.add_btn_frame,
            text="+ Add Row",
            command=self.add_row
        )

        # Submit and Clear buttons
        self.action_frame = ttk.Frame(self.bottom_frame)
        self.submit_btn = ttk.Button(
            self.action_frame,
            text="Submit",
            command=self.submit_form
        )
        self.clear_btn = ttk.Button(
            self.action_frame,
            text="Clear All Rows",
            command=self.clear_all
        )

        # Clear download history button
        self.clear_history_btn = ttk.Button(
            self.action_frame,
            text="Clear Download History",
            command=self.clear_download_history
        )

        # Log frame
        self.log_frame = ttk.LabelFrame(self.bottom_frame, text="Log", padding=5)

        self.log_text = tk.Text(
            self.log_frame,
            height=8,
            width=80,
            state='disabled',
            wrap=tk.WORD,
            bg='#1e1e1e',
            fg='#d4d4d4',
            font=('Consolas', 9)
        )
        self.log_scrollbar = ttk.Scrollbar(
            self.log_frame,
            orient="vertical",
            command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)

        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%H:%M:%S')
        )
        self.logger.addHandler(text_handler)

        self.clear_log_btn = ttk.Button(
            self.log_frame,
            text="Clear Log",
            command=self.clear_log
        )

        # Status bar
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )

    def setup_layout(self):
        """Arrange widgets"""
        # Header
        self.header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.title_label.pack()

        # Login button
        self.login_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.login_btn.pack(side=tk.RIGHT)

        # Headers
        self.headers_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Canvas and scrollbar (takes up remaining space)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(10, 5), pady=5)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=5)

        # Bottom frame (buttons + log)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 5))

        # Button rows
        self.add_btn_frame.pack(fill=tk.X, pady=(0, 5))
        self.add_btn.pack(side=tk.LEFT)

        self.action_frame.pack(fill=tk.X, pady=(0, 10))
        self.submit_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        self.clear_history_btn.pack(side=tk.LEFT, padx=5)

        # Log frame at the very bottom
        self.log_frame.pack(fill=tk.BOTH, expand=False)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clear_log_btn.pack(side=tk.BOTTOM, pady=(5, 0))

        # Status bar
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def clear_download_history(self):
        bridge.clear_download_history()

    def on_github_login(self):
        """Wrapper for GitHub login with logging"""
        self.logger.info("GitHub login initiated")
        self.status_bar.config(text="Opening GitHub login...")

        try:
            bridge.github_login()
            self.logger.info("GitHub login terminal opened successfully")
            self.status_bar.config(text="GitHub login terminal opened")
        except Exception as e:
            self.logger.error(f"GitHub login failed: {e}")
            messagebox.showerror("Login Error", str(e))
            self.status_bar.config(text="Login failed")
        logger.info("done")

    def clear_log(self):
        """Clear the log text widget"""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        self.logger.info("Log cleared")

    def _on_frame_configure(self, event=None):
        """Update scroll region when frame changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Resize the inner frame to match canvas width"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Enable mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_row(self):
        """Add a new row to the form"""
        self.row_counter += 1

        row = DynamicRow(self.rows_frame, self.row_counter, self.remove_row)
        row.pack(fill=tk.X, padx=10, pady=2)

        self.rows.append(row)

        self.status_bar.config(text=f"Row added. Total rows: {len(self.rows)}")
        self.logger.debug(f"Row {self.row_counter} added. Total: {len(self.rows)}")
        
        self.root.after(100, lambda: self.canvas.yview_moveto(1.0))

    def remove_row(self, row):
        """Remove a specific row"""
        if row in self.rows:
            self.rows.remove(row)
            row_num = row.row_index
            self.status_bar.config(text=f"Row removed. Total rows: {len(self.rows)}")
            self.logger.debug(f"Row {row_num} removed. Total: {len(self.rows)}")

    def submit_form(self):
        """Collect and display all form values"""
        form_data = [row.get_values() for row in self.rows]
        bridge.submit_operation(form_data)

    def clear_all(self):
        """Remove all rows from the form"""
        for row in self.rows[:]:
            row.frame.destroy()
        self.rows.clear()
        
        self.add_row()
        
        self.logger.info("Form cleared")
        self.status_bar.config(text="Form cleared. Ready for new input.")

    def run(self):
        """Start the main event loop"""
        self.root.mainloop()