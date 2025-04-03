import os
import re
import yt_dlp
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import requests
from io import BytesIO

QUALITY_OPTIONS = {
    "Low quality (96kbps)": "bestaudio[ext=m4a]/worstaudio[ext=mp3]/bestaudio[abr<=96]",
    "Medium quality (128kbps)": "bestaudio[ext=m4a]/bestaudio[abr<=128]",
    "High quality (320kbps)": "bestaudio[ext=m4a]/bestaudio/bestaudio[abr<=320]"
}

song_queue = []


def add_to_queue():
    url = url_entry.get()
    quality = quality_var.get()

    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    if not quality:
        messagebox.showerror("Error", "Please select an audio quality")
        return

    song_queue.append((url, quality))
    update_list()
    url_entry.delete(0, tk.END)


def update_list():
    queue_list.delete(0, tk.END)
    for i, (url, quality) in enumerate(song_queue):
        queue_list.insert(tk.END, f"{i+1}. {url} - {quality}")


def download_queue():
    if not song_queue:
        messagebox.showerror("Error", "There are no songs in the queue")
        return

    folder = filedialog.askdirectory(title="Select the destination folder")
    if not folder:
        return

    total_songs = len(song_queue)
    song_progress["maximum"] = total_songs
    global_progress["maximum"] = 100

    for i, (url, quality) in enumerate(song_queue):
        song_progress["value"] = i + 1
        download_song(url, quality, folder)
        root.update_idletasks()

    messagebox.showinfo("Success", "All songs have been downloaded")
    song_queue.clear()
    update_list()
    song_progress["value"] = 0
    global_progress["value"] = 0


def download_song(url, quality, folder):
    ydl_opts = {
        "format": QUALITY_OPTIONS[quality],
        "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality.split()[2]},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"}
        ],
        "progress_hooks": [update_progress],
        "noprogress": True,  # Prevents ANSI codes in output
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    download_cover(info, folder)
    organize_files(folder)


def update_progress(d):
    if d["status"] == "downloading":
        percentage = d.get("_percent_str", "0%")

        # Remove ANSI color codes
        percentage = re.sub(r"\x1b\[[0-9;]*m", "", percentage).strip("%")

        try:
            global_progress["value"] = float(percentage)
            root.update_idletasks()
        except ValueError:
            print(f"Error converting percentage: {percentage}")


def download_cover(info, folder):
    thumbnail_url = info.get("thumbnail")
    if not thumbnail_url:
        return

    try:
        response = requests.get(thumbnail_url)
        response.raise_for_status()
        image_data = BytesIO(response.content)

        for root_dir, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".mp3"):
                    file_path = os.path.join(root_dir, file)
                    audio = MP3(file_path, ID3=ID3)
                    audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=image_data.getvalue()))
                    audio.save()
    except Exception as e:
        print(f"Error downloading cover: {e}")


def organize_files(folder):
    for root_dir, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".mp3"):
                file_path = os.path.join(root_dir, file)
                try:
                    audio = MP3(file_path, ID3=ID3)
                    artist = audio.tags.get("TPE1", "Unknown").text[0]
                    album = audio.tags.get("TALB", "Unknown").text[0]

                    album_path = os.path.join(folder, artist, album)
                    os.makedirs(album_path, exist_ok=True)
                    os.rename(file_path, os.path.join(album_path, file))
                except Exception as e:
                    print(f"Error organizing {file}: {e}")


root = tk.Tk()
root.title("SoulDown - S3RGI09")
root.geometry("850x450")
root.configure(bg="#121212")

style = ttk.Style()
style.configure("TButton", font=("Arial", 12), background="#1E90FF", foreground="white")
style.configure("TLabel", font=("Arial", 12), background="#121212", foreground="white")
style.configure("TEntry", font=("Arial", 12), fieldbackground="#1E1E1E", foreground="white")
style.configure("TListbox", font=("Arial", 12), background="#1E1E1E", foreground="white")

# Configure grid
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(2, weight=1)
root.grid_rowconfigure(3, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_rowconfigure(5, weight=1)
root.grid_rowconfigure(6, weight=1)
root.grid_rowconfigure(7, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=3)

ttk.Label(root, text="Song URL:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
url_entry = ttk.Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(root, text="Select audio quality:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
quality_var = tk.StringVar(value="Low quality (96kbps)")  # Corrected initial value
quality_menu = ttk.OptionMenu(root, quality_var, "Medium quality (128kbps)", *QUALITY_OPTIONS.keys())
quality_menu.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="Download queue:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
queue_list = tk.Listbox(root, width=70, height=6, bg="#1E1E1E", fg="white")
queue_list.grid(row=2, column=1, padx=10, pady=5)

ttk.Button(root, text="Add to queue", command=add_to_queue).grid(row=3, column=0, columnspan=2, pady=5)
ttk.Button(root, text="Download queue", command=download_queue).grid(row=4, column=0, columnspan=2, pady=5)

ttk.Label(root, text="Total progress:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
song_progress = ttk.Progressbar(root, length=400)
song_progress.grid(row=5, column=1, padx=10, pady=5)

ttk.Label(root, text="Song progress:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
global_progress = ttk.Progressbar(root, length=400)
global_progress.grid(row=6, column=1, padx=10, pady=5)

root.mainloop()
