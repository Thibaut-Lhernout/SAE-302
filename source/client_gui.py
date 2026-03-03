"""
Desktop client GUI for the SAE32 search engine.

- Tkinter interface.
- Sends search requests to the TCP server.
- Displays results in a table.
"""

from __future__ import annotations

import json
import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk

SERVER_HOST: str = "127.0.0.1"
SERVER_PORT: int = 65432
BUFFER_SIZE: int = 4096


class SearchApp:
    """
    Main desktop client for the SAE search engine.

    Handles the Tkinter user interface and the TCP communication
    with the search server.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the main window, styles and network state."""
        self.root = root
        self.root.title("T1b021 research")
        self.root.geometry("1000x650")

        # --- Theme colors ---
        self.bg_color = "#050505"
        self.fg_color = "#00ff66"
        self.accent_color = "#00aa55"
        self.frame_color = "#101010"

        self.root.configure(bg=self.bg_color)
        self._configure_style()

        self.client_socket: socket.socket | None = None
        self.is_connected: bool = False

        self.setup_ui()
        self.start_connection_thread()

    # ------------------------------------------------------------------ #
    #  UI configuration                                                  #
    # ------------------------------------------------------------------ #

    def _configure_style(self) -> None:
        """Configure the custom dark theme for ttk widgets."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=self.bg_color)

        style.configure(
            "TLabelframe",
            background=self.frame_color,
            foreground=self.fg_color,
            bordercolor=self.accent_color,
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=self.frame_color,
            foreground=self.accent_color,
        )

        style.configure(
            "TLabel",
            background=self.frame_color,
            foreground=self.fg_color,
        )

        style.configure(
            "TEntry",
            fieldbackground="#000000",
            foreground=self.fg_color,
            insertcolor=self.fg_color,
            borderwidth=0,
        )

        style.configure(
            "TCheckbutton",
            background=self.frame_color,
            foreground=self.fg_color,
            focuscolor=self.accent_color,
        )

        style.configure(
            "TButton",
            background=self.bg_color,
            foreground=self.accent_color,
            borderwidth=1,
            focusthickness=2,
            focuscolor=self.accent_color,
        )
        style.map(
            "TButton",
            background=[("active", "#002211")],
            foreground=[("active", "#00ff99")],
        )

        style.configure(
            "Treeview",
            background="#000000",
            foreground=self.fg_color,
            fieldbackground="#000000",
            rowheight=22,
        )
        style.configure(
            "Treeview.Heading",
            background=self.frame_color,
            foreground=self.accent_color,
        )

    def setup_ui(self) -> None:
        """
        Build all UI widgets: query console, filters, results table and status bar.
        """
        # Top banner
        banner = ttk.Frame(self.root)
        banner.pack(fill="x", padx=10, pady=(8, 4))

        lbl_title = ttk.Label(
            banner,
            text="> T1b021 research // interactive search console",
            foreground=self.accent_color,
        )
        lbl_title.pack(side="left")

        # ---- Query console ----------------------------------------------
        control_frame = ttk.LabelFrame(self.root, text="QUERY CONSOLE", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        # Query line
        ttk.Label(control_frame, text="pattern> ").grid(row=0, column=0, sticky="w")
        self.entry_query = ttk.Entry(control_frame, width=60)
        self.entry_query.grid(row=0, column=1, padx=10, sticky="w")
        self.entry_query.bind("<Return>", lambda _: self.on_search())

        # Regex mode checkbox
        self.var_regex = tk.BooleanVar()
        ttk.Checkbutton(
            control_frame,
            text="regex_mode",
            variable=self.var_regex,
        ).grid(row=0, column=2, padx=10, sticky="w")

        # File type filters
        type_frame = ttk.Frame(control_frame)
        type_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky="w")

        ttk.Label(type_frame, text="targets> ").pack(side="left")

        self.ext_vars: dict[str, tk.BooleanVar] = {
            ".txt": tk.BooleanVar(value=True),
            ".html": tk.BooleanVar(value=True),
            ".pdf": tk.BooleanVar(value=True),
            ".xlsx": tk.BooleanVar(value=True),
        }
        for ext, var in self.ext_vars.items():
            ttk.Checkbutton(type_frame, text=ext, variable=var).pack(
                side="left",
                padx=5,
            )

        # Execute button
        self.btn_search = ttk.Button(
            control_frame,
            text="EXECUTE",
            command=self.on_search,
        )
        self.btn_search.grid(row=0, column=3, padx=10, sticky="e")

        # ---- Results table ----------------------------------------------
        result_frame = ttk.LabelFrame(self.root, text="RESULT FEED", padding=10)
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("file", "type", "loc", "ctx")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings")

        self.tree.heading("file", text="file")
        self.tree.heading("type", text="fmt")
        self.tree.heading("loc", text="location")
        self.tree.heading("ctx", text="context")

        self.tree.column("file", width=170)
        self.tree.column("type", width=60, anchor="center")
        self.tree.column("loc", width=150)
        self.tree.column("ctx", width=600)

        scrollbar = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ---- Status bar -------------------------------------------------
        status_frame = tk.Frame(self.root, bg="#000000")
        status_frame.pack(fill="x", side="bottom")

        self.var_status = tk.StringVar(value="[boot] initializing client...")
        lbl_status = tk.Label(
            status_frame,
            textvariable=self.var_status,
            anchor="w",
            bg="#000000",
            fg=self.fg_color,
        )
        lbl_status.pack(fill="x")

    # ------------------------------------------------------------------ #
    #  Networking                                                        #
    # ------------------------------------------------------------------ #

    def start_connection_thread(self) -> None:
        """Spawn a background thread that connects to the server."""
        threading.Thread(target=self.connect_to_server, daemon=True).start()

    def connect_to_server(self) -> None:
        """Connect to the TCP server and update the status bar."""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            self.is_connected = True
            self.var_status.set(
                f"[ok] linked to {SERVER_HOST}:{SERVER_PORT} :: waiting for queries"
            )
        except Exception as error:
            self.is_connected = False
            self.var_status.set(f"[fail] connection error: {error}")
            messagebox.showerror(
                "Network Error",
                "Could not connect to server.\nMake sure server.py is running.",
            )

    # ------------------------------------------------------------------ #
    #  Search handling                                                   #
    # ------------------------------------------------------------------ #

    def on_search(self) -> None:
        """Validate user input and start a background search request."""
        if not self.is_connected or self.client_socket is None:
            messagebox.showwarning("Warning", "Not connected to server.")
            return

        query = self.entry_query.get().strip()
        if not query:
            return

        selected_exts = [ext for ext, var in self.ext_vars.items() if var.get()]

        payload = {
            "query": query,
            "extensions": selected_exts,
            "regex": self.var_regex.get(),
        }

        # Clear old results
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.var_status.set(f"[query] '{query}' :: dispatching to server...")

        threading.Thread(
            target=self.process_request,
            args=(payload,),
            daemon=True,
        ).start()

    def process_request(self, payload: dict) -> None:
        """
        Send the JSON payload to the server and receive the result list.

        Runs in a background thread to keep the GUI responsive.
        """
        assert self.client_socket is not None

        try:
            self.client_socket.sendall(json.dumps(payload).encode("utf-8"))
            self.client_socket.settimeout(2.0)

            data = b""
            while True:
                try:
                    chunk = self.client_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    data += chunk
                    if len(chunk) < BUFFER_SIZE:
                        break
                except socket.timeout:
                    break
            self.client_socket.settimeout(None)

            if data:
                results = json.loads(data.decode("utf-8"))
                self.root.after(0, self.update_results, results)
            else:
                self.root.after(
                    0,
                    lambda: self.var_status.set("[warn] no data received."),
                )

        except Exception as error:
            self.root.after(
                0,
                lambda: self.var_status.set(f"[error] client exception: {error}"),
            )

    def update_results(self, results: list[dict] | None) -> None:
        """
        Populate the Treeview with search results and update the status.
        """
        if results is None:
            results = []

        self.var_status.set(f"[done] {len(results)} matches returned.")

        for res in results:
            self.tree.insert(
                "",
                "end",
                values=(
                    res.get("file", "?"),
                    res.get("type", "?"),
                    res.get("location", "?"),
                    res.get("context", "?"),
                ),
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = SearchApp(root)
    root.mainloop()
