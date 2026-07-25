import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import yt_dlp
import threading
import os
import re
import sys

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        # ffmpeg
        base = sys._MEIPASS
        return os.path.join(base, "ffmpeg.exe")
    return "ffmpeg"  # Linux/dev mode — system ffmpeg

class ProDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader")
        self.root.geometry("650x650")
        self.root.configure(bg="#f0f0f0")

        header_frame = tk.Frame(root, bg="#2980b9", height=60)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="All DOWNLOADER", font=('Arial', 16, 'bold'), fg="white", bg="#2980b9").pack(pady=15)

        tk.Label(root, text="URL:", font=('Arial', 12, 'bold'), bg="#f0f0f0").pack(pady=(15, 5))
        self.url_input = tk.Entry(root, width=55, font=('Arial', 11))
        self.url_input.pack(pady=2)

        self.settings_frame = tk.Frame(root, bg="#f0f0f0")
        self.settings_frame.pack(pady=15)

        tk.Label(self.settings_frame, text="Res:", font=('Arial', 11), bg="#f0f0f0").grid(row=0, column=0)
        self.res_var = tk.StringVar(value="1080")
        res_box = ttk.Combobox(self.settings_frame, textvariable=self.res_var,
                               values=["4320", "2160", "1440", "1080", "720", "480", "360"],
                               width=7, state="readonly", font=('Arial', 10))
        res_box.grid(row=0, column=1, padx=5)

        tk.Label(self.settings_frame, text="Start:", font=('Arial', 11), bg="#f0f0f0").grid(row=0, column=2, padx=5)
        self.start_idx = tk.Entry(self.settings_frame, width=5, font=('Arial', 10))
        self.start_idx.insert(0, "1")
        self.start_idx.grid(row=0, column=3)

        tk.Label(self.settings_frame, text="End:", font=('Arial', 11), bg="#f0f0f0").grid(row=0, column=4, padx=5)
        self.end_idx = tk.Entry(self.settings_frame, width=5, font=('Arial', 10))
        self.end_idx.insert(0, "")
        self.end_idx.grid(row=0, column=5)

        self.folder_path = tk.StringVar(value=os.path.expanduser("~/Videos"))
        tk.Button(root, text="Select Folder", font=('Arial', 10, 'bold'), command=self.browse).pack(pady=5)
        tk.Label(root, textvariable=self.folder_path, fg="#2980b9", font=('Arial', 10, 'italic'),
                 bg="#f0f0f0", wraplength=550).pack()

        self.total_label = tk.Label(root, text="Status: Ready to go", fg="#8e44ad",
                                    font=('Arial', 12, 'bold'), bg="#f0f0f0")
        self.total_label.pack(pady=10)

        self.file_label = tk.Label(root, text='', wraplength=580, fg="#2c3e50",
                                   font=('Arial', 10, 'bold'), bg="#f0f0f0")
        self.file_label.pack(pady=5)

        self.prog_frame = tk.Frame(root, bg="#f0f0f0")
        self.prog_frame.pack(pady=10)
        self.progress_bar = ttk.Progressbar(self.prog_frame, length=480, mode='determinate')
        self.progress_bar.grid(row=0, column=0, padx=10)
        self.percent_label = tk.Label(self.prog_frame, text="0.00%", font=('Arial', 12, 'bold'), bg="#f0f0f0")
        self.percent_label.grid(row=0, column=1)

        self.stats_label = tk.Label(root, text="Speed: 0 MiB/s \t ETA: 00:00\nItem: 0 / 0",
                                    font=('Courier', 12, 'bold'), justify=tk.LEFT,
                                    bg="#ecf0f1", padx=10, pady=10, relief=tk.RIDGE)
        self.stats_label.pack(pady=15)

        self.download_btn = tk.Button(root, text="START DOWNLOAD", bg="#27ae60", fg="white",
                                      font=('Arial', 13, 'bold'), width=25,
                                      command=self.run_thread, cursor="hand2")
        self.download_btn.pack(pady=5)
        tk.Button(root, text="STOP", bg="#c0392b", fg="white", font=('Arial', 11, 'bold'),
                  width=25, command=lambda: os._exit(0), cursor="hand2").pack(pady=5)

    def browse(self):
        path = filedialog.askdirectory(initialdir=self.folder_path.get())
        if path:
            os.makedirs(path, exist_ok=True)
            self.folder_path.set(path)

    def clean_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def hook(self, d):
        if d['status'] == 'downloading':
            total_b = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total_b:
                p_val = (downloaded / total_b) * 100
                self.progress_bar['value'] = p_val
                self.percent_label.config(text=f"{p_val:.2f}%")

            info = d.get('info_dict', {})
            current = info.get('playlist_index') or d.get('playlist_index', 1)
            total_v = info.get('n_entries') or d.get('playlist_count', 1)

            fname = os.path.basename(d.get('filename', 'Unknown'))
            speed = self.clean_ansi(d.get('_speed_str', '0 MiB/s'))
            eta = self.clean_ansi(d.get('_eta_str', '00:00'))

            self.total_label.config(text=f"Processing: {current} of {total_v}")
            self.file_label.config(text=f"File: {fname}", font=('Arial', 10, 'bold'))
            self.stats_label.config(text=f"SPEED: {speed.strip()} \t ETA: {eta.strip()} \nPROGRESS: Item {current} of {total_v}")
            self.root.update_idletasks()

        elif d['status'] == 'finished':
            self.progress_bar['value'] = 100
            self.percent_label.config(text="100.00%")

    def download_logic(self):
        url = self.url_input.get().strip()
        if not url:
            return

        start = self.start_idx.get().strip() or "1"
        end = self.end_idx.get().strip()
        p_items = f"{start}-{end}" if end else f"{start}-"

        ydl_opts = {
            'ignoreerrors': True,
            'format': f'bestvideo[height<={self.res_var.get()}]+bestaudio/best',
            'outtmpl': os.path.join(self.folder_path.get(), '%(title).150s (%(height)sp).%(ext)s'),
            'progress_hooks': [self.hook],
            'playlist_items': p_items,
            'color': 'no_color',
            'ffmpeg_location': get_ffmpeg_path(),  # bundled ffmpeg.exe
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Success", "Download Completed!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.download_btn.config(state='normal')

    def run_thread(self):
        self.download_btn.config(state='disabled')
        threading.Thread(target=self.download_logic, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProDownloader(root)
    root.mainloop()
