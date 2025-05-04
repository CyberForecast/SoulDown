# -*- coding: utf-8 -*-
"""
SoulDown - Stable v1.0
- By S3RGI09
"""
import os
import re
import uuid
from io import BytesIO
from pathlib import Path

# For Wayland compatibility
os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')

import requests
import yt_dlp
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from mutagen.mp3 import MP3
from PyQt5 import QtCore, QtWidgets, QtGui

# Soportes
AUDIO_EXTS = ['mp3', 'aac', 'opus']
VIDEO_EXTS = ['mp4', 'avi']

class DownloadWorker(QtCore.QThread):
    songProgress = QtCore.pyqtSignal(int, int)
    fileProgress = QtCore.pyqtSignal(int)
    finishedAll = QtCore.pyqtSignal()
    errorOccurred = QtCore.pyqtSignal(str)

    def __init__(self, queue, output_folder):
        super().__init__()
        self.queue = queue
        self.output = Path(output_folder)
        self.temp = self.output / 'temp'
        self.temp.mkdir(exist_ok=True)
        self.current_progress = 0

    def run(self):
        expanded_queue = []
        for url, ftype, ext, quality in self.queue:
            # Check if it's a playlist
            ydl_opts = {'quiet': True, 'extract_flat': 'in_playlist', 'force_generic_extractor': False}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        for entry in info['entries']:
                            expanded_queue.append((entry['url'], ftype, ext, quality))
                    else:
                        expanded_queue.append((url, ftype, ext, quality))
                except Exception as e:
                    self.errorOccurred.emit(f"Error leyendo {url}: {e}")

        total = len(expanded_queue)
        for idx, (url, ftype, ext, quality) in enumerate(expanded_queue, start=1):
            self.songProgress.emit(idx, total)
            try:
                self.download_item(url, ftype, ext, quality)
            except Exception as e:
                self.errorOccurred.emit(f"Error en {url}: {e}")

        for f in self.temp.glob('*'): f.unlink()
        self.temp.rmdir()
        self.finishedAll.emit()

    def download_item(self, url, ftype, ext, quality):
        def hook(d):
            if d.get('status') == 'downloading':
                pct = d.get('_percent_str', '0%').strip('%')
                try:
                    val = int(float(pct))
                    self.fileProgress.emit(val)
                except:
                    pass

        class Logger:
            def debug(self, msg):
                match = re.search(r'\[download\]\s+(\d{1,3}\.\d+)%', msg)
                if match:
                    try:
                        pct = int(float(match.group(1)))
                        self.fileProgress.emit(pct)
                    except:
                        pass
            def warning(self, msg): pass
            def error(self, msg): pass

        ydl_opts = {
            'quiet': True,
            'logger': Logger(),
            'progress_hooks': [hook],
            'outtmpl': str(self.temp / '%(id)s.%(ext)s'),
        }
        if ftype == 'Audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ext,
                'preferredquality': quality
            }]
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = ext

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except yt_dlp.utils.DownloadError:
                if ftype == 'Audio':
                    ydl_opts['format'] = 'bestaudio'
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(url, download=True)
                else:
                    raise

        file_id = info['id']
        src = next(self.temp.glob(f"{file_id}.*"))
        if ftype == 'Audio':
            self.embed_cover(info, src)
        self.organize(info, src)

    def embed_cover(self, info, path):
        thumb = info.get('thumbnail')
        if not thumb: return
        try:
            data = requests.get(thumb, timeout=10).content
            audio = MP3(path, ID3=ID3)
            try: audio.add_tags()
            except ID3NoHeaderError: pass
            audio.tags.add(APIC(3, 'image/jpeg', 3, 'Cover', data))
            audio.save()
        except: pass

    def organize(self, info, src):
        title = info.get('title') or src.stem
        artist = info.get('artist') or info.get('uploader', 'Unknown')
        main = re.split(r'\s+ft\.?\s+', artist, flags=re.I)[0]
        album = info.get('album') or 'Unknown Album'
        dest_dir = self.output / main / album
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{main} - {album} - {title}{src.suffix}"
        if dest.exists():
            dest = dest_dir / f"{dest.stem}_{uuid.uuid4().hex[:6]}{src.suffix}"
        src.rename(dest)

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SoulDown - Stable v2.3")
        self.resize(800, 500)
        self.apply_styles()
        self.queue = []
        self.setup_ui()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #000000; color: #FFFFFF; }
            QLineEdit, QComboBox, QListWidget { background-color: #121212; selection-background-color: #1E90FF; }
            QPushButton { background-color: #1E90FF; color: #000000; border-radius: 5px; padding: 5px; }
            QPushButton:hover { background-color: #5599FF; }
            QProgressBar { background-color: #121212; border: 1px solid #1E90FF; border-radius: 5px; }
            QProgressBar::chunk { background-color: #1E90FF; }
        """)

    def setup_ui(self):
        grid = QtWidgets.QGridLayout(self)
        grid.addWidget(QtWidgets.QLabel("URL:"), 0, 0)
        self.url_input = QtWidgets.QLineEdit()
        grid.addWidget(self.url_input, 0, 1, 1, 3)
        self.type_box = QtWidgets.QComboBox(); self.type_box.addItems(['Audio', 'Video'])
        self.ext_box = QtWidgets.QComboBox(); self.ext_box.addItems(AUDIO_EXTS)
        self.qual_box = QtWidgets.QComboBox(); self.qual_box.addItems(['Low', 'Medium', 'High'])
        grid.addWidget(self.type_box, 1, 0)
        grid.addWidget(self.ext_box, 1, 1)
        grid.addWidget(self.qual_box, 1, 2)
        self.add_btn = QtWidgets.QPushButton("Add to Queue")
        grid.addWidget(self.add_btn, 1, 3)
        grid.addWidget(QtWidgets.QLabel("Queue:"), 2, 0)
        self.queue_list = QtWidgets.QListWidget()
        grid.addWidget(self.queue_list, 3, 0, 1, 4)
        self.download_btn = QtWidgets.QPushButton("Download All")
        grid.addWidget(self.download_btn, 4, 0, 1, 4)
        grid.addWidget(QtWidgets.QLabel("Overall Progress:"), 5, 0)
        self.overall_pb = QtWidgets.QProgressBar()
        grid.addWidget(self.overall_pb, 5, 1, 1, 3)
        grid.addWidget(QtWidgets.QLabel("File Progress:"), 6, 0)
        self.file_pb = QtWidgets.QProgressBar()
        grid.addWidget(self.file_pb, 6, 1, 1, 3)
        self.add_btn.clicked.connect(self.add_to_queue)
        self.download_btn.clicked.connect(self.start_download)
        self.type_box.currentTextChanged.connect(self.update_ext)

    def update_ext(self, text):
        self.ext_box.clear(); self.qual_box.clear()
        if text == 'Audio':
            self.ext_box.addItems(AUDIO_EXTS)
            self.qual_box.addItems(['Low', 'Medium', 'High'])
        else:
            self.ext_box.addItems(VIDEO_EXTS)
            self.qual_box.addItems(['360p', '720p', '1080p'])

    def add_to_queue(self):
        url = self.url_input.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "Error", "Enter URL")
            return
        ftype = self.type_box.currentText()
        ext = self.ext_box.currentText()
        quality = self.qual_box.currentText()
        self.queue.append((url, ftype, ext, quality))
        self.queue_list.addItem(f"{ftype} | {ext} | {quality} | {url}")
        self.url_input.clear()

    def start_download(self):
        if not self.queue:
            QtWidgets.QMessageBox.warning(self, "Error", "Queue empty")
            return
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        self.overall_pb.setMaximum(1)  # Placeholder
        self.file_pb.setMaximum(100)
        self.worker = DownloadWorker(self.queue, folder)
        self.worker.songProgress.connect(self.update_overall)
        self.worker.fileProgress.connect(lambda p: self.file_pb.setValue(p))
        self.worker.errorOccurred.connect(lambda e: QtWidgets.QMessageBox.warning(self, 'Error', e))
        self.worker.finishedAll.connect(self.download_finished)
        self.download_btn.setEnabled(False)
        self.worker.start()

    def update_overall(self, current, total):
        self.overall_pb.setMaximum(total)
        self.overall_pb.setValue(current)

    def download_finished(self):
        QtWidgets.QMessageBox.information(self, "Done", "All downloads completed")
        self.queue.clear(); self.queue_list.clear()
        self.download_btn.setEnabled(True)
        self.overall_pb.reset(); self.file_pb.reset()

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
