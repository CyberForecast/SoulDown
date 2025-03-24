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
    "Baja calidad (96kbps)": "bestaudio[ext=m4a]/worstaudio[ext=mp3]/bestaudio[abr<=96]",
    "Calidad media (128kbps)": "bestaudio[ext=m4a]/bestaudio[abr<=128]",
    "Alta calidad (320kbps)": "bestaudio[ext=m4a]/bestaudio/bestaudio[abr<=320]"
}

song_queue = []


def agregar_a_cola():
    url = url_entry.get()
    calidad = quality_var.get()

    if not url:
        messagebox.showerror("Error", "Por favor, introduce una URL de YouTube")
        return

    if not calidad:
        messagebox.showerror("Error", "Por favor, selecciona una calidad de audio")
        return

    song_queue.append((url, calidad))
    actualizar_lista()
    url_entry.delete(0, tk.END)


def actualizar_lista():
    queue_list.delete(0, tk.END)
    for i, (url, calidad) in enumerate(song_queue):
        queue_list.insert(tk.END, f"{i+1}. {url} - {calidad}")


def descargar_cola():
    if not song_queue:
        messagebox.showerror("Error", "No hay canciones en cola")
        return

    folder = filedialog.askdirectory(title="Selecciona la carpeta de destino")
    if not folder:
        return

    total_songs = len(song_queue)
    song_progress["maximum"] = total_songs
    global_progress["maximum"] = 100

    for i, (url, calidad) in enumerate(song_queue):
        song_progress["value"] = i + 1
        descargar_cancion(url, calidad, folder)
        root.update_idletasks()

    messagebox.showinfo("Éxito", "Todas las canciones han sido descargadas")
    song_queue.clear()
    actualizar_lista()
    song_progress["value"] = 0
    global_progress["value"] = 0


def descargar_cancion(url, calidad, folder):
    ydl_opts = {
        "format": QUALITY_OPTIONS[calidad],
        "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": calidad.split()[2]},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"}
        ],
        "progress_hooks": [actualizar_progreso],
        "noprogress": True,  # Evita códigos ANSI en la salida
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    descargar_caratula(info, folder)
    organizar_archivos(folder)


def actualizar_progreso(d):
    if d["status"] == "downloading":
        porcentaje = d.get("_percent_str", "0%")

        # Eliminar códigos de color ANSI
        porcentaje = re.sub(r"\x1b\[[0-9;]*m", "", porcentaje).strip("%")

        try:
            global_progress["value"] = float(porcentaje)
            root.update_idletasks()
        except ValueError:
            print(f"Error al convertir porcentaje: {porcentaje}")


def descargar_caratula(info, folder):
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
        print(f"Error al descargar carátula: {e}")


def organizar_archivos(folder):
    for root_dir, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".mp3"):
                file_path = os.path.join(root_dir, file)
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
root.title("SoulDown - S3RGI09")
root.geometry("600x450")
root.configure(bg="#121212")

style = ttk.Style()
style.configure("TButton", font=("Arial", 12), background="#1E90FF", foreground="white")
style.configure("TLabel", font=("Arial", 12), background="#121212", foreground="white")
style.configure("TEntry", font=("Arial", 12), fieldbackground="#1E1E1E", foreground="white")
style.configure("TListbox", font=("Arial", 12), background="#1E1E1E", foreground="white")

# Configurar el grid
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

ttk.Label(root, text="URL de la canción:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
url_entry = ttk.Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(root, text="Selecciona la calidad de audio:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
quality_var = tk.StringVar()
quality_menu = ttk.OptionMenu(root, quality_var, *QUALITY_OPTIONS.keys())
quality_menu.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="Cola de descargas:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
queue_list = tk.Listbox(root, width=70, height=6, bg="#1E1E1E", fg="white")
queue_list.grid(row=2, column=1, padx=10, pady=5)

ttk.Button(root, text="Agregar a la cola", command=agregar_a_cola).grid(row=3, column=0, columnspan=2, pady=5)
ttk.Button(root, text="Descargar cola", command=descargar_cola).grid(row=4, column=0, columnspan=2, pady=5)

ttk.Label(root, text="Progreso total:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
song_progress = ttk.Progressbar(root, length=400)
song_progress.grid(row=5, column=1, padx=10, pady=5)

ttk.Label(root, text="Progreso de la cancion:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
global_progress = ttk.Progressbar(root, length=400)
global_progress.grid(row=6, column=1, padx=10, pady=5)

root.mainloop()
