import sys
import os
import subprocess
import shutil
import json
import time
import psutil
import zipfile
import tarfile
import py7zr
import requests
import atexit
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from mcrcon import MCRcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QLineEdit, QLabel, QTextEdit, QTabWidget, QSpinBox, QCheckBox,
    QFileDialog, QMessageBox, QInputDialog, QProgressBar, QComboBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QScrollArea, QGroupBox, QGridLayout, QSizePolicy, 
    QFormLayout, QProgressDialog, QDialog, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QIcon, QColor, QCloseEvent
from PyQt6.QtWidgets import QMessageBox, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QFileInfo
from PyQt6.QtWidgets import QVBoxLayout, QListWidget, QLabel, QFrame, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QApplication
from PyQt6.QtGui import QLinearGradient, QPalette, QColor, QFont, QPainter
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtGui import QPalette, QColor, QLinearGradient, QBrush
from PyQt6.QtCore import Qt

def set_dark_theme(app):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #000000; border: 1px solid white; }")


class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("ISASM")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        
        layout.addWidget(title_label)
        
        self.setFixedHeight(30)
        
    def paintEvent(self, event):
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#000000"))
        gradient.setColorAt(1, QColor("#252524"))
        
        painter = QPainter(self)
        painter.fillRect(self.rect(), gradient)

class FancyLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
            font-family: 'Papyrus', Arial, sans-serif;
            padding: 10px;
            border-radius: 10px;
            border: 2px solid #000000;
        """)

class FancyListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setSpacing(8)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
class ValueEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 1:  # Only create editor for the value column
            editor = QLineEdit(parent)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == 1:
            value = index.model().data(index, Qt.ItemDataRole.EditRole)
            editor.setText(str(value))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == 1:
            model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

class EditGUSSettingDialog(QDialog):
    def __init__(self, setting_name, current_value, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Setting: {setting_name}")
        layout = QVBoxLayout(self)

        self.value_input = QLineEdit(str(current_value))
        layout.addWidget(QLabel(f"Setting: {setting_name}"))
        layout.addWidget(self.value_input)

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

    def get_value(self):
        return self.value_input.text()

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Item Stack")
        layout = QVBoxLayout(self)

        self.item_class = QComboBox()
        self.populate_common_items()
        self.item_class.setEditable(True)
        self.max_quantity = QLineEdit()
        self.ignore_multiplier = QCheckBox("Ignore Multiplier")

        form_layout = QFormLayout()
        form_layout.addRow("Item Class:", self.item_class)
        form_layout.addRow("Max Quantity:", self.max_quantity)
        form_layout.addRow(self.ignore_multiplier)
        layout.addLayout(form_layout)

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

    def populate_common_items(self):
        common_items = [
            "PrimalItemConsumable_RawPrimeMeat",
            "PrimalItemResource_Stone",
            "PrimalItemResource_Wood",
            "PrimalItemResource_Thatch",
            "PrimalItemResource_Metal",
            "PrimalItemResource_Fiber",
            # Add more common items here
        ]
        self.item_class.addItems(common_items)


class ChatMonitorThread(QThread):
    chat_signal = pyqtSignal(str)

    def __init__(self, ip, password, port):
        super().__init__()
        self.ip = ip
        self.password = password
        self.port = port
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                with MCRcon(self.ip, self.password, self.port) as mcr:
                    resp = mcr.command("getchat")
                    if resp and resp != "No chat messages.":
                        self.chat_signal.emit(resp)
            except Exception as e:
                print(f"Error fetching chat: {str(e)}")
            time.sleep(5)  # Poll every 5 seconds

    def stop(self):
        self.running = False

class ShutdownProgressDialog(QProgressDialog):
    def __init__(self, parent=None):
        super().__init__("Server Shutdown in Progress", "Cancel", 0, 15, parent)
        self.setWindowTitle("Server Shutdown")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumDuration(0)
        self.setAutoReset(False)
        self.setAutoClose(False)

    def update_progress(self, minutes_left):
        self.setValue(15 - minutes_left)
        if minutes_left > 0:
            self.setLabelText(f"Server Shutdown in Progress\n{minutes_left} minutes remaining")
        else:
            self.setLabelText("Server is shutting down...")        

class ServerThread(QThread):
    update_signal = pyqtSignal(str)
    status_signal = pyqtSignal(dict)

    def __init__(self, server_path, bat_path):
        super().__init__()
        self.server_path = server_path
        self.bat_path = bat_path
        self.process = None
        self.running = False
        self.start_time = time.time()
        self.last_io_counters = None
        self.last_net_io_counters = None

    def run(self):
        self.running = True
        # Use CREATE_NEW_CONSOLE flag to run the server in a new console window
        self.process = subprocess.Popen(
            self.bat_path,
            cwd=self.server_path,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True
        )
        
        while self.running:
            try:
                output = self.process.stdout.readline()
                if output:
                    self.update_signal.emit(output.strip())
                
                if self.process.poll() is not None:
                    self.running = False
                
                self.update_server_stats()
            except Exception as e:
                print(f"Error in ServerThread: {e}")
            time.sleep(1)

    def stop(self):
        self.running = False

    def terminate(self):
        self.running = False
        if self.process:
            try:
                parent = psutil.Process(self.process.pid)
                children = parent.children(recursive=True)
                for child in children:
                    child.terminate()
                parent.terminate()
            except psutil.NoSuchProcess:
                pass

    def update_server_stats(self):
        if not self.process:
            return

        try:
            process = psutil.Process(self.process.pid)
            
            # CPU usage (focus on the process's CPU usage)
            cpu_percent = process.cpu_percent(interval=1.0)
            
            # Memory usage
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Disk I/O
            io_counters = process.io_counters()
            if self.last_io_counters:
                disk_read = (io_counters.read_bytes - self.last_io_counters.read_bytes) / 1024 / 1024
                disk_write = (io_counters.write_bytes - self.last_io_counters.write_bytes) / 1024 / 1024
            else:
                disk_read = disk_write = 0
            self.last_io_counters = io_counters
            
            # Network I/O (this is still system-wide)
            net_io_counters = psutil.net_io_counters()
            if self.last_net_io_counters:
                net_sent = (net_io_counters.bytes_sent - self.last_net_io_counters.bytes_sent) / 1024 / 1024
                net_recv = (net_io_counters.bytes_recv - self.last_net_io_counters.bytes_recv) / 1024 / 1024
            else:
                net_sent = net_recv = 0
            self.last_net_io_counters = net_io_counters
            
            # Disk usage
            disk_usage = psutil.disk_usage(self.server_path)
            
            # Uptime
            uptime = time.time() - self.start_time
            
            self.status_signal.emit({
                "cpu": cpu_percent,
                "memory": memory_info.rss / (1024 * 1024),  # Convert to MB
                "memory_percent": memory_percent,
                "disk_read": disk_read,  # MB/s
                "disk_write": disk_write,  # MB/s
                "net_sent": net_sent,  # MB/s
                "net_recv": net_recv,  # MB/s
                "disk_usage": disk_usage.percent,
                "uptime": uptime
            })
        except psutil.NoSuchProcess:
            self.running = False

class BackupThread(QThread):
    backup_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    file_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, server_path, backup_config):
        super().__init__()
        self.server_path = server_path
        self.backup_config = backup_config
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self.perform_backup()
            # Sleep for the specified interval (in hours)
            for _ in range(int(self.backup_config['backup_interval'] * 3600)):
                if not self.running:
                    break
                time.sleep(1)
        self.finished.emit()

    def perform_backup(self):
        try:
            if self.backup_config['backup_savedark']:
                source_path = os.path.join(self.server_path, "ark_survival_ascended", "ShooterGame", "Saved", "SavedArks")
            elif self.backup_config['backup_saved']:
                source_path = os.path.join(self.server_path, "ark_survival_ascended", "ShooterGame", "Saved")
            else:
                self.backup_signal.emit("Error: No backup option selected.")
                return

            if not os.path.exists(source_path):
                self.backup_signal.emit(f"Error: Source path does not exist: {source_path}")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}"
            compression_method = self.backup_config['compression_method']
            
            if compression_method == "zip":
                backup_filename += ".zip"
                self.create_zip_backup(source_path, os.path.join(self.backup_config['backup_directory'], backup_filename))
            elif compression_method == "tar.gz":
                backup_filename += ".tar.gz"
                self.create_tar_backup(source_path, os.path.join(self.backup_config['backup_directory'], backup_filename))
            elif compression_method == "7z":
                backup_filename += ".7z"
                self.create_7z_backup(source_path, os.path.join(self.backup_config['backup_directory'], backup_filename))

            self.backup_signal.emit(f"Backup created: {backup_filename}")
            self.remove_old_backups()

        except Exception as e:
            self.backup_signal.emit(f"Backup failed: {str(e)}")

    def count_files(self, path):
        total_files = 0
        for root, _, files in os.walk(path):
            total_files += len(files)
        return total_files

    def create_zip_backup(self, source_path, backup_path):
        total_files = self.count_files(source_path)
        files_processed = 0
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_path)
                    zipf.write(file_path, arcname)
                    files_processed += 1
                    progress = min(int((files_processed / total_files) * 100), 100)
                    self.progress_signal.emit(progress)
                    self.file_signal.emit(f"Compressing: {arcname}")

    def create_tar_backup(self, source_path, backup_path):
        total_files = self.count_files(source_path)
        files_processed = 0
        with tarfile.open(backup_path, "w:gz") as tar:
            for root, _, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_path)
                    tar.add(file_path, arcname=arcname)
                    files_processed += 1
                    progress = min(int((files_processed / total_files) * 100), 100)
                    self.progress_signal.emit(progress)
                    self.file_signal.emit(f"Compressing: {arcname}")         

    def create_7z_backup(self, source_path, backup_path):
        total_files = self.count_files(source_path)
        files_processed = 0
        with py7zr.SevenZipFile(backup_path, 'w') as archive:
            for root, _, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_path)
                    archive.write(file_path, arcname)
                    files_processed += 1
                    progress = min(int((files_processed / total_files) * 100), 100)
                    self.progress_signal.emit(progress)
                    self.file_signal.emit(f"Compressing: {arcname}")

    def remove_old_backups(self):
        backup_dir = self.backup_config['backup_directory']
        backups = [f for f in os.listdir(backup_dir) if f.startswith("backup_")]
        backups.sort(reverse=True)

        while len(backups) > self.backup_config['backup_count']:
            oldest_backup = backups.pop()
            os.remove(os.path.join(backup_dir, oldest_backup))
            self.backup_signal.emit(f"Removed old backup: {oldest_backup}")

    def stop(self):
        self.running = False

class ModInstaller(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)

    def __init__(self, mod_id, server_path):
        super().__init__()
        self.mod_id = mod_id
        self.server_path = server_path

    def run(self):
        self.status_signal.emit(f"Installing mod {self.mod_id}")
        # Implement mod installation logic here
        # You'll need to use SteamCMD to download the mod
        # and then move it to the correct folder
        self.status_signal.emit(f"Mod {self.mod_id} installed successfully")

class ARKServerManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ISASM")
        self.setGeometry(100, 100, 1200, 800)

        # Create a linear gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#000000"))
        gradient.setColorAt(1, QColor("#252524"))

        # Create a palette and set the gradient as the window color
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)

        # Create a central widget and set its background to transparent
        central_widget = QWidget(self)
        central_widget.setAutoFillBackground(False)
        self.setCentralWidget(central_widget)
        

        self.servers = {}
        self.load_servers()

        self.settings = QSettings("YourCompany", "ARKServerManager")
        self.load_settings()

        self.init_ui()

        self.backup_threads = {}
        self.server_threads = {}

        self.load_servers()
        self.update_server_list()
        self.load_all_server_configs()
        self.setGeometry(100, 100, 1200, 800)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Server list
        server_list_layout = QVBoxLayout()
        
        # Fancy label
        fancy_label = FancyLabel("Servers")
        server_list_layout.addWidget(fancy_label)
        
        # Add some spacing
        server_list_layout.addSpacing(15)
        
        # Fancy list widget
        self.server_list = FancyListWidget()
        self.server_list.itemClicked.connect(self.load_server_config)

        # Set custom font
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        font.setWeight(QFont.Weight.Bold)
        self.server_list.setFont(font)

        # Set style sheet for font color, rounded borders, and other properties
        self.server_list.setStyleSheet("""
            QListWidget {
                color: #ffffff;  /* Blue text color */
                border: 2px solid #A0A0A0;  /* Gray border around the whole widget */
                border-radius: 15px;  /* Rounded corners for the widget */
                padding: 10px;  /* Padding inside the widget */
                outline: 0;  /* Remove the focus outline */
            }
            QListWidget::item {
                border-bottom: 1px solid #E0E0E0;  /* Light gray border between items */
                padding: 5px;  /* Padding inside each item */
            }
            QListWidget::item:selected {
                color: #FFffff;  /* Red color for selected item text */
                background-color: #252524;  /* Light gray background for selected item */
                border: 1px solid #000000;  /* Gray border around selected item */
                border-radius: 5px;  /* Slightly rounded corners for selected item */
            }
            QListWidget::item:focus {
                outline: none;  /* Remove focus outline from items */
            }
        """)

        server_list_layout.addWidget(self.server_list)
        
        # Add a subtle shadow effect to the list
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 0)
        self.server_list.setGraphicsEffect(shadow)

        # Set background color for the entire layout
        palette = self.palette()
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, 
                    x2: 1, y2: 1,
                    stop: 0 #000000, 
                    stop: 1 #252524
                );
            }
        """)
        self.setPalette(palette)

        main_layout.addLayout(server_list_layout)

        add_server_button = QPushButton("Add Server")
        add_server_button.clicked.connect(self.add_server)
        server_list_layout.addWidget(add_server_button)

        remove_server_button = QPushButton("Remove Server")
        remove_server_button.clicked.connect(self.remove_server)
        server_list_layout.addWidget(remove_server_button)

        main_layout.addLayout(server_list_layout)

        # Server configuration and management
        server_config_layout = QVBoxLayout()
        self.server_tabs = QTabWidget()
        self.server_tabs.setTabPosition(QTabWidget.TabPosition.West)

        # General Settings Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        # Program Information
        info_group = QGroupBox("Program Information")
        info_layout = QGridLayout()

        program_name = QLabel("ARK: Survival Ascended Server Manager")
        program_name.setStyleSheet("font-weight: bold; font-size: 18px;")
        info_layout.addWidget(program_name, 0, 0, 1, 2)

        version_label = QLabel("Version: 3.5.0")
        version_label.setStyleSheet("font-weight: bold;")
        version = QLabel("")  # Update this with your actual version number
        version.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(version_label, 1, 0)
        info_layout.addWidget(version, 1, 1)

        developer_label = QLabel("Developed by: ISA - Lucifer")
        developer_label.setStyleSheet("font-weight: bold;")
        developer = QLabel("")
        info_layout.addWidget(developer_label, 2, 0)
        info_layout.addWidget(developer, 2, 1)

        discord_label = QLabel("Discord: ISA - Indiana Survival Ark")
        discord_label.setStyleSheet("font-weight: bold;")
        discord_info = QLabel('<a href="https://discord.gg/hYEgmaHXpX">Join our community</a>')
        discord_info.setOpenExternalLinks(True)
        info_layout.addWidget(discord_label, 3, 0)
        info_layout.addWidget(discord_info, 3, 1)

        info_group.setLayout(info_layout)
        general_layout.addWidget(info_group)

        # Program Description and User Agreement
        description_group = QGroupBox("")
        description_layout = QVBoxLayout()

        description_text = QTextEdit()
        description_text.setReadOnly(True)
        description_text.setHtml("""
        <h4>Program Features:</h4>
        <p>This comprehensive application is designed to streamline the management of ARK: Survival Ascended servers, offering a range of powerful features through an intuitive interface:</p>

        <ul>
            <li><strong>Server Installation and Updates:</strong> Easily install and keep your ARK: Survival Ascended server up-to-date with automated processes, ensuring you're always running the latest version.</li>
            
            <li><strong>Effortless Configuration:</strong> Configure your server settings through a user-friendly interface, eliminating the need for manual .ini file editing. Adjust game rules, player limits, and server performance settings with just a few clicks.</li>
            
            <li><strong>Mod Management:</strong> Seamlessly install, update, and manage mods for your server. Our integrated mod manager allows you to browse, add, and remove mods without leaving the application.</li>
            
            <li><strong>Performance Monitoring:</strong> Keep a close eye on your server's health with real-time monitoring of CPU usage, memory consumption, network traffic, and more. Receive alerts for potential issues before they impact your players.</li>
            
            <li><strong>Player Activity Tracking:</strong> Monitor online players, view detailed player statistics, and manage player interactions directly from the dashboard.</li>
            
            <li><strong>Automated Backups:</strong> Set up scheduled backups of your server data, ensuring you never lose important progress. Easily restore from backups with our intuitive restore feature.</li>
            
            <li><strong>RCON Command Interface:</strong> Execute RCON commands directly from the application, allowing for real-time server management and player moderation without the need for external tools.</li>
            
            <li><strong>Customizable Startup Scripts:</strong> Create and manage custom startup scripts to fine-tune your server's launch parameters and performance.</li>
        </ul>

        <h4>User Agreement:</h4>
        <p>By using the ARK: Survival Ascended Server Manager, you acknowledge and agree to the following terms:</p>

        <ol>
            <li><strong>As-Is Basis:</strong> This software is provided "as is", without warranty of any kind, express or implied. This includes, but is not limited to, the warranties of merchantability, fitness for a particular purpose, and non-infringement.</li>
            
            <li><strong>Legal Compliance:</strong> You are solely responsible for ensuring that your use of this software, including the operation of any servers managed through it, complies with all applicable local, state, national, and international laws and regulations.</li>
            
            <li><strong>Proper Use:</strong> You agree not to use this software for any illegal, harmful, or unauthorized purposes. This includes, but is not limited to, violating any third-party intellectual property rights or using the software to distribute malicious content.</li>
            
            <li><strong>Limitation of Liability:</strong> The developers, contributors, and distributors of this software shall not be held liable for any damages, losses, or issues arising from the use of this software. This includes, but is not limited to, data loss, server downtime, or any financial losses incurred through the use of this application.</li>
            
            <li><strong>Modification and Updates:</strong> The developers reserve the right to modify, update, or discontinue this software at any time without prior notice. You are responsible for keeping the software updated to the latest version.</li>
            
            <li><strong>Data Collection:</strong> This software may collect anonymous usage statistics to improve its functionality. No personal or identifiable information is collected or transmitted.</li>
        </ol>

        <p>By using this software, you indicate that you have read, understood, and agreed to these terms. If you do not agree with any part of this agreement, please refrain from using the software.</p>

        <p>For support, feature requests, or to report bugs, please join our Discord community. Our team and community members are dedicated to helping you get the most out of your ARK: Survival Ascended server management experience.</p>
        """)
        description_layout.addWidget(description_text)

        description_group.setLayout(description_layout)
        general_layout.addWidget(description_group)

        # Set the layout for the general tab
        general_tab.setLayout(general_layout)

        # Set size policy to make the description group expand
        description_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        description_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.server_tabs.addTab(general_tab, "General")

        # Installation Tab
        install_tab = QWidget()
        install_layout = QVBoxLayout(install_tab)

        # Server Path Selection
        path_group = QGroupBox("Server Installation Path")
        path_layout = QFormLayout()

        self.server_path_input = QLineEdit()
        select_path_button = QPushButton("Browse")
        select_path_button.setIcon(QIcon.fromTheme("folder-open"))
        select_path_button.clicked.connect(self.select_server_path)

        path_input_layout = QHBoxLayout()
        path_input_layout.addWidget(self.server_path_input)
        path_input_layout.addWidget(select_path_button)

        path_layout.addRow("Server Path:", path_input_layout)
        path_group.setLayout(path_layout)
        install_layout.addWidget(path_group)

        # Installation Steps
        steps_group = QGroupBox("Installation Steps")
        steps_layout = QVBoxLayout()

        # Step 1: Install SteamCMD
        self.install_steamcmd_button = QPushButton("1. Install SteamCMD")
        self.install_steamcmd_button.clicked.connect(self.install_steamcmd)
        steps_layout.addWidget(self.install_steamcmd_button)

        # Step 2: Install/Update Server
        self.install_server_button = QPushButton("2. Install/Update ARK Server")
        self.install_server_button.clicked.connect(self.install_server)
        steps_layout.addWidget(self.install_server_button)

        steps_group.setLayout(steps_layout)
        install_layout.addWidget(steps_group)

        # Installation Log
        log_group = QGroupBox("Installation Log")
        log_layout = QVBoxLayout()

        self.install_log = QTextEdit()
        self.install_log.setReadOnly(True)
        log_layout.addWidget(self.install_log)

        log_group.setLayout(log_layout)
        install_layout.addWidget(log_group)

        # Add stretch to push everything to the top
        install_layout.addStretch()

        self.server_tabs.addTab(install_tab, "Installation")


        # Configuration Tab
        config_tab = QWidget()
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setWidget(config_tab)
        config_layout = QVBoxLayout(config_tab)

        # Map Selection
        self.map_selector = QComboBox()
        self.map_selector.addItems(["TheIsland_WP", "Ragnarok_WP", "TheCenter_WP", "ScorchedEarth_WP", "Aberration_WP", "Extinction", "Valguero_P", "Genesis", "CrystalIsles", "Gen2", "LostIsland", "Fjordur", "Oros"])
        config_layout.addWidget(QLabel("Map:"))
        config_layout.addWidget(self.map_selector)

        # Server Name
        self.server_name_input = QLineEdit()
        config_layout.addWidget(QLabel("Server Name:"))
        config_layout.addWidget(self.server_name_input)

        # Session Name
        self.session_name_input = QLineEdit()
        config_layout.addWidget(QLabel("Session Name:"))
        config_layout.addWidget(self.session_name_input)

        # Admin Password
        self.admin_password_input = QLineEdit()
        self.admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        config_layout.addWidget(QLabel("Admin Password:"))
        config_layout.addWidget(self.admin_password_input)

        # Server Password
        self.server_password_input = QLineEdit()
        self.server_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        config_layout.addWidget(QLabel("Server Password:"))
        config_layout.addWidget(self.server_password_input)

        # Port
        self.port_input = QLineEdit()
        config_layout.addWidget(QLabel("Port:"))
        config_layout.addWidget(self.port_input)

        # Query Port
        self.query_port_input = QLineEdit()
        config_layout.addWidget(QLabel("Query Port:"))
        config_layout.addWidget(self.query_port_input)

        #RCON Port  
        self.rcon_port_input = QLineEdit()
        config_layout.addWidget(QLabel("RCON Port:"))
        config_layout.addWidget(self.rcon_port_input)        

        # Max Players
        self.max_players_input = QLineEdit()
        config_layout.addWidget(QLabel("Max Players:"))
        config_layout.addWidget(self.max_players_input)

        # Backup Options
        self.backup_dir_input = QLineEdit()
        config_layout.addWidget(QLabel("Backup Directory:"))
        config_layout.addWidget(self.backup_dir_input)
        select_backup_dir_button = QPushButton("Select Backup Directory")
        select_backup_dir_button.clicked.connect(self.select_backup_directory)
        config_layout.addWidget(select_backup_dir_button)

        # Checkboxes
        self.checkboxes = {}
        checkbox_options = [
            "AllowCrateSpawnsOnTopOfStructures", "ForceAllowCaveFlyers", "NoBattlEye",
            "servergamelog", "severgamelogincludetribelogs", "ServerRCONOutputTribeLogs",
            "NotifyAdminCommandsInChat", "nosteamclient", "crossplay", "ForceRespawnDinos",
            "AllowAnyoneBabyImprintCuddle", "AllowFlyerCarryPvE", "AllowFlyerSpeedLeveling",
            "AllowMultipleAttachedC4", "AllowRaidDinoFeeding", "AlwaysAllowStructurePickup",
            "AutoDestroyStructures", "ClampResourceHarvestDamage", "DisableStructureDecayPvE",
            "EnableExtraStructurePreventionVolumes", "FastDecayUnsnappedCoreStructures",
            "ForceFlyerExplosives", "NoTransferFromFiltering", "PreventDownloadSurvivors",
            "PreventDownloadItems", "PreventDownloadDinos", "PreventUploadSurvivors",
            "PreventUploadItems", "PreventUploadDinos", "UseOptimizedHarvestingHealth",
            "ClusterDirOverride", "EnableDynamicConfig", "NoDinos", "NoHangDetection",
            "NoUnderMeshChecking", "NoUnderMeshKilling", "ServerAllowAnsel", "UseServerNetSpeedCheck"
        ]
        
        for option in checkbox_options:
            self.checkboxes[option] = QCheckBox(option)
            config_layout.addWidget(self.checkboxes[option])

        # Mods
        self.mods_input = QLineEdit()
        config_layout.addWidget(QLabel("Mods (comma-separated IDs):"))
        config_layout.addWidget(self.mods_input)

        # Active Event
        self.active_event_input = QLineEdit()
        config_layout.addWidget(QLabel("Active Event:"))
        config_layout.addWidget(self.active_event_input)

        # Custom Launch Options
        self.custom_launch_options = QTextEdit()
        config_layout.addWidget(QLabel("Custom Launch Options:"))
        config_layout.addWidget(self.custom_launch_options)

        # Save Configuration Button
        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_server_config)
        config_layout.addWidget(save_config_button)

        self.server_tabs.addTab(config_scroll, "Configuration")

        # GameUserSettings Tab
        gus_tab = QWidget()
        gus_layout = QVBoxLayout(gus_tab)

        # Search bar
        self.gus_search_bar = QLineEdit()
        self.gus_search_bar.setPlaceholderText("Search settings...")
        self.gus_search_bar.textChanged.connect(self.filter_gus_settings)
        gus_layout.addWidget(self.gus_search_bar)

        # GUS Table
        self.gus_table = QTableWidget()
        self.gus_table.setColumnCount(2)
        self.gus_table.setHorizontalHeaderLabels(["Setting", "Value"])
        self.gus_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.gus_table.verticalHeader().setVisible(False)
        self.gus_table.setItemDelegate(ValueEditDelegate(self.gus_table))
        self.gus_table.itemChanged.connect(self.on_gus_item_changed)
        gus_layout.addWidget(self.gus_table)

        #Remove Settings
        remove_setting_button = QPushButton("Remove Setting")
        remove_setting_button.clicked.connect(self.remove_gus_setting)
        gus_layout.addWidget(remove_setting_button)

        # Add new setting section
        add_setting_layout = QHBoxLayout()
        self.new_setting_section = QLineEdit()
        self.new_setting_section.setPlaceholderText("Section")
        self.new_setting_key = QLineEdit()
        self.new_setting_key.setPlaceholderText("Key")
        self.new_setting_value = QLineEdit()
        self.new_setting_value.setPlaceholderText("Value")
        add_setting_button = QPushButton("Add Setting")
        add_setting_button.clicked.connect(self.add_new_gus_setting)

        add_setting_layout.addWidget(self.new_setting_section)
        add_setting_layout.addWidget(self.new_setting_key)
        add_setting_layout.addWidget(self.new_setting_value)
        add_setting_layout.addWidget(add_setting_button)

        gus_layout.addLayout(add_setting_layout)        

        # Save button
        save_gus_button = QPushButton("Save GameUserSettings.ini")
        save_gus_button.clicked.connect(self.save_game_user_settings)
        gus_layout.addWidget(save_gus_button)

        self.server_tabs.addTab(gus_tab, "GUS.ini")

        # Game.ini Tab
        game_ini_tab = QWidget()
        game_ini_layout = QVBoxLayout(game_ini_tab)
        self.game_ini_editor = QTextEdit()
        game_ini_layout.addWidget(self.game_ini_editor)
        save_game_ini_button = QPushButton("Save Game.ini")
        save_game_ini_button.clicked.connect(self.save_game_ini)
        game_ini_layout.addWidget(save_game_ini_button)
        self.server_tabs.addTab(game_ini_tab, "Game.ini")       
        
        # Backup Tab
        backup_tab = QWidget()
        backup_layout = QVBoxLayout(backup_tab)

        # Backup Settings Group
        backup_settings_group = QGroupBox("Backup Settings")
        backup_settings_layout = QVBoxLayout()

        # Backup Interval and Count
        interval_count_layout = QHBoxLayout()
        self.backup_interval = QSpinBox()
        self.backup_interval.setMinimum(1)
        self.backup_interval.setMaximum(24)
        interval_count_layout.addWidget(QLabel("Backup every:"))
        interval_count_layout.addWidget(self.backup_interval)
        interval_count_layout.addWidget(QLabel("hours"))
        interval_count_layout.addStretch()
        self.backup_count = QSpinBox()
        self.backup_count.setMinimum(1)
        self.backup_count.setMaximum(100)
        interval_count_layout.addWidget(QLabel("Keep:"))
        interval_count_layout.addWidget(self.backup_count)
        interval_count_layout.addWidget(QLabel("backups"))
        backup_settings_layout.addLayout(interval_count_layout)

        # Compression Method
        compression_layout = QHBoxLayout()
        compression_layout.addWidget(QLabel("Compression Method:"))
        self.compression_method = QComboBox()
        self.compression_method.addItems(["zip", "tar.gz", "7z"])
        compression_layout.addWidget(self.compression_method)
        compression_layout.addStretch()
        backup_settings_layout.addLayout(compression_layout)

        # Backup Selection
        backup_selection_layout = QVBoxLayout()
        backup_selection_layout.addWidget(QLabel("Backup Selection:"))
        self.backup_savedark_checkbox = QCheckBox("Backup SavedArks folder")
        self.backup_saved_checkbox = QCheckBox("Backup entire Saved folder")
        self.backup_savedark_checkbox.stateChanged.connect(self.toggle_backup_selection)
        self.backup_saved_checkbox.stateChanged.connect(self.toggle_backup_selection)
        backup_selection_layout.addWidget(self.backup_savedark_checkbox)
        backup_selection_layout.addWidget(self.backup_saved_checkbox)
        backup_settings_layout.addLayout(backup_selection_layout)

        backup_settings_group.setLayout(backup_settings_layout)
        backup_layout.addWidget(backup_settings_group)

        # Backup Control Group
        backup_control_group = QGroupBox("Backup Control")
        backup_control_layout = QVBoxLayout()

        self.backup_now_button = QPushButton("Backup Now")
        self.backup_now_button.clicked.connect(self.backup_now)
        backup_control_layout.addWidget(self.backup_now_button)

        # Add a progress bar to the backup control group
        self.backup_progress_bar = QProgressBar()
        self.backup_progress_bar.setVisible(False)
        backup_control_layout.addWidget(self.backup_progress_bar)

        backup_control_group.setLayout(backup_control_layout)
        backup_layout.addWidget(backup_control_group)

        # Backup Log Group
        backup_log_group = QGroupBox("Backup Log")
        backup_log_layout = QVBoxLayout()

        self.backup_log = QTextEdit()
        self.backup_log.setReadOnly(True)
        backup_log_layout.addWidget(self.backup_log)

        # Add checkbox for showing compression details
        self.show_compression_details = QCheckBox("Show file compression details")
        self.show_compression_details.setChecked(False)
        backup_log_layout.addWidget(self.show_compression_details)

        clear_log_button = QPushButton("Clear Log")
        clear_log_button.clicked.connect(self.clear_backup_log)
        backup_log_layout.addWidget(clear_log_button)

        backup_log_group.setLayout(backup_log_layout)
        backup_layout.addWidget(backup_log_group)

        self.server_tabs.addTab(backup_tab, "Backup")
        # RCON Tab

        rcon_tab = QWidget()
        rcon_layout = QVBoxLayout(rcon_tab)

        # Top section: Test connection and Chat monitor
        top_section = QHBoxLayout()

        test_rcon_button = QPushButton("Test RCON Connection")
        test_rcon_button.clicked.connect(self.test_rcon_connection)
        top_section.addWidget(test_rcon_button)

        self.chat_monitor_checkbox = QCheckBox("Monitor Chat")
        self.chat_monitor_checkbox.stateChanged.connect(self.toggle_chat_monitor)
        top_section.addWidget(self.chat_monitor_checkbox)

        rcon_layout.addLayout(top_section)

        # RCON Command section
        command_section = QHBoxLayout()

        self.rcon_command_input = QLineEdit()
        command_section.addWidget(QLabel("RCON Command:"))
        command_section.addWidget(self.rcon_command_input)

        send_rcon_button = QPushButton("Send")
        send_rcon_button.clicked.connect(self.send_rcon_command)
        command_section.addWidget(send_rcon_button)

        rcon_layout.addLayout(command_section)

        # RCON Output
        rcon_layout.addWidget(QLabel("RCON Output:"))
        self.rcon_output = QTextEdit()
        self.rcon_output.setReadOnly(True)
        rcon_layout.addWidget(self.rcon_output)

        # Clear Output Button
        clear_output_button = QPushButton("Clear Output")
        clear_output_button.clicked.connect(self.clear_rcon_output)
        rcon_layout.addWidget(clear_output_button)

        self.server_tabs.addTab(rcon_tab, "RCON")

        # Replace Console Tab with Item Stack Adjustment Tab
        item_stack_tab = QWidget()
        item_stack_layout = QVBoxLayout(item_stack_tab)

        # Create table for item stack adjustments
        self.item_stack_table = QTableWidget()
        self.item_stack_table.setColumnCount(3)
        self.item_stack_table.setHorizontalHeaderLabels(["Item Class", "Max Quantity", "Ignore Multiplier"])
        header = self.item_stack_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        item_stack_layout.addWidget(self.item_stack_table)

        # Add and Remove buttons
        button_layout = QHBoxLayout()
        add_item_button = QPushButton("Add Item")
        add_item_button.clicked.connect(self.add_item_stack)
        remove_item_button = QPushButton("Remove Item")
        remove_item_button.clicked.connect(self.remove_item_stack)
        button_layout.addWidget(add_item_button)
        button_layout.addWidget(remove_item_button)
        item_stack_layout.addLayout(button_layout)

        # Save button
        save_stacks_button = QPushButton("Save Stack Configurations")
        save_stacks_button.clicked.connect(self.save_item_stacks)
        item_stack_layout.addWidget(save_stacks_button)

        self.server_tabs.addTab(item_stack_tab, "Item Stacks")

        # Players Tab
        players_tab = QWidget()
        players_layout = QVBoxLayout(players_tab)
        self.players_table = QTableWidget()
        self.players_table.setColumnCount(4)
        self.players_table.setHorizontalHeaderLabels(["Index", "Name", "Steam ID", "Actions"])
        self.players_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        players_layout.addWidget(self.players_table)
        refresh_players_button = QPushButton("Refresh Players")
        refresh_players_button.clicked.connect(self.refresh_players)
        players_layout.addWidget(refresh_players_button)
        self.server_tabs.addTab(players_tab, "Players")

        # Mods Tab
        mods_tab = QWidget()
        mods_layout = QVBoxLayout(mods_tab)
        self.mod_list = QListWidget()
        mods_layout.addWidget(QLabel("Installed Mods:"))
        mods_layout.addWidget(self.mod_list)
        mod_id_input = QLineEdit()
        mods_layout.addWidget(QLabel("Mod ID:"))
        mods_layout.addWidget(mod_id_input)
        install_mod_button = QPushButton("Install Mod")
        install_mod_button.clicked.connect(lambda: self.install_mod(mod_id_input.text()))
        mods_layout.addWidget(install_mod_button)
        self.mod_install_progress = QProgressBar()
        mods_layout.addWidget(self.mod_install_progress)
        self.server_tabs.addTab(mods_tab, "Mods")

        server_config_layout.addWidget(self.server_tabs)

        # Server control buttons
        control_layout = QHBoxLayout()
        start_server_button = QPushButton("Start Server")
        start_server_button.clicked.connect(self.start_server)
        control_layout.addWidget(start_server_button)
        stop_server_button = QPushButton("Stop Server")
        stop_server_button.clicked.connect(self.stop_server)
        control_layout.addWidget(stop_server_button)
        restart_server_button = QPushButton("Restart Server")
        restart_server_button.clicked.connect(self.restart_server)
        control_layout.addWidget(restart_server_button)
        server_config_layout.addLayout(control_layout)

        # Server status
        self.status_label = QLabel("Server Status: Offline")
        server_config_layout.addWidget(self.status_label)
        
        self.cpu_label = QLabel("CPU Usage: N/A")
        server_config_layout.addWidget(self.cpu_label)
        
        self.memory_label = QLabel("Memory Usage: N/A")
        server_config_layout.addWidget(self.memory_label)
        
        
        self.uptime_label = QLabel("Uptime: N/A")
        server_config_layout.addWidget(self.uptime_label)

        main_layout.addLayout(server_config_layout)

        self.update_server_list()

        # Set up a timer to periodically update the player list
        self.player_update_timer = QTimer(self)
        self.player_update_timer.timeout.connect(self.refresh_players)
        self.player_update_timer.start(60000)  # Update every minute

        # Create system tray icon
        self.tray_icon = None
        icon_path = "images/isa.ico"  # Replace with your actual icon path
        if QFileInfo(icon_path).exists():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon(icon_path))
            tray_menu = QMenu()
            show_action = tray_menu.addAction("Show")
            show_action.triggered.connect(self.show)
            quit_action = tray_menu.addAction("Quit")
            quit_action.triggered.connect(self.quit_application)
            self.tray_icon.setContextMenu(tray_menu)
        else:
            print(f"Warning: Tray icon file not found: {icon_path}") 

    def load_settings(self):
        self.steamcmd_path = self.settings.value("steamcmd_path", "")

    def save_settings(self):
        self.settings.setValue("steamcmd_path", self.steamcmd_path)

    def load_servers(self):
        if os.path.exists("servers.json"):
            with open("servers.json", "r") as f:
                self.servers = json.load(f)

    def save_servers(self):
        with open("servers.json", "w") as f:
            json.dump(self.servers, f)

    def update_server_list(self):
        self.server_list.clear()
        for server_name in self.servers:
            self.server_list.addItem(server_name)

    def load_game_user_settings(self, server_name):
        server = self.servers[server_name]
        gus_path = os.path.join(server["path"], "ark_survival_ascended", "ShooterGame", "Saved", "Config", "WindowsServer", "GameUserSettings.ini")
        self.gus_settings = {}
        if os.path.exists(gus_path):
            with open(gus_path, 'r') as f:
                current_section = ""
                for line in f:
                    line = line.strip()
                    if line.startswith("[") and line.endswith("]"):
                        current_section = line[1:-1]
                        self.gus_settings[current_section] = {}
                    elif "=" in line:
                        key, value = line.split("=", 1)
                        self.gus_settings[current_section][key.strip()] = value.strip()
        self.update_gus_table()

    def update_gus_table(self):
        self.gus_table.setRowCount(0)
        self.gus_table.setSortingEnabled(False)  # Disable sorting while updating
        for section, settings in self.gus_settings.items():
            for key, value in settings.items():
                row = self.gus_table.rowCount()
                self.gus_table.insertRow(row)
                self.gus_table.setItem(row, 0, QTableWidgetItem(f"{section} | {key}"))
                self.gus_table.setItem(row, 1, QTableWidgetItem(value))
        self.gus_table.setSortingEnabled(True)  # Re-enable sorting

    def resizeEvent(self, event):
        # Update the gradient when the window is resized
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#000000"))
        gradient.setColorAt(1, QColor("#252524"))
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)
        super().resizeEvent(event)        

    def filter_gus_settings(self):
        search_text = self.gus_search_bar.text().lower()
        for row in range(self.gus_table.rowCount()):
            item = self.gus_table.item(row, 0)
            if search_text in item.text().lower():
                self.gus_table.setRowHidden(row, False)
            else:
                self.gus_table.setRowHidden(row, True)

    def on_gus_item_changed(self, item):
        if item.column() == 1:  # Only handle changes in the value column
            row = item.row()
            setting_item = self.gus_table.item(row, 0)
            section, key = setting_item.text().split(" | ")
            new_value = item.text()
            self.gus_settings[section][key] = new_value

    def save_game_user_settings(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            gus_path = os.path.join(server["path"], "ark_survival_ascended", "ShooterGame", "Saved", "Config", "WindowsServer", "GameUserSettings.ini")
            try:
                with open(gus_path, 'w') as f:
                    for section, settings in self.gus_settings.items():
                        if settings:  # Only write sections that have settings
                            f.write(f"[{section}]\n")
                            for key, value in settings.items():
                                f.write(f"{key}={value}\n")
                            f.write("\n")
                QMessageBox.information(self, "Save Successful", f"GameUserSettings.ini has been saved to {gus_path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Failed", f"Failed to save GameUserSettings.ini: {str(e)}")

    def update_game_ini(self, server_name):
        server = self.servers[server_name]
        game_ini_path = os.path.join(server["path"], "ark_survival_ascended", "ShooterGame", "Saved", "Config", "WindowsServer", "Game.ini")
        
        # Read existing content
        with open(game_ini_path, 'r') as f:
            content = f.read()

        # Remove existing ConfigOverrideItemMaxQuantity entries
        content = re.sub(r'ConfigOverrideItemMaxQuantity=\(.*?\)\n?', '', content, flags=re.MULTILINE)

        # Add new ConfigOverrideItemMaxQuantity entries
        for stack in server["item_stacks"]:
            new_entry = f"ConfigOverrideItemMaxQuantity=(ItemClassString=\"{stack['ItemClassString']}\",Quantity=(MaxItemQuantity={stack['Quantity']['MaxItemQuantity']},bIgnoreMultiplier={'True' if stack['Quantity']['bIgnoreMultiplier'] else 'False'}))\n"
            content += new_entry

        # Write updated content back to Game.ini
        with open(game_ini_path, 'w') as f:
            f.write(content)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()            

    def paintEvent(self, event):
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#000000"))
        gradient.setColorAt(1, QColor("#252524"))
        
        painter = QPainter(self)
        painter.fillRect(self.rect(), gradient)

    def save_game_ini(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            game_ini_path = os.path.join(server["path"], "ark_survival_ascended", "ShooterGame", "Saved", "Config", "WindowsServer", "Game.ini")
            try:
                # Get the current content from the editor
                current_content = self.game_ini_editor.toPlainText()

                # Save the current content
                with open(game_ini_path, 'w') as f:
                    f.write(current_content)

                # Update the item stack configurations
                self.update_game_ini(server_name)

                QMessageBox.information(self, "Save Successful", f"Game.ini has been saved to {game_ini_path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Failed", f"Failed to save Game.ini: {str(e)}")           

    def add_server(self):
        server_name, ok = QInputDialog.getText(self, "Add Server", "Enter server name:")
        if ok and server_name:
            self.servers[server_name] = {
                "name": server_name,
                "path": "",
                "config": "",
                "backup_interval": 2,
                "backup_count": 40,
                "compression_method": "zip",
                "backup_savedark": True,
                "backup_saved": False,
                "backup_directory": "",
                "mods": []
            }
            self.save_servers()
            self.update_server_list()            

    def cleanup(self):
        for server_name, thread in self.server_threads.items():
            print(f"Detaching from server: {server_name}")
            thread.stop()  # This now just stops the monitoring thread, not the server process
            thread.wait()  # Wait for the thread to finish
        
        # Add this part to stop backup threads
        for server_name, thread in self.backup_threads.items():
            print(f"Stopping backup thread for server: {server_name}")
            thread.stop()
            thread.wait()       

    def remove_server(self):
            current_item = self.server_list.currentItem()
            if current_item:
                server_name = current_item.text()
                confirm = QMessageBox.question(self, "Remove Server", 
                                            f"Are you sure you want to remove {server_name}?",
                                            QMessageBox.StandardButton.Yes | 
                                            QMessageBox.StandardButton.No)
                if confirm == QMessageBox.StandardButton.Yes:
                    del self.servers[server_name]
                    self.save_servers()
                    self.update_server_list()
                    if server_name in self.backup_threads:
                        self.backup_threads[server_name].stop()
                        del self.backup_threads[server_name]
                    if server_name in self.server_threads:
                        self.server_threads[server_name].stop()
                        del self.server_threads[server_name]

    def load_server_config(self, item):
        server_name = item.text()
        server = self.servers.get(server_name)
        if not server:
            # This is a new server, initialize with default values
            server = {
                "name": server_name,
                "path": "",
                "map": "TheIsland_WP",
                "session_name": "",
                "admin_password": "",
                "server_password": "",
                "port": "",
                "query_port": "",
                "rcon_port": "",
                "max_players": "",
                "mods": [],
                "active_event": "",
                "custom_launch_options": "",
                "backup_directory": "",
                "backup_interval": 6,
                "backup_count": 5,
                "compression_method": "zip",
                "backup_savedark": True,
                "backup_saved": False,
                "item_stacks": []
            }
            self.servers[server_name] = server

        # Load server settings
        self.map_selector.setCurrentText(server.get("map", "TheIsland_WP"))
        self.server_name_input.setText(server.get("name", ""))
        self.server_path_input.setText(server.get("path", ""))
        self.session_name_input.setText(server.get("session_name", ""))
        self.admin_password_input.setText(server.get("admin_password", ""))
        self.server_password_input.setText(server.get("server_password", ""))
        self.port_input.setText(server.get("port", ""))
        self.query_port_input.setText(server.get("query_port", ""))
        self.rcon_port_input.setText(server.get("rcon_port", "")) 
        self.max_players_input.setText(server.get("max_players", ""))
        
        # Load backup settings
        self.backup_dir_input.setText(server.get("backup_directory", ""))
        self.backup_interval.setValue(server.get("backup_interval", 6))
        self.backup_count.setValue(server.get("backup_count", 5))
        self.compression_method.setCurrentText(server.get("compression_method", "zip"))
        self.backup_savedark_checkbox.setChecked(server.get("backup_savedark", True))
        self.backup_saved_checkbox.setChecked(server.get("backup_saved", False))
        
        for option, checkbox in self.checkboxes.items():
            checkbox.setChecked(server.get(option, False))
        
        self.mods_input.setText(",".join(server.get("mods", [])))
        self.active_event_input.setText(server.get("active_event", ""))
        self.custom_launch_options.setPlainText(server.get("custom_launch_options", ""))

        # Load .ini files
        self.load_game_user_settings(server_name)
        self.load_game_ini(server_name)

        # Load RCON port
        rcon_port = self.parse_game_user_settings(server_name)
        if rcon_port:
            server["rcon_port"] = rcon_port

        # Update mods in both Configuration and Mods tabs
        mods = server.get("mods", [])
        self.mods_input.setText(",".join(mods))
        self.update_mod_list(mods)            

        # Load .ini files
        self.load_game_user_settings(server_name)
        self.load_game_ini(server_name)        

        # Load item stacks
        self.load_item_stacks(server_name)

    def load_item_stacks(self, server_name):
        server = self.servers[server_name]
        item_stacks = server.get("item_stacks", [])
        self.item_stack_table.setRowCount(len(item_stacks))
        for row, stack in enumerate(item_stacks):
            self.item_stack_table.setItem(row, 0, QTableWidgetItem(stack['ItemClassString']))
            self.item_stack_table.setItem(row, 1, QTableWidgetItem(str(stack['Quantity']['MaxItemQuantity'])))
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Checked if stack['Quantity']['bIgnoreMultiplier'] else Qt.CheckState.Unchecked)
            self.item_stack_table.setItem(row, 2, checkbox)


    def load_game_ini(self, server_name):
        server = self.servers.get(server_name)
        if not server:
            return  # Exit if the server doesn't exist

        game_ini_path = os.path.join(server.get("path", ""), "ark_survival_ascended", "ShooterGame", "Saved", "Config", "WindowsServer", "Game.ini")
        if os.path.exists(game_ini_path):
            with open(game_ini_path, 'r') as f:
                self.game_ini_editor.setPlainText(f.read())
        else:
            self.game_ini_editor.setPlainText("# Game.ini content will be displayed here once the server is set up")            

    def add_item_stack(self):
        dialog = AddItemDialog(self)
        if dialog.exec():
            item_class = dialog.item_class.currentText()
            max_quantity = dialog.max_quantity.text()
            ignore_multiplier = dialog.ignore_multiplier.isChecked()

            row_count = self.item_stack_table.rowCount()
            self.item_stack_table.insertRow(row_count)
            self.item_stack_table.setItem(row_count, 0, QTableWidgetItem(item_class))
            self.item_stack_table.setItem(row_count, 1, QTableWidgetItem(max_quantity))
            
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Checked if ignore_multiplier else Qt.CheckState.Unchecked)
            self.item_stack_table.setItem(row_count, 2, checkbox)

    def remove_item_stack(self):
        current_row = self.item_stack_table.currentRow()
        if current_row >= 0:
            self.item_stack_table.removeRow(current_row)

    def add_new_gus_setting(self):
        section = self.new_setting_section.text()
        key = self.new_setting_key.text()
        value = self.new_setting_value.text()
        
        if not section or not key or not value:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields (Section, Key, and Value).")
            return
        
        if section not in self.gus_settings:
            self.gus_settings[section] = {}
        
        self.gus_settings[section][key] = value
        
        # Add the new setting to the table
        row = self.gus_table.rowCount()
        self.gus_table.insertRow(row)
        self.gus_table.setItem(row, 0, QTableWidgetItem(f"{section} | {key}"))
        self.gus_table.setItem(row, 1, QTableWidgetItem(value))
        
        # Clear the input fields
        self.new_setting_section.clear()
        self.new_setting_key.clear()
        self.new_setting_value.clear()
        
        # Optionally, you can call save_game_user_settings here to immediately save the changes
        # self.save_game_user_settings()            

    def save_item_stacks(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            item_stacks = []
            for row in range(self.item_stack_table.rowCount()):
                item_class = self.item_stack_table.item(row, 0).text()
                max_quantity = int(self.item_stack_table.item(row, 1).text())
                ignore_multiplier = self.item_stack_table.item(row, 2).checkState() == Qt.CheckState.Checked
                item_stacks.append({
                    "ItemClassString": item_class,
                    "Quantity": {
                        "MaxItemQuantity": max_quantity,
                        "bIgnoreMultiplier": ignore_multiplier
                    }
                })
            server["item_stacks"] = item_stacks
            self.save_servers()
            self.update_game_ini(server_name)
            QMessageBox.information(self, "Save Successful", "Item stack configurations have been saved and Game.ini has been updated.")

    def update_game_user_settings(self, server_name, config):
        server = self.servers[server_name]
        gus_path = os.path.join(server["path"], "ark_survival_ascended", "ShooterGame", "Saved", "Config", "WindowsServer", "GameUserSettings.ini")
        
        # Load existing settings
        if not hasattr(self, 'gus_settings') or server_name not in self.gus_settings:
            self.load_game_user_settings(server_name)
        
        # Update ServerSettings
        if 'ServerSettings' not in self.gus_settings:
            self.gus_settings['ServerSettings'] = {}
        
        self.gus_settings['ServerSettings']['SessionName'] = config['session_name']
        self.gus_settings['ServerSettings']['ServerAdminPassword'] = config['admin_password']
        self.gus_settings['ServerSettings']['RCONPort'] = config['rcon_port']  # Use the RCON port from config
        
        # Update SessionSettings
        if 'SessionSettings' not in self.gus_settings:
            self.gus_settings['SessionSettings'] = {}
        
        self.gus_settings['SessionSettings']['Port'] = config['port']
        self.gus_settings['SessionSettings']['QueryPort'] = config['query_port']
        
        # Save updated settings
        try:
            with open(gus_path, 'w') as f:
                for section, settings in self.gus_settings.items():
                    f.write(f"[{section}]\n")
                    for key, value in settings.items():
                        f.write(f"{key}={value}\n")
                    f.write("\n")
            print(f"Updated GameUserSettings.ini for {server_name}")
        except Exception as e:
            print(f"Failed to update GameUserSettings.ini for {server_name}: {str(e)}")

    def remove_gus_setting(self):
        selected_items = self.gus_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a setting to remove.")
            return

        selected_row = selected_items[0].row()
        setting_item = self.gus_table.item(selected_row, 0)
        setting_text = setting_item.text()

        reply = QMessageBox.question(self, "Remove Setting", 
                                    f"Are you sure you want to remove the setting: {setting_text}?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            section, key = setting_text.split(" | ")
            if section in self.gus_settings and key in self.gus_settings[section]:
                del self.gus_settings[section][key]
                if not self.gus_settings[section]:  # If the section is now empty, remove it
                    del self.gus_settings[section]
            self.gus_table.removeRow(selected_row)
            QMessageBox.information(self, "Setting Removed", f"The setting {setting_text} has been removed.")            


    def load_all_server_configs(self):
        if not self.servers:
            return  # Exit if there are no servers

        for server_name in self.servers:
            items = self.server_list.findItems(server_name, Qt.MatchFlag.MatchExactly)
            if items:
                self.load_server_config(items[0])

    def select_backup_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if folder:
            self.backup_dir_input.setText(folder)
            self.save_server_config()                

    def save_server_config(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            mods = [mod.strip() for mod in self.mods_input.text().split(",") if mod.strip()]
            
            config = {
                "name": self.server_name_input.text(),
                "path": self.server_path_input.text(),
                "map": self.map_selector.currentText(),
                "session_name": self.session_name_input.text(),
                "admin_password": self.admin_password_input.text(),
                "server_password": self.server_password_input.text(),
                "port": self.port_input.text(),
                "query_port": self.query_port_input.text(),
                "rcon_port": self.rcon_port_input.text(),  # Use the separate RCON port input
                "max_players": self.max_players_input.text(),
                "mods": mods,
                "active_event": self.active_event_input.text(),
                "custom_launch_options": self.custom_launch_options.toPlainText(),
                # Backup settings
                "backup_directory": self.backup_dir_input.text(),
                "backup_interval": self.backup_interval.value(),
                "backup_count": self.backup_count.value(),
                "compression_method": self.compression_method.currentText(),
                "backup_savedark": self.backup_savedark_checkbox.isChecked(),
                "backup_saved": self.backup_saved_checkbox.isChecked(),
            }
            
            for option, checkbox in self.checkboxes.items():
                config[option] = checkbox.isChecked()
            
            self.servers[server_name] = config
            print(f"Saved server config for {server_name}. Path: {self.server_path_input.text()}")
            self.save_servers()
            self.update_server_list()
            self.create_runserver_bat(server_name)
            self.update_mod_list(mods)
            
            # Update GameUserSettings.ini
            self.update_game_user_settings(server_name, config)

    def start_chat_monitor(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            
            rcon_password = server.get("admin_password")
            rcon_port = server.get("rcon_port")

            if not rcon_password or not rcon_port:
                QMessageBox.warning(self, "RCON Error", "Admin password or RCON port not set. Please check your server configuration.")
                return

            self.chat_monitor = ChatMonitorThread("127.0.0.1", rcon_password, int(rcon_port))
            self.chat_monitor.chat_signal.connect(self.update_rcon_output)
            self.chat_monitor.start()

    def stop_chat_monitor(self):
        if hasattr(self, 'chat_monitor'):
            self.chat_monitor.stop()
            self.chat_monitor.wait()

    def update_rcon_output(self, message):
        self.rcon_output.append(message)

    def toggle_chat_monitor(self, state):
        if state == Qt.Checked:
            self.start_chat_monitor()
        else:
            self.stop_chat_monitor()            
            
    def create_runserver_bat(self, server_name):
        server = self.servers[server_name]
        bat_path = os.path.join(server["path"], "ark_survival_ascended", "ShooterGame", "Binaries", "Win64", "runserver.bat")
        
        mods_string = ",".join(server.get("mods", []))
        
        # Start with the selected map, ensuring the question mark is right after it
        command = f"start ArkAscendedServer.exe {server['map']}?"
        
        # Add the rest of the parameters
        command += "listen"
        command += f"?SessionName=\"{server['session_name']}\""  # Enclose SessionName in quotes
        command += f"?ServerAdminPassword={server['admin_password']}"
        command += f"?ServerPassword={server['server_password']}"
        command += f"?Port={server['port']}"
        command += f"?QueryPort={server['query_port']}"
        command += f"?MaxPlayers={server['max_players']}"
        
        # Handle AllowCrateSpawnsOnTopOfStructures separately
        if server.get('AllowCrateSpawnsOnTopOfStructures', False):
            command += "?AllowCrateSpawnsOnTopOfStructures=True"
        else:
            command += "?AllowCrateSpawnsOnTopOfStructures=False"
        
        # Add other checkbox options
        for option, checkbox in self.checkboxes.items():
            if server.get(option, False) and option != 'AllowCrateSpawnsOnTopOfStructures':
                command += f" -{option}"
        
        # Add mods
        if mods_string:
            command += f" -mods={mods_string}"
        
        # Add active event
        if server.get("active_event"):
            command += f" -ActiveEvent={server['active_event']}"
        
        # Add standard arguments
        command += " -game -server -log"
        
        # Add custom launch options
        if server.get("custom_launch_options"):
            command += f" {server['custom_launch_options']}"
        
        os.makedirs(os.path.dirname(bat_path), exist_ok=True)
        with open(bat_path, "w") as f:
            f.write(command)
        
        print(f"Created runserver.bat for {server_name} at {bat_path}")
        print(f"Command: {command}")  # This will print the command to the console for debugging

    def select_server_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Server Directory")
        if folder:
            self.server_path_input.setText(folder)
            print(f"Server path set to: {folder}")
            self.save_server_config()  

    def install_steamcmd(self):
        if not self.steamcmd_path:
            self.steamcmd_path = QFileDialog.getExistingDirectory(self, "Select SteamCMD Directory")
            if not self.steamcmd_path:
                return
            self.save_settings()

        if not os.path.exists(os.path.join(self.steamcmd_path, "steamcmd.exe")):
            url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
            response = requests.get(url)
            zip_path = os.path.join(self.steamcmd_path, "steamcmd.zip")
            with open(zip_path, "wb") as f:
                f.write(response.content)
            shutil.unpack_archive(zip_path, self.steamcmd_path)
            os.remove(zip_path)

        QMessageBox.information(self, "SteamCMD Installed", "SteamCMD has been installed successfully.")

    def install_server(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            server_path = server["path"]

            print(f"Installing server: {server_name}")
            print(f"Server path from config: {server_path}")

            if not server_path:
                QMessageBox.warning(self, "Error", "Please set the server path first.")
                return

            source_installer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Server Installer.exe")

            if not os.path.exists(source_installer_path):
                QMessageBox.warning(self, "Error", "Server Installer.exe not found in the application directory.")
                return

            dest_installer_path = os.path.join(server_path, "Server Installer.exe")

            try:
                shutil.copy2(source_installer_path, dest_installer_path)
                print(f"Copied Server Installer to: {dest_installer_path}")

                subprocess.Popen([dest_installer_path], cwd=server_path)
                
                self.create_runserver_bat(server_name)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to copy or launch Server Installer: {str(e)}")
        else:
            print("No server selected in the list")
            QMessageBox.warning(self, "Error", "Please select a server from the list first.")

    def toggle_backup_selection(self, state):
        sender = self.sender()
        if state == Qt.CheckState.Checked:
            if sender == self.backup_savedark_checkbox:
                self.backup_saved_checkbox.setChecked(False)
            else:
                self.backup_savedark_checkbox.setChecked(False)         

    def clear_backup_log(self):
        self.backup_log.clear()                        

    def install_finished(self):
        QMessageBox.information(self, "Installation Complete", "Server installation/update completed.")
        self.install_progress.setValue(0)

    def start_server(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            server_path = server["path"]

            if not server_path:
                QMessageBox.warning(self, "Error", "Please set the server path first.")
                return

            bat_path = os.path.join(server_path, "ark_survival_ascended", "ShooterGame", "Binaries", "Win64", "runserver.bat")
            
            if not os.path.exists(bat_path):
                self.create_runserver_bat(server_name)
                if not os.path.exists(bat_path):
                    QMessageBox.warning(self, "Error", "Failed to create runserver.bat. Please check the server configuration.")
                    return

            self.server_threads[server_name] = ServerThread(os.path.dirname(bat_path), bat_path)
            self.server_threads[server_name].status_signal.connect(self.update_server_status)
            self.server_threads[server_name].start()

            self.status_label.setText("Server Status: Online")
            self.start_backup_thread(server_name)  # Make sure this line is here
            
            # Add this line to start the chat monitor
            self.start_chat_monitor()

    def server_shutdown_sequence(self, server_name):
        server = self.servers[server_name]
        rcon_password = server.get("admin_password")
        rcon_port = server.get("rcon_port")

        if not rcon_password or not rcon_port:
            QMessageBox.warning(self, "RCON Error", "Admin password or RCON port not set. Please check your server configuration.")
            return

        progress_dialog = ShutdownProgressDialog(self)
        progress_dialog.show()

        def update_and_send_message(minutes_left, message):
            progress_dialog.update_progress(minutes_left)
            try:
                with MCRcon("127.0.0.1", rcon_password, int(rcon_port)) as mcr:
                    mcr.command(f'ServerChat {message}')
                    if minutes_left == 3:
                        mcr.command('SaveWorld')
                    elif minutes_left == 2:
                        mcr.command('DestroyWildDinos')
                    elif minutes_left == 1:
                        mcr.command('SaveWorld')
                    elif minutes_left == 0:
                        mcr.command('DoExit')
            except Exception as e:
                QMessageBox.warning(self, "RCON Error", f"Failed to send message: {str(e)}")

        minutes_left = 15
        timer = QTimer(self)

        def countdown():
            nonlocal minutes_left
            if minutes_left > 0:
                if minutes_left in [15, 10, 5, 3, 2, 1]:
                    message = f"Server Restart in {minutes_left} minute{'s' if minutes_left > 1 else ''}"
                    if minutes_left == 2:
                        message += "! Please log off"
                    update_and_send_message(minutes_left, message)
                minutes_left -= 1
                timer.start(60000)  # 1 minute
            else:
                update_and_send_message(0, "Restarting Server Now")
                timer.stop()
                progress_dialog.close()
                self.stop_server_final(server_name)

        timer.timeout.connect(countdown)
        timer.start(0)  # Start immediately

    def stop_server(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            reply = QMessageBox.question(self, 'Stop Server', 
                                        'Are you sure you want to stop the server?\nThis will initiate a 15-minute shutdown sequence.',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                        QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.server_shutdown_sequence(server_name)
                
                # Add this part to stop the backup thread
                if server_name in self.backup_threads:
                    print(f"Stopping backup thread for server: {server_name}")
                    self.backup_threads[server_name].stop()
                    self.backup_threads[server_name].wait()
                    del self.backup_threads[server_name]

    def restart_server(self):
        self.stop_server()
        QTimer.singleShot(5000, self.start_server)  # Wait 5 seconds before starting

    def parse_game_user_settings(self, server_name):
        server = self.servers[server_name]
        gus_path = os.path.join(server["path"], "ark_survival_ascended", "ShooterGame", "Saved", "Config", "WindowsServer", "GameUserSettings.ini")
        rcon_port = None
        
        if os.path.exists(gus_path):
            with open(gus_path, 'r') as f:
                for line in f:
                    if line.startswith("RCONPort="):
                        rcon_port = line.split("=")[1].strip()
                        break
        
        return rcon_port     


    def toggle_chat_monitor(self, state):
        if state == Qt.CheckState.Checked:
            self.start_chat_monitor()
        else:
            self.stop_chat_monitor()

    def clear_rcon_output(self):
        self.rcon_output.clear()       

    def update_server_status(self, status):
        self.cpu_label.setText(f"CPU Usage (Most Used Core): {status['cpu']:.2f}%")
        self.memory_label.setText(f"Memory Usage: {status['memory']:.2f} MB ({status['memory_percent']:.2f}%)")
        self.disk_label.setText(f"Disk I/O: Read {status['disk_read']:.2f} MB/s, Write {status['disk_write']:.2f} MB/s")
        self.network_label.setText(f"Network I/O: Sent {status['net_sent']:.2f} MB/s, Received {status['net_recv']:.2f} MB/s")
        self.disk_usage_label.setText(f"Disk Usage: {status['disk_usage']:.2f}%")
        
        uptime = datetime.timedelta(seconds=int(status['uptime']))
        self.uptime_label.setText(f"Uptime: {uptime}")

        # Color-code labels based on usage
        self.set_label_color(self.cpu_label, status['cpu'])
        self.set_label_color(self.memory_label, status['memory_percent'])
        self.set_label_color(self.disk_usage_label, status['disk_usage'])

    def backup_now(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            
            backup_config = {
                'backup_directory': server.get('backup_directory', ''),
                'backup_interval': server.get('backup_interval', 6),
                'backup_count': server.get('backup_count', 5),
                'compression_method': server.get('compression_method', 'zip'),
                'backup_savedark': server.get('backup_savedark', True),
                'backup_saved': server.get('backup_saved', False),
            }

            if not backup_config['backup_directory']:
                QMessageBox.warning(self, "Backup Error", "Backup directory not set. Please configure it in the server settings.")
                return

            if not backup_config['backup_savedark'] and not backup_config['backup_saved']:
                QMessageBox.warning(self, "Backup Error", "Please select either SavedArks folder or entire Saved folder for backup.")
                return

            server_path = server.get('path', '')
            if not server_path:
                QMessageBox.warning(self, "Backup Error", "Server path not set. Please configure it in the general settings.")
                return

            self.backup_now_button.setEnabled(False)
            self.backup_progress_bar.setVisible(True)
            self.backup_progress_bar.setValue(0)
            self.backup_thread = BackupThread(server_path, backup_config)
            self.backup_thread.backup_signal.connect(self.update_backup_log)
            self.backup_thread.progress_signal.connect(self.update_backup_progress)
            self.backup_thread.file_signal.connect(self.update_backup_file)
            self.backup_thread.finished.connect(self.backup_finished)
            self.backup_thread.start()

    def update_backup_file(self, file_name):
        if self.show_compression_details.isChecked():
            self.update_backup_log(file_name)

    def update_backup_log(self, message):
        self.backup_log.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
        # Automatically scroll to the bottom of the log
        self.backup_log.verticalScrollBar().setValue(self.backup_log.verticalScrollBar().maximum())
    def update_backup_progress(self, progress):
        self.backup_progress_bar.setValue(progress)

    def backup_finished(self):
        self.backup_now_button.setEnabled(True)
        self.backup_progress_bar.setVisible(False)
        self.backup_thread.deleteLater()
        self.update_backup_log("Backup completed.")

    def set_label_color(self, label, value):
        if value < 50:
            label.setStyleSheet("color: green;")
        elif value < 80:
            label.setStyleSheet("color: orange;")
        else:
            label.setStyleSheet("color: red;")

    def start_backup_thread(self, server_name):
        server = self.servers[server_name]
        backup_config = {
            'backup_directory': server.get('backup_directory', ''),
            'backup_interval': server.get('backup_interval', 6),
            'backup_count': server.get('backup_count', 5),
            'compression_method': server.get('compression_method', 'zip'),
            'backup_savedark': server.get('backup_savedark', True),
            'backup_saved': server.get('backup_saved', False),
        }

        if not backup_config['backup_directory']:
            print(f"Warning: Backup directory not set for server {server_name}. Skipping automatic backups.")
            return

        if server_name in self.backup_threads:
            self.backup_threads[server_name].stop()
            self.backup_threads[server_name].wait()

        self.backup_threads[server_name] = BackupThread(server['path'], backup_config)
        self.backup_threads[server_name].backup_signal.connect(self.update_backup_log)
        self.backup_threads[server_name].finished.connect(lambda: self.backup_thread_finished(server_name))
        self.backup_threads[server_name].start()

        self.update_backup_log(f"Backup scheduler started for {server_name}. Next backup in {backup_config['backup_interval']} hours.")

    def backup_thread_finished(self, server_name):
        if server_name in self.backup_threads:
            self.backup_threads[server_name].deleteLater()
            del self.backup_threads[server_name]
        self.update_backup_log(f"Backup scheduler stopped for {server_name}.")



    def stop_backup_thread(self, server_name):
        if server_name in self.backup_threads:
            self.backup_threads[server_name].stop()

    def send_rcon_command(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            
            rcon_password = server.get("admin_password")
            rcon_port = server.get("rcon_port")

            if not rcon_password or not rcon_port:
                QMessageBox.warning(self, "RCON Error", "Admin password or RCON port not set. Please check your server configuration.")
                return

            try:
                with MCRcon("127.0.0.1", rcon_password, int(rcon_port)) as mcr:
                    resp = mcr.command(self.rcon_command_input.text())
                    self.rcon_output.append(f"> {self.rcon_command_input.text()}")
                    self.rcon_output.append(resp)
            except Exception as e:
                self.rcon_output.append(f"Error: {str(e)}")
                QMessageBox.warning(self, "RCON Error", f"Failed to connect to RCON: {str(e)}")

    def kick_player(self, player_name):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            
            rcon_password = server.get("admin_password")
            rcon_port = server.get("rcon_port")

            if not rcon_password or not rcon_port:
                QMessageBox.warning(self, "RCON Error", "Admin password or RCON port not set. Please check your server configuration.")
                return

            try:
                with MCRcon("127.0.0.1", rcon_password, int(rcon_port)) as mcr:
                    resp = mcr.command(f"kickplayer {player_name}")
                    QMessageBox.information(self, "Player Kicked", f"Player {player_name} has been kicked.")
                    self.refresh_players()
            except Exception as e:
                QMessageBox.warning(self, "RCON Error", f"Failed to kick player: {str(e)}")                

    def test_rcon_connection(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            
            rcon_password = server.get("admin_password")
            rcon_port = server.get("rcon_port")

            if not rcon_password or not rcon_port:
                QMessageBox.warning(self, "RCON Error", "Admin password or RCON port not set. Please check your server configuration.")
                return

            try:
                with MCRcon("127.0.0.1", rcon_password, int(rcon_port)) as mcr:
                    resp = mcr.command("getversion")
                    QMessageBox.information(self, "RCON Test", f"RCON connection successful. Server version: {resp}")
            except Exception as e:
                QMessageBox.warning(self, "RCON Error", f"Failed to connect to RCON: {str(e)}")                
 
    def parse_player_list(self, player_list_string):
        players = []
        lines = player_list_string.strip().split('\n')
        for line in lines:
            if line.strip():
                parts = line.split('.')
                if len(parts) == 2:
                    index = parts[0].strip()
                    player_data = parts[1].strip().split(',')
                    if len(player_data) == 2:
                        name = player_data[0].strip()
                        steam_id = player_data[1].strip()
                        players.append({"index": index, "name": name, "steam_id": steam_id})
                    else:
                        print(f"Unexpected player data format: {line}")
                else:
                    print(f"Unexpected line format: {line}")
        return players

    def update_player_table(self, players):
        self.players_table.setRowCount(len(players))
        self.players_table.setColumnCount(4)
        self.players_table.setHorizontalHeaderLabels(["Index", "Name", "Steam ID", "Actions"])
        
        for row, player in enumerate(players):
            self.players_table.setItem(row, 0, QTableWidgetItem(player["index"]))
            self.players_table.setItem(row, 1, QTableWidgetItem(player["name"]))
            self.players_table.setItem(row, 2, QTableWidgetItem(player["steam_id"]))
            
            kick_button = QPushButton("Kick")
            kick_button.clicked.connect(lambda _, p=player: self.kick_player(p["name"]))
            self.players_table.setCellWidget(row, 3, kick_button)

    def refresh_players(self):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            
            rcon_password = server.get("admin_password")
            rcon_port = server.get("rcon_port")

            if not rcon_password or not rcon_port:
                return

            try:
                with MCRcon("127.0.0.1", rcon_password, int(rcon_port)) as mcr:
                    resp = mcr.command("listplayers")
                    if resp:
                        players = self.parse_player_list(resp)
                        self.update_player_table(players)
                    else:
                        self.update_player_table([])
                        print("No players online or empty response from server.")
            except Exception as e:
                print(f"Error refreshing player list: {str(e)}")
                QMessageBox.warning(self, "RCON Error", f"Failed to connect to RCON: {str(e)}")


    def install_mod(self, mod_id):
        current_item = self.server_list.currentItem()
        if current_item:
            server_name = current_item.text()
            server = self.servers[server_name]
            server_path = server["path"]

            if not server_path:
                QMessageBox.warning(self, "Error", "Please set the server path first.")
                return

            # Add the mod ID to the server's mod list
            if "mods" not in server:
                server["mods"] = []
            if mod_id not in server["mods"]:
                server["mods"].append(mod_id)
                self.save_servers()

            # Update the mod list display
            self.update_mod_list(server["mods"])

            # Recreate the runserver.bat file with the updated mod list
            self.create_runserver_bat(server_name)

            QMessageBox.information(self, "Mod Added", f"Mod {mod_id} has been added to the server configuration.")

    def update_mod_status(self, status):
        QMessageBox.information(self, "Mod Installation", status)
        self.update_mod_list(self.servers[self.server_list.currentItem().text()]["mods"])

    def update_mod_list(self, mods):
        self.mod_list.clear()
        for mod in mods:
            self.mod_list.addItem(str(mod))

    def add_mod(self):
        mod_id, ok = QInputDialog.getText(self, "Add Mod", "Enter mod ID:")
        if ok and mod_id:
            self.mod_list.addItem(mod_id)

    def remove_mod(self):
        current_item = self.mod_list.currentItem()
        if current_item:
            self.mod_list.takeItem(self.mod_list.row(current_item))  

    def closeEvent(self, event: QCloseEvent):
        event.ignore()  # Ignore the close event
        self.show_exit_dialog()

    def show_exit_dialog(self):
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Exit Confirmation")
        message_box.setText("If this program exits, the servers will be halted. How would you like to proceed?")
        message_box.setIcon(QMessageBox.Icon.Warning)

        yes_button = message_box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        no_button = message_box.addButton("No", QMessageBox.ButtonRole.NoRole)
        
        if self.tray_icon:
            minimize_button = message_box.addButton("Minimize", QMessageBox.ButtonRole.ActionRole)

        message_box.exec()

        if message_box.clickedButton() == yes_button:
            self.cleanup()
            QApplication.quit()
        elif message_box.clickedButton() == no_button:
            pass  # Do nothing, keep the application running
        elif self.tray_icon and message_box.clickedButton() == minimize_button:
            self.hide()
            self.tray_icon.show()

    def quit_application(self):
        self.cleanup()
        QApplication.quit()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    set_dark_theme(app)
    manager = ARKServerManager()
    manager.show()
    sys.exit(app.exec())