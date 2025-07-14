"""
Liyana NEXUS v1 - Automation Init
GUI-Dialog für Automatisierungsauswahl beim Start
"""

import asyncio
import logging
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                   QHBoxLayout, QPushButton, QLabel, QComboBox, 
                                   QTextEdit, QProgressBar, QFrame, QGridLayout)
    from PySide6.QtCore import Qt, QTimer, pyqtSignal, QThread
    from PySide6.QtGui import QFont, QPalette, QColor, QPixmap
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

import config
from nexus_core import get_nexus_core

class AutomationWorker(QThread):
    """Worker-Thread für Automatisierungsstart"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, automation_type: str):
        super().__init__()
        self.automation_type = automation_type
    
    def run(self):
        """Führt die Automatisierung aus"""
        try:
            self.status_updated.emit("Initialisiere NEXUS Core...")
            self.progress_updated.emit(10)
            
            # Hole NEXUS Core
            nexus = get_nexus_core()
            
            self.status_updated.emit("Starte Automatisierung...")
            self.progress_updated.emit(30)
            
            # Starte Event-Loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Starte NEXUS mit Automatisierung
                loop.run_until_complete(nexus.start(self.automation_type))
                
                self.status_updated.emit("Automatisierung erfolgreich gestartet!")
                self.progress_updated.emit(100)
                self.finished.emit(True, "Automatisierung erfolgreich gestartet")
                
            finally:
                loop.close()
                
        except Exception as e:
            self.status_updated.emit(f"Fehler: {str(e)}")
            self.finished.emit(False, str(e))

class CyberpunkStyle:
    """Cyberpunk-Styling für die GUI"""
    
    @staticmethod
    def get_dark_palette():
        """Erstellt eine dunkle Cyberpunk-Palette"""
        palette = QPalette()
        
        # Farben aus der Config
        colors = config.GUI_CONFIG["colors"]
        
        # Setze Farben
        palette.setColor(QPalette.Window, QColor(colors["background"]))
        palette.setColor(QPalette.WindowText, QColor(colors["text"]))
        palette.setColor(QPalette.Base, QColor(colors["surface"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["surface"]))
        palette.setColor(QPalette.ToolTipBase, QColor(colors["surface"]))
        palette.setColor(QPalette.ToolTipText, QColor(colors["text"]))
        palette.setColor(QPalette.Text, QColor(colors["text"]))
        palette.setColor(QPalette.Button, QColor(colors["surface"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["text"]))
        palette.setColor(QPalette.BrightText, QColor(colors["primary"]))
        palette.setColor(QPalette.Link, QColor(colors["accent"]))
        palette.setColor(QPalette.Highlight, QColor(colors["primary"]))
        palette.setColor(QPalette.HighlightedText, QColor(colors["background"]))
        
        return palette
    
    @staticmethod
    def get_button_style():
        """Gibt Cyberpunk-Button-Styling zurück"""
        colors = config.GUI_CONFIG["colors"]
        return f"""
        QPushButton {{
            background-color: {colors['surface']};
            border: 2px solid {colors['primary']};
            color: {colors['primary']};
            padding: 10px 20px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {colors['primary']};
            color: {colors['background']};
        }}
        QPushButton:pressed {{
            background-color: {colors['secondary']};
            border-color: {colors['secondary']};
        }}
        """
    
    @staticmethod
    def get_label_style():
        """Gibt Cyberpunk-Label-Styling zurück"""
        colors = config.GUI_CONFIG["colors"]
        return f"""
        QLabel {{
            color: {colors['text']};
            font-size: 12px;
            font-weight: normal;
        }}
        QLabel[class="title"] {{
            color: {colors['primary']};
            font-size: 18px;
            font-weight: bold;
        }}
        QLabel[class="subtitle"] {{
            color: {colors['accent']};
            font-size: 14px;
            font-weight: bold;
        }}
        """
    
    @staticmethod
    def get_combo_style():
        """Gibt Cyberpunk-ComboBox-Styling zurück"""
        colors = config.GUI_CONFIG["colors"]
        return f"""
        QComboBox {{
            background-color: {colors['surface']};
            border: 2px solid {colors['accent']};
            color: {colors['text']};
            padding: 8px;
            border-radius: 5px;
            font-size: 12px;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors['accent']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors['surface']};
            border: 2px solid {colors['accent']};
            color: {colors['text']};
            selection-background-color: {colors['primary']};
        }}
        """

class AutomationInitGUI(QMainWindow):
    """
    Automation Init GUI - Cyberpunk-Interface für Automatisierungsauswahl
    """
    
    def __init__(self):
        super().__init__()
        
        if not PYSIDE6_AVAILABLE:
            print("❌ PySide6 nicht verfügbar. Verwende Konsolen-Interface.")
            self._run_console_interface()
            return
        
        self.logger = logging.getLogger("nexus.automation_init")
        self.worker = None
        
        self._init_ui()
        self._apply_cyberpunk_style()
        
        self.logger.info("🎨 Automation Init GUI initialisiert")
    
    def _init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("Liyana NEXUS v1 - Automation Init")
        self.setGeometry(100, 100, 800, 600)
        
        # Zentrale Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Haupt-Layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Titel
        title_label = QLabel("🧠 Liyana NEXUS v1")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Super-KI-Agent Stufe 8 - Automatisierungsauswahl")
        subtitle_label.setProperty("class", "subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Automatisierungsauswahl
        automation_frame = QFrame()
        automation_frame.setFrameStyle(QFrame.Box)
        automation_layout = QVBoxLayout(automation_frame)
        
        automation_label = QLabel("Wählen Sie die gewünschte Automatisierung:")
        automation_label.setProperty("class", "subtitle")
        automation_layout.addWidget(automation_label)
        
        # ComboBox für Automatisierungstypen
        self.automation_combo = QComboBox()
        self.automation_combo.addItem("E-Mail Support", "email_support")
        self.automation_combo.addItem("Call Center", "call_center")
        self.automation_combo.addItem("Dropshipping", "dropshipping")
        self.automation_combo.addItem("Marktforschung", "research")
        self.automation_combo.addItem("Alle Module", "all")
        automation_layout.addWidget(self.automation_combo)
        
        # Beschreibung
        self.description_label = QLabel("Automatische E-Mail-Bearbeitung und Antworten")
        self.description_label.setWordWrap(True)
        automation_layout.addWidget(self.description_label)
        
        main_layout.addWidget(automation_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🚀 Automatisierung starten")
        self.start_button.clicked.connect(self._start_automation)
        button_layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton("❌ Abbrechen")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Status-Bereich
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_layout = QVBoxLayout(status_frame)
        
        status_label = QLabel("Status:")
        status_label.setProperty("class", "subtitle")
        status_layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(status_frame)
        
        # Verbinde ComboBox-Änderungen
        self.automation_combo.currentIndexChanged.connect(self._update_description)
        
        # Initialisiere Beschreibung
        self._update_description()
    
    def _apply_cyberpunk_style(self):
        """Wendet Cyberpunk-Styling an"""
        # Palette
        self.setPalette(CyberpunkStyle.get_dark_palette())
        
        # Stylesheets
        self.setStyleSheet(f"""
        QMainWindow {{
            background-color: {config.GUI_CONFIG['colors']['background']};
        }}
        QFrame {{
            border: 2px solid {config.GUI_CONFIG['colors']['accent']};
            border-radius: 5px;
            padding: 10px;
        }}
        {CyberpunkStyle.get_button_style()}
        {CyberpunkStyle.get_label_style()}
        {CyberpunkStyle.get_combo_style()}
        QTextEdit {{
            background-color: {config.GUI_CONFIG['colors']['surface']};
            border: 2px solid {config.GUI_CONFIG['colors']['accent']};
            color: {config.GUI_CONFIG['colors']['text']};
            border-radius: 5px;
            padding: 5px;
        }}
        QProgressBar {{
            border: 2px solid {config.GUI_CONFIG['colors']['accent']};
            border-radius: 5px;
            text-align: center;
            background-color: {config.GUI_CONFIG['colors']['surface']};
        }}
        QProgressBar::chunk {{
            background-color: {config.GUI_CONFIG['colors']['primary']};
            border-radius: 3px;
        }}
        """)
    
    def _update_description(self):
        """Aktualisiert die Beschreibung basierend auf der Auswahl"""
        descriptions = {
            "email_support": "Automatische E-Mail-Bearbeitung und Antworten mit KI-Unterstützung",
            "call_center": "Sprachverarbeitung und Anrufbehandlung mit Whisper und TTS",
            "dropshipping": "Automatische Produktsuche und Bestellungen über AliExpress, Temu, Shopify",
            "research": "Trendanalysen und Konkurrenzvergleich mit kostenlosen APIs",
            "all": "Alle verfügbaren Module und Automatisierungen"
        }
        
        current_data = self.automation_combo.currentData()
        if current_data in descriptions:
            self.description_label.setText(descriptions[current_data])
    
    def _start_automation(self):
        """Startet die gewählte Automatisierung"""
        automation_type = self.automation_combo.currentData()
        
        if not automation_type:
            self._log_status("❌ Keine Automatisierung ausgewählt")
            return
        
        self._log_status(f"🚀 Starte Automatisierung: {automation_type}")
        
        # Deaktiviere UI
        self.start_button.setEnabled(False)
        self.automation_combo.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Starte Worker-Thread
        self.worker = AutomationWorker(automation_type)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self._log_status)
        self.worker.finished.connect(self._automation_finished)
        self.worker.start()
    
    def _log_status(self, message: str):
        """Loggt Status-Nachrichten"""
        self.status_text.append(f"[{self._get_timestamp()}] {message}")
        self.status_text.ensureCursorVisible()
    
    def _get_timestamp(self):
        """Gibt aktuelle Zeitstempel zurück"""
        import datetime
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def _automation_finished(self, success: bool, message: str):
        """Wird aufgerufen wenn Automatisierung abgeschlossen ist"""
        if success:
            self._log_status("✅ " + message)
            self._log_status("🎉 Liyana NEXUS v1 ist bereit!")
            
            # Schließe GUI nach kurzer Verzögerung
            QTimer.singleShot(3000, self.close)
        else:
            self._log_status("❌ " + message)
            
            # Reaktiviere UI
            self.start_button.setEnabled(True)
            self.automation_combo.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _run_console_interface(self):
        """Führt Konsolen-Interface aus falls GUI nicht verfügbar"""
        print("🧠 Liyana NEXUS v1 - Automation Init")
        print("=" * 50)
        print("Wählen Sie die gewünschte Automatisierung:")
        print("1. E-Mail Support")
        print("2. Call Center")
        print("3. Dropshipping")
        print("4. Marktforschung")
        print("5. Alle Module")
        print("0. Abbrechen")
        
        try:
            choice = input("\nIhre Wahl (0-5): ").strip()
            
            automation_map = {
                "1": "email_support",
                "2": "call_center", 
                "3": "dropshipping",
                "4": "research",
                "5": "all"
            }
            
            if choice == "0":
                print("Abgebrochen.")
                return
            
            if choice in automation_map:
                automation_type = automation_map[choice]
                print(f"🚀 Starte Automatisierung: {automation_type}")
                
                # Starte NEXUS
                nexus = get_nexus_core()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    loop.run_until_complete(nexus.start(automation_type))
                    print("✅ Automatisierung erfolgreich gestartet!")
                    print("🎉 Liyana NEXUS v1 ist bereit!")
                except Exception as e:
                    print(f"❌ Fehler: {e}")
                finally:
                    loop.close()
            else:
                print("❌ Ungültige Auswahl")
                
        except KeyboardInterrupt:
            print("\nAbgebrochen.")
        except Exception as e:
            print(f"❌ Fehler: {e}")

def main():
    """Hauptfunktion für Automation Init"""
    # Konfiguriere Logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Erstelle GUI-Anwendung
    if PYSIDE6_AVAILABLE:
        app = QApplication(sys.argv)
        app.setApplicationName("Liyana NEXUS v1")
        app.setApplicationVersion("1.0.0")
        
        # Erstelle und zeige GUI
        window = AutomationInitGUI()
        window.show()
        
        # Führe Event-Loop aus
        sys.exit(app.exec())
    else:
        # Führe Konsolen-Interface aus
        gui = AutomationInitGUI()

if __name__ == "__main__":
    main()