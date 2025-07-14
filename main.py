#!/usr/bin/env python3
"""
Liyana NEXUS v1 - Hauptanwendung
Super-KI-Agent Stufe 8 - Produktionssystem
"""

import sys
import asyncio
import logging
import signal
from pathlib import Path
from typing import Optional

# PySide6 Imports
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PySide6.QtGui import QPixmap

# NEXUS Imports
from config import config, LOGS_DIR
from core import NexusCore
from gui import MainWindow, CyberpunkTheme

# Logging Setup
logging.basicConfig(
    level=getattr(logging, config.system.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.system.log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class NexusWorker(QThread):
    """Worker-Thread für NEXUS Core"""
    
    # Signals
    status_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    initialization_complete = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.nexus_core: Optional[NexusCore] = None
        self._running = False
    
    def run(self):
        """Hauptschleife des Workers"""
        try:
            # Erstelle Event Loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Initialisiere NEXUS Core
            self.nexus_core = NexusCore()
            
            # Starte NEXUS
            loop.run_until_complete(self._run_nexus())
            
        except Exception as e:
            logger.error(f"Fehler im NexusWorker: {e}")
            self.error_occurred.emit(str(e))
    
    async def _run_nexus(self):
        """Führt NEXUS Core aus"""
        try:
            # Initialisiere NEXUS
            success = await self.nexus_core.initialize()
            self.initialization_complete.emit(success)
            
            if not success:
                logger.error("NEXUS Initialisierung fehlgeschlagen")
                return
            
            # Starte NEXUS
            await self.nexus_core.start()
            
        except Exception as e:
            logger.error(f"Fehler beim Ausführen von NEXUS: {e}")
            self.error_occurred.emit(str(e))
    
    async def get_status(self) -> dict:
        """Gibt den aktuellen Status zurück"""
        if self.nexus_core:
            return await self.nexus_core.get_system_status()
        return {}
    
    async def stop_nexus(self):
        """Stoppt NEXUS Core"""
        if self.nexus_core:
            await self.nexus_core.stop()

class LiyanaNexusApp:
    """Hauptanwendung für Liyana NEXUS v1"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.worker: Optional[NexusWorker] = None
        self.main_window: Optional[MainWindow] = None
        self.splash_screen: Optional[QSplashScreen] = None
        
        # Setup
        self._setup_application()
        self._setup_splash_screen()
        self._setup_worker()
        self._setup_main_window()
        
        # Timer für Status-Updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # Jede Sekunde
    
    def _setup_application(self):
        """Setup der Anwendung"""
        # Anwendungsinformationen
        self.app.setApplicationName("Liyana NEXUS v1")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("Liyana Systems")
        self.app.setOrganizationDomain("liyana-systems.com")
        
        # Cyberpunk-Theme anwenden
        CyberpunkTheme.apply_theme(self.app)
        
        # Fenster-Icon (falls vorhanden)
        # icon_path = Path(__file__).parent / "assets" / "icon.png"
        # if icon_path.exists():
        #     self.app.setWindowIcon(QIcon(str(icon_path)))
        
        logger.info("Anwendung initialisiert")
    
    def _setup_splash_screen(self):
        """Setup des Splash-Screens"""
        # Erstelle Splash-Screen
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(Qt.black)
        
        # Hier könnte ein echtes Splash-Screen-Bild geladen werden
        # splash_pixmap = QPixmap("assets/splash.png")
        
        self.splash_screen = QSplashScreen(splash_pixmap)
        self.splash_screen.show()
        
        # Zeige Initialisierungsnachrichten
        self.splash_screen.showMessage(
            "Initialisiere Liyana NEXUS v1...",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        
        self.app.processEvents()
    
    def _setup_worker(self):
        """Setup des Worker-Threads"""
        self.worker = NexusWorker()
        
        # Verbinde Signals
        self.worker.initialization_complete.connect(self._on_initialization_complete)
        self.worker.error_occurred.connect(self._on_worker_error)
        
        # Starte Worker
        self.worker.start()
        
        logger.info("Worker-Thread gestartet")
    
    def _setup_main_window(self):
        """Setup des Hauptfensters"""
        self.main_window = MainWindow(self.worker)
        
        # Verbinde Signals
        self.main_window.closing.connect(self._on_main_window_closing)
        
        logger.info("Hauptfenster erstellt")
    
    def _on_initialization_complete(self, success: bool):
        """Callback für abgeschlossene Initialisierung"""
        if success:
            self.splash_screen.showMessage(
                "NEXUS Core erfolgreich initialisiert",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.green
            )
            
            # Warte kurz und zeige Hauptfenster
            QTimer.singleShot(1000, self._show_main_window)
            
            logger.info("NEXUS Core erfolgreich initialisiert")
        else:
            self.splash_screen.showMessage(
                "NEXUS Core Initialisierung fehlgeschlagen",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.red
            )
            
            # Zeige Fehlermeldung
            QTimer.singleShot(2000, self._show_error_dialog)
            
            logger.error("NEXUS Core Initialisierung fehlgeschlagen")
    
    def _on_worker_error(self, error_message: str):
        """Callback für Worker-Fehler"""
        logger.error(f"Worker-Fehler: {error_message}")
        
        # Zeige Fehlermeldung
        QMessageBox.critical(
            self.main_window,
            "NEXUS Fehler",
            f"Ein Fehler ist aufgetreten:\n{error_message}"
        )
    
    def _show_main_window(self):
        """Zeigt das Hauptfenster an"""
        if self.splash_screen:
            self.splash_screen.finish(self.main_window)
        
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        logger.info("Hauptfenster angezeigt")
    
    def _show_error_dialog(self):
        """Zeigt einen Fehler-Dialog an"""
        QMessageBox.critical(
            None,
            "Initialisierungsfehler",
            "Liyana NEXUS v1 konnte nicht initialisiert werden.\n"
            "Bitte überprüfen Sie die Konfiguration und versuchen Sie es erneut."
        )
        
        # Beende Anwendung
        self.app.quit()
    
    def _on_main_window_closing(self):
        """Callback für schließendes Hauptfenster"""
        logger.info("Hauptfenster wird geschlossen")
        
        # Stoppe Worker
        if self.worker and self.worker.isRunning():
            # Erstelle Event Loop für async Stop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self.worker.stop_nexus())
            except Exception as e:
                logger.error(f"Fehler beim Stoppen von NEXUS: {e}")
            
            loop.close()
            
            # Warte auf Worker
            self.worker.wait(5000)  # 5 Sekunden Timeout
        
        # Beende Anwendung
        self.app.quit()
    
    def _update_status(self):
        """Aktualisiert den Status"""
        if self.main_window and self.worker and self.worker.nexus_core:
            try:
                # Erstelle Event Loop für async Status-Abfrage
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                status = loop.run_until_complete(self.worker.get_status())
                self.main_window.update_status(status)
                
                loop.close()
                
            except Exception as e:
                logger.error(f"Fehler beim Status-Update: {e}")
    
    def run(self) -> int:
        """Führt die Anwendung aus"""
        try:
            logger.info("Starte Liyana NEXUS v1")
            
            # Signal-Handler für sauberes Beenden
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Führe Anwendung aus
            return self.app.exec()
            
        except Exception as e:
            logger.error(f"Fehler beim Ausführen der Anwendung: {e}")
            return 1
        finally:
            logger.info("Liyana NEXUS v1 beendet")
    
    def _signal_handler(self, signum, frame):
        """Signal-Handler für sauberes Beenden"""
        logger.info(f"Signal {signum} empfangen, beende Anwendung...")
        
        if self.main_window:
            self.main_window.close()
        else:
            self.app.quit()

def main():
    """Hauptfunktion"""
    try:
        # Erstelle und führe Anwendung aus
        app = LiyanaNexusApp()
        return app.run()
        
    except Exception as e:
        logger.error(f"Kritischer Fehler: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())