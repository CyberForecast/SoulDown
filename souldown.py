import os
import yt_dlp
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import requests
from io import BytesIO

QUALITY_OPTIONS = {
    "Baja calidad (96kbps)": "bestaudio[ext=m4a]/worstaudio[ext=mp3]/bestaudio[abr<=96]",
    "Calidad media (128kbps)": "bestaudio[ext=m4a]/bestaudio[abr<=128]",
    "Alta calidad (320kbps)": "bestaudio[ext=m4a]/bestaudio/bestaudio[abr<=320]"
}

album_queue = []

def agregar_a_cola():
    url = url_entry.get()
    calidad = quality_var.get()

    if not url:
        messagebox.showerror("Error", "Por favor, introduce una URL de YouTube")
        return
    
    if not calidad:
        messagebox.showerror("Error", "Por favor, selecciona una calidad de audio")
        return

    album_queue.append((url, calidad))
    actualizar_lista()
    url_entry.delete(0, tk.END)

def actualizar_lista():
    queue_list.delete(0, tk.END)
    for i, (url, calidad) in enumerate(album_queue):
        queue_list.insert(tk.END, f"{i+1}. {url} - {calidad}")

def descargar_cola():
    if not album_queue:
        messagebox.showerror("Error", "No hay álbumes en cola")
        return

    folder = filedialog.askdirectory(title="Selecciona la carpeta de destino")
    if not folder:
        return

    total_albums = len(album_queue)
    album_progress["maximum"] = total_albums
    global_progress["maximum"] = 100

    for i, (url, calidad) in enumerate(album_queue):
        album_progress["value"] = i
        descargar_album(url, calidad, folder)
        root.update_idletasks()
    
    messagebox.showinfo("Éxito", "Todos los álbumes han sido descargados")
    album_queue.clear()
    actualizar_lista()
    album_progress["value"] = 0
    global_progress["value"] = 0

def descargar_album(url, calidad, folder):
    ydl_opts = {
        "format": QUALITY_OPTIONS[calidad],
        "outtmpl": os.path.join(folder, "%(uploader)s", "%(playlist_title)s", "%(track_number)s - %(title)s.%(ext)s"),
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": calidad.split()[2]},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"}
        ],
        "progress_hooks": [actualizar_progreso]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    
    descargar_caratula(info, folder)
    organizar_archivos(folder)

def actualizar_progreso(d):
    if d["status"] == "downloading":
        porcentaje = d.get("_percent_str", "0%").strip("%")
        global_progress["value"] = float(porcentaje)
        root.update_idletasks()

def descargar_caratula(info, folder):
    thumbnail_url = info.get("thumbnail")
    if not thumbnail_url:
        return

    try:
        response = requests.get(thumbnail_url)
        response.raise_for_status()
        image_data = BytesIO(response.content)

        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".mp3"):
                    file_path = os.path.join(root, file)
                    audio = MP3(file_path, ID3=ID3)
                    audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=image_data.getvalue()))
                    audio.save()
    except Exception as e:
        print(f"Error al descargar carátula: {e}")

def organizar_archivos(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".mp3"):
                file_path = os.path.join(root, file)
                try:
                    audio = MP3(file_path, ID3=ID3)
                    artist = audio.tags.get("TPE1", "Desconocido").text[0]
                    album = audio.tags.get("TALB", "Desconocido").text[0]

                    album_path = os.path.join(folder, artist, album)
                    os.makedirs(album_path, exist_ok=True)
                    os.rename(file_path, os.path.join(album_path, file))
                except Exception as e:
                    print(f"Error organizando {file}: {e}")

root = tk.Tk()
root.title("SoulDown - Descargador de Álbumes")
root.geometry("600x450")
root.configure(bg="#121212")

style = ttk.Style()
style.configure("TButton", font=("Arial", 12), background="#1E90FF", foreground="white")
style.configure("TLabel", font=("Arial", 12), background="#121212", foreground="white")
style.configure("TEntry", font=("Arial", 12), fieldbackground="#1E1E1E", foreground="white")
style.configure("TListbox", font=("Arial", 12), background="#1E1E1E", foreground="white")

ttk.Label(root, text="URL del álbum o playlist:").pack(pady=5)
url_entry = ttk.Entry(root, width=50)
url_entry.pack(pady=5)

ttk.Label(root, text="Selecciona la calidad de audio:").pack(pady=5)
quality_var = tk.StringVar()
quality_menu = ttk.OptionMenu(root, quality_var, *QUALITY_OPTIONS.keys())
quality_menu.pack(pady=5)

ttk.Label(root, text="Cola de descargas:").pack(pady=5)
queue_list = tk.Listbox(root, width=70, height=6, bg="#1E1E1E", fg="white")
queue_list.pack(pady=5)

ttk.Button(root, text="Agregar a la cola", command=agregar_a_cola).pack(pady=5)
ttk.Button(root, text="Descargar cola", command=descargar_cola).pack(pady=5)

ttk.Label(root, text="Progreso del álbum actual:").pack(pady=5)
album_progress = ttk.Progressbar(root, length=400)
album_progress.pack(pady=5)

ttk.Label(root, text="Progreso total:").pack(pady=5)
global_progress = ttk.Progressbar(root, length=400)
global_progress.pack(pady=5)

root.mainloop()
