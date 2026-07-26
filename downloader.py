import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import yt_dlp
import threading
import os
import re
import sys
import json
import subprocess
import platform
import webbrowser

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".video_downloader_config.json")

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        return os.path.join(base, "ffmpeg.exe")
    return "ffmpeg"

def open_folder_in_manager(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open folder:\n{e}")

# ── Color Palette (Light / White Mode) ─────────────────────
BG       = "#f5f7fa"
SURFACE  = "#ffffff"
SURFACE2 = "#eef1f6"
ACCENT   = "#2563eb"
ACCENT2  = "#7c3aed"
SUCCESS  = "#16a34a"
WARNING  = "#d97706"
DANGER   = "#dc2626"
TEXT_PRI = "#111827"
TEXT_SEC = "#6b7280"
BORDER   = "#d1d5db"

MIN_W    = 500


class ProDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("StreamGet —Video Downloader")
        # Set window icon
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "logo.ico")
            else:
                icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
            self.root.iconbitmap(icon_path)
        except:
            pass

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        win_w = MIN_W
        win_h = sh - 120
        x = (sw - win_w) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+0")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(MIN_W, 500)

        self._paused = False
        self._pause_event = threading.Event()
        self._pause_event.set()

        config = load_config()
        default_folder = config.get("last_folder", os.path.expanduser("~/Videos"))
        self._build_ui(default_folder)

    def _build_ui(self, default_folder):
        root = self.root

        # ── Top accent bar ──────────────────────────────────
        tk.Frame(root, bg=ACCENT, height=4).pack(fill=tk.X)

        # ── Header ─────────────────────────────────────────
        header = tk.Frame(root, bg=SURFACE, pady=18)
        header.pack(fill=tk.X)
        tk.Label(header, text="Stream", font=('Arial', 22, 'bold'),
                 fg=TEXT_PRI, bg=SURFACE).pack(side=tk.LEFT, padx=(28, 0))
        tk.Label(header, text="Get", font=('Arial', 22, 'bold'),
                 fg=ACCENT, bg=SURFACE).pack(side=tk.LEFT)
        tk.Label(header, text="  ·  Video Downloader", font=('Arial', 11),
                 fg=TEXT_SEC, bg=SURFACE).pack(side=tk.LEFT, padx=(4, 0))
        tk.Label(header, text=" v2.0 ", font=('Arial', 8, 'bold'),
                 fg=ACCENT, bg=SURFACE2, padx=4, pady=2).pack(side=tk.RIGHT, padx=24)
        tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Developer footer (pinned to bottom) ─────────────
        tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X, side=tk.BOTTOM)
        footer = tk.Frame(root, bg=SURFACE, pady=14, padx=24)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        left_col = tk.Frame(footer, bg=SURFACE)
        left_col.pack(side=tk.LEFT)
        tk.Label(left_col, text="Developed by", font=('Arial', 8),
                 fg=TEXT_SEC, bg=SURFACE).pack(anchor='w')
        tk.Label(left_col, text="Md. Imran Ali", font=('Arial', 11, 'bold'),
                 fg=TEXT_PRI, bg=SURFACE).pack(anchor='w')

        link_row = tk.Frame(left_col, bg=SURFACE)
        link_row.pack(anchor='w', pady=(6, 0))
        self._footer_link(link_row, "  GitHub  ",
                          "https://github.com/Imran-Ali-101/", "#24292e").pack(side=tk.LEFT, padx=(0, 6))
        self._footer_link(link_row, "  LinkedIn  ",
                          "https://www.linkedin.com/in/imran-ali101/", "#0a66c2").pack(side=tk.LEFT, padx=(0, 6))
        self._footer_link(link_row, "  Email  ",
                          "mailto:imran.28279@gmail.com", "#ea4335").pack(side=tk.LEFT)

        tk.Label(footer, text="StreamGet v2.0", font=('Arial', 8),
                 fg=TEXT_SEC, bg=SURFACE).pack(side=tk.RIGHT, anchor='se')

        # ── Scrollable content area ──────────────────────────
        canvas_frame = tk.Frame(root, bg=BG)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = tk.Frame(self.canvas, bg=BG)
        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.inner.bind("<Configure>",  self._on_inner_resize)

        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        self.canvas.bind_all("<Button-4>",
                             lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>",
                             lambda e: self.canvas.yview_scroll(1, "units"))

        self._build_content(self.inner, default_folder)

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_inner_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _build_content(self, content, default_folder):
        tk.Frame(content, bg=BG, height=20).pack()

        wrap = tk.Frame(content, bg=BG, padx=24)
        wrap.pack(fill=tk.X)

        # ── VIDEO URL ───────────────────────────────────────
        self._section_label(wrap, "VIDEO URL")
        url_frame = tk.Frame(wrap, bg=SURFACE2, highlightbackground=BORDER,
                             highlightthickness=1)
        url_frame.pack(fill=tk.X, pady=(6, 16))
        tk.Label(url_frame, text="🔗", font=('Arial', 13), bg=SURFACE2,
                 fg=TEXT_SEC).pack(side=tk.LEFT, padx=(12, 6), pady=10)
        self.url_input = tk.Entry(url_frame, font=('Arial', 11), bg=SURFACE2,
                                  fg=TEXT_SEC, insertbackground=ACCENT,
                                  relief=tk.FLAT, bd=0)
        self.url_input.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=10, padx=(0, 12))
        self.url_input.insert(0, "Paste YouTube / playlist URL here...")
        self.url_input.bind("<FocusIn>",  self._url_focus_in)
        self.url_input.bind("<FocusOut>", self._url_focus_out)

        # ── DOWNLOAD SETTINGS ───────────────────────────────
        self._section_label(wrap, "DOWNLOAD SETTINGS")
        settings_outer = tk.Frame(wrap, bg=SURFACE, highlightbackground=BORDER,
                                  highlightthickness=1, pady=14, padx=16)
        settings_outer.pack(fill=tk.X, pady=(6, 16))

        col1 = tk.Frame(settings_outer, bg=SURFACE)
        col1.pack(side=tk.LEFT, expand=True)
        tk.Label(col1, text="QUALITY", font=('Arial', 8, 'bold'),
                 fg=TEXT_SEC, bg=SURFACE).pack(anchor='w')
        self.res_var = tk.StringVar(value="1080")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Dark.TCombobox",
                        fieldbackground=SURFACE2, background=SURFACE2,
                        foreground=TEXT_PRI, arrowcolor=ACCENT,
                        bordercolor=BORDER, lightcolor=SURFACE2,
                        darkcolor=BORDER, relief="flat")
        ttk.Combobox(col1, textvariable=self.res_var,
                     values=["4320","2160","1440","1080","720","480","360"],
                     width=8, state="readonly", style="Dark.TCombobox",
                     font=('Arial', 11)).pack(anchor='w', pady=(4, 0))

        tk.Frame(settings_outer, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=20)

        col2 = tk.Frame(settings_outer, bg=SURFACE)
        col2.pack(side=tk.LEFT, expand=True)
        tk.Label(col2, text="PLAYLIST RANGE", font=('Arial', 8, 'bold'),
                 fg=TEXT_SEC, bg=SURFACE).pack(anchor='w')
        range_row = tk.Frame(col2, bg=SURFACE)
        range_row.pack(anchor='w', pady=(4, 0))
        tk.Label(range_row, text="From", font=('Arial', 10),
                 fg=TEXT_SEC, bg=SURFACE).pack(side=tk.LEFT)
        self.start_idx = self._mini_entry(range_row, "1")
        tk.Label(range_row, text="To", font=('Arial', 10),
                 fg=TEXT_SEC, bg=SURFACE).pack(side=tk.LEFT, padx=(10, 0))
        self.end_idx = self._mini_entry(range_row, "")
        tk.Label(range_row, text="(blank = all)", font=('Arial', 8),
                 fg=TEXT_SEC, bg=SURFACE).pack(side=tk.LEFT, padx=(6, 0))

        # ── SAVE LOCATION ───────────────────────────────────
        self._section_label(wrap, "SAVE LOCATION")
        self.folder_path = tk.StringVar(value=default_folder)
        folder_card = tk.Frame(wrap, bg=SURFACE, highlightbackground=BORDER,
                               highlightthickness=1, pady=10, padx=14)
        folder_card.pack(fill=tk.X, pady=(6, 16))
        tk.Label(folder_card, text="📂", font=('Arial', 14),
                 bg=SURFACE, fg=TEXT_PRI).pack(side=tk.LEFT, padx=(0, 10))
        self.folder_label = tk.Label(folder_card, textvariable=self.folder_path,
                                     fg=ACCENT, font=('Arial', 10),
                                     bg=SURFACE, anchor='w', wraplength=200)
        self.folder_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.folder_label.bind("<Configure>",
                               lambda e: self.folder_label.config(wraplength=max(60, e.width - 10)))
        btn_frame = tk.Frame(folder_card, bg=SURFACE)
        btn_frame.pack(side=tk.RIGHT)
        self._small_btn(btn_frame, "Browse",  self.browse,      SURFACE2).pack(side=tk.LEFT, padx=4)
        self._small_btn(btn_frame, "Open ↗",  self.open_folder, SURFACE2).pack(side=tk.LEFT)

        # ── STATUS ──────────────────────────────────────────
        status_card = tk.Frame(wrap, bg=SURFACE, highlightbackground=BORDER,
                               highlightthickness=1, pady=14, padx=16)
        status_card.pack(fill=tk.X, pady=(0, 14))
        self.status_dot = tk.Label(status_card, text="●", font=('Arial', 10),
                                   fg=TEXT_SEC, bg=SURFACE)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        self.total_label = tk.Label(status_card, text="Ready to download",
                                    fg=TEXT_PRI, font=('Arial', 11, 'bold'), bg=SURFACE)
        self.total_label.pack(side=tk.LEFT)
        self.stats_label = tk.Label(status_card, text="",
                                    fg=TEXT_SEC, font=('Arial', 9), bg=SURFACE)
        self.stats_label.pack(side=tk.RIGHT)

        # Current file name
        self.file_label = tk.Label(wrap, text="", fg=TEXT_SEC,
                                   font=('Arial', 9), bg=BG, anchor='w', wraplength=300)
        self.file_label.pack(fill=tk.X, pady=(0, 8))
        self.file_label.bind("<Configure>",
                             lambda e: self.file_label.config(wraplength=max(60, e.width - 10)))

        # ── PROGRESS BAR ────────────────────────────────────
        prog_frame = tk.Frame(wrap, bg=BG)
        prog_frame.pack(fill=tk.X, pady=(0, 16))
        style.configure("Accent.Horizontal.TProgressbar",
                        troughcolor=SURFACE2, background=ACCENT,
                        bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT2)
        self.progress_bar = ttk.Progressbar(prog_frame, mode='determinate',
                                            style="Accent.Horizontal.TProgressbar")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.percent_label = tk.Label(prog_frame, text="0%", font=('Arial', 10, 'bold'),
                                      fg=ACCENT, bg=BG, width=5)
        self.percent_label.pack(side=tk.LEFT, padx=(10, 0))

        # ── ACTION BUTTONS ──────────────────────────────────
        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill=tk.X, pady=(4, 0))

        self.download_btn = tk.Button(btn_row, text="▶  START DOWNLOAD",
                                      bg=ACCENT, fg="white",
                                      font=('Arial', 12, 'bold'),
                                      relief=tk.FLAT, bd=0, pady=12,
                                      activebackground=ACCENT2, activeforeground="white",
                                      cursor="hand2", command=self.run_thread)
        self.download_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))

        self.pause_btn = tk.Button(btn_row, text="⏸  PAUSE",
                                   bg=SURFACE2, fg=WARNING,
                                   font=('Arial', 11, 'bold'),
                                   relief=tk.FLAT, bd=0, pady=12,
                                   activebackground=SURFACE, activeforeground=WARNING,
                                   cursor="hand2", state='disabled',
                                   command=self.toggle_pause, width=10)
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(btn_row, text="⏹  STOP",
                  bg=SURFACE2, fg=DANGER,
                  font=('Arial', 11, 'bold'),
                  relief=tk.FLAT, bd=0, pady=12,
                  activebackground=SURFACE, activeforeground=DANGER,
                  cursor="hand2", command=self.stop_download,
                  width=10).pack(side=tk.LEFT)

        tk.Frame(content, bg=BG, height=20).pack()

    # ── UI Helpers ───────────────────────────────────────────

    def _section_label(self, parent, text):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill=tk.X)
        tk.Label(row, text=text, font=('Arial', 8, 'bold'),
                 fg=TEXT_SEC, bg=BG).pack(side=tk.LEFT)
        tk.Frame(row, bg=BORDER, height=1).pack(side=tk.LEFT, fill=tk.X,
                                                expand=True, padx=(8, 0), pady=6)

    def _mini_entry(self, parent, default):
        e = tk.Entry(parent, width=5, font=('Arial', 11),
                     bg=SURFACE2, fg=TEXT_PRI, insertbackground=ACCENT,
                     relief=tk.FLAT, bd=0,
                     highlightbackground=BORDER, highlightthickness=1)
        e.insert(0, default)
        e.pack(side=tk.LEFT, padx=(6, 0), ipady=4, ipadx=4)
        return e

    def _small_btn(self, parent, text, cmd, bg):
        return tk.Button(parent, text=text, font=('Arial', 9, 'bold'),
                         fg=TEXT_SEC, bg=bg, relief=tk.FLAT, bd=0,
                         padx=10, pady=5, cursor="hand2",
                         activebackground=BORDER, activeforeground=TEXT_PRI,
                         command=cmd)

    def _footer_link(self, parent, text, url, color):
        btn = tk.Label(parent, text=text, font=('Arial', 8, 'bold'),
                       fg="white", bg=color, cursor="hand2", padx=6, pady=4)
        btn.bind("<Button-1>", lambda e: webbrowser.open(url))
        btn.bind("<Enter>",    lambda e: btn.config(bg=ACCENT))
        btn.bind("<Leave>",    lambda e: btn.config(bg=color))
        return btn

    def _url_focus_in(self, e):
        if self.url_input.get() == "Paste YouTube / playlist URL here...":
            self.url_input.delete(0, tk.END)
            self.url_input.config(fg=TEXT_PRI)

    def _url_focus_out(self, e):
        if not self.url_input.get():
            self.url_input.insert(0, "Paste YouTube / playlist URL here...")
            self.url_input.config(fg=TEXT_SEC)

    # ── Actions ──────────────────────────────────────────────

    def browse(self):
        path = filedialog.askdirectory(initialdir=self.folder_path.get())
        if path:
            os.makedirs(path, exist_ok=True)
            self.folder_path.set(path)
            save_config({"last_folder": path})

    def open_folder(self):
        path = self.folder_path.get()
        if os.path.exists(path):
            open_folder_in_manager(path)
        else:
            messagebox.showwarning("Warning", "Folder does not exist yet!")

    def clean_ansi(self, text):
        return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)

    def hook(self, d):
        # Block here when paused — resumes when pause_event is set again
        self._pause_event.wait()

        if d['status'] == 'downloading':
            total_b    = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)

            # Calculate MB values for display
            if total_b:
                p_val    = (downloaded / total_b) * 100
                total_mb = total_b / 1024 / 1024
                done_mb  = downloaded / 1024 / 1024
                self.progress_bar['value'] = p_val
                self.percent_label.config(text=f"{p_val:.0f}%")
            else:
                total_mb = 0
                done_mb  = downloaded / 1024 / 1024

            info    = d.get('info_dict', {})
            current = info.get('playlist_index') or d.get('playlist_index', 1)
            total_v = info.get('n_entries')      or d.get('playlist_count', 1)
            fname   = os.path.basename(d.get('filename', ''))
            speed   = self.clean_ansi(d.get('_speed_str', '—'))
            eta     = self.clean_ansi(d.get('_eta_str',   '—'))

            if self._paused:
                self.total_label.config(text="Paused", fg=WARNING)
                self.status_dot.config(fg=WARNING)
            else:
                self.total_label.config(text=f"Downloading...  {current} / {total_v}", fg=TEXT_PRI)
                self.status_dot.config(fg=ACCENT)

            self.file_label.config(text=f"↓  {fname}" if fname else "")
            self.stats_label.config(
                text=f"{speed.strip()}  ·  ETA {eta.strip()}  ·  {done_mb:.1f} / {total_mb:.1f} MB  ·  Item {current} / {total_v}"
            )
            self.root.update_idletasks()

        elif d['status'] == 'finished':
            self.progress_bar['value'] = 100
            self.percent_label.config(text="100%")

    def toggle_pause(self):
        if not self._paused:
            self._paused = True
            self._pause_event.clear()
            self.pause_btn.config(text="▶  RESUME", fg=SUCCESS)
        else:
            self._paused = False
            self._pause_event.set()
            self.pause_btn.config(text="⏸  PAUSE", fg=WARNING)

    def stop_download(self):
        self._pause_event.set()
        os._exit(0)

    def download_logic(self):
        url = self.url_input.get().strip()
        if not url or url == "Paste YouTube / playlist URL here...":
            self.download_btn.config(state='normal')
            self.pause_btn.config(state='disabled')
            return

        start   = self.start_idx.get().strip() or "1"
        end     = self.end_idx.get().strip()
        p_items = f"{start}-{end}" if end else f"{start}-"

        self.status_dot.config(fg=ACCENT)
        self.total_label.config(text="Connecting...", fg=TEXT_PRI)

        ydl_opts = {
            'ignoreerrors': True,
            'format':       f'bestvideo[height<={self.res_var.get()}]+bestaudio/best',
            'outtmpl':      os.path.join(self.folder_path.get(),
                                         '%(title).150s (%(height)sp).%(ext)s'),
            'progress_hooks': [self.hook],
            'playlist_items': p_items,
            'color':          'no_color',
            'ffmpeg_location': get_ffmpeg_path(),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.total_label.config(text="Download complete ✓", fg=SUCCESS)
            self.status_dot.config(fg=SUCCESS)
            self.progress_bar['value'] = 100
            self.percent_label.config(text="100%")
            messagebox.showinfo("Done!", "Download completed successfully!")
        except Exception as e:
            self.total_label.config(text="Error occurred", fg=DANGER)
            self.status_dot.config(fg=DANGER)
            messagebox.showerror("Error", str(e))
        finally:
            self.download_btn.config(state='normal')
            self.pause_btn.config(state='disabled', text="⏸  PAUSE", fg=WARNING)
            self._paused = False
            self._pause_event.set()

    def run_thread(self):
        self._paused = False
        self._pause_event.set()
        self.progress_bar['value'] = 0
        self.percent_label.config(text="0%")
        self.download_btn.config(state='disabled')
        self.pause_btn.config(state='normal')
        threading.Thread(target=self.download_logic, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ProDownloader(root)
    root.mainloop()
