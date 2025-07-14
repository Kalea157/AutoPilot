"""
Liyana NEXUS v1 - Main Window
Hauptfenster mit Cyberpunk-Interface
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QTabWidget, QGroupBox,
    QProgressBar, QFrame, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, pyqtSignal
from PySide6.QtGui import QFont, QPalette, QColor

from .cyberpunk_theme import CyberpunkTheme
from .agent_widgets import AgentStatusWidget, SystemStatusWidget
from .automation_dialog import AutomationDialog

class MainWindow(QMainWindow):
    """Hauptfenster für Liyana NEXUS v1"""
    
    # Signals
    closing = pyqtSignal()
    
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.logger = logging.getLogger(__name__)
        
        # Setup
        self._setup_ui()
        self._setup_connections()
        self._setup_timers()
        
        # Status
        self.current_status = {}
        
        self.logger.info("Main Window initialisiert")
    
    def _setup_ui(self):
        """Setup der Benutzeroberfläche"""
        # Fenster-Eigenschaften
        self.setWindowTitle("Liyana NEXUS v1 - Super-KI-Agent Stufe 8")
        self.setGeometry(100, 100, 1400, 900)
        
        # Zentrale Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Haupt-Layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Splitter für linke und rechte Seite
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Linke Seite - Agent-Status
        left_widget = self._create_left_panel()
        splitter.addWidget(left_widget)
        
        # Rechte Seite - Hauptbereich
        right_widget = self._create_right_panel()
        splitter.addWidget(right_widget)
        
        # Splitter-Verhältnis
        splitter.setSizes([400, 1000])
        
        # Status-Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Liyana NEXUS v1 bereit")
    
    def _create_left_panel(self) -> QWidget:
        """Erstellt die linke Panel"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # System-Status
        system_group = QGroupBox("System Status")
        system_layout = QVBoxLayout(system_group)
        
        self.system_status_widget = SystemStatusWidget()
        system_layout.addWidget(self.system_status_widget)
        
        left_layout.addWidget(system_group)
        
        # Agent-Status
        agents_group = QGroupBox("Agent Status")
        agents_layout = QVBoxLayout(agents_group)
        
        self.agent_status_widget = AgentStatusWidget()
        agents_layout.addWidget(self.agent_status_widget)
        
        left_layout.addWidget(agents_group)
        
        # Steuerung
        control_group = QGroupBox("Steuerung")
        control_layout = QVBoxLayout(control_group)
        
        # Buttons
        self.start_button = QPushButton("System Starten")
        self.start_button.setProperty("class", "accent")
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("System Stoppen")
        self.stop_button.setProperty("class", "secondary")
        control_layout.addWidget(self.stop_button)
        
        self.automation_button = QPushButton("Automatisierung")
        control_layout.addWidget(self.automation_button)
        
        self.settings_button = QPushButton("Einstellungen")
        control_layout.addWidget(self.settings_button)
        
        left_layout.addWidget(control_group)
        
        # Füllen Sie den restlichen Platz
        left_layout.addStretch()
        
        return left_widget
    
    def _create_right_panel(self) -> QWidget:
        """Erstellt die rechte Panel"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Tab-Widget
        self.tab_widget = QTabWidget()
        right_layout.addWidget(self.tab_widget)
        
        # Dashboard Tab
        dashboard_tab = self._create_dashboard_tab()
        self.tab_widget.addTab(dashboard_tab, "Dashboard")
        
        # Logs Tab
        logs_tab = self._create_logs_tab()
        self.tab_widget.addTab(logs_tab, "Logs")
        
        # Tasks Tab
        tasks_tab = self._create_tasks_tab()
        self.tab_widget.addTab(tasks_tab, "Tasks")
        
        # Konfiguration Tab
        config_tab = self._create_config_tab()
        self.tab_widget.addTab(config_tab, "Konfiguration")
        
        return right_widget
    
    def _create_dashboard_tab(self) -> QWidget:
        """Erstellt das Dashboard Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Überschrift
        title_label = QLabel("Liyana NEXUS v1 - Dashboard")
        title_label.setProperty("class", "header")
        layout.addWidget(title_label)
        
        # Status-Grid
        status_grid = QGridLayout()
        
        # System-Metriken
        self.uptime_label = QLabel("Uptime: --")
        self.uptime_label.setProperty("class", "muted")
        status_grid.addWidget(self.uptime_label, 0, 0)
        
        self.memory_label = QLabel("Speicher: --")
        self.memory_label.setProperty("class", "muted")
        status_grid.addWidget(self.memory_label, 0, 1)
        
        self.cpu_label = QLabel("CPU: --")
        self.cpu_label.setProperty("class", "muted")
        status_grid.addWidget(self.cpu_label, 0, 2)
        
        # Task-Metriken
        self.tasks_completed_label = QLabel("Tasks abgeschlossen: --")
        self.tasks_completed_label.setProperty("class", "success")
        status_grid.addWidget(self.tasks_completed_label, 1, 0)
        
        self.tasks_failed_label = QLabel("Tasks fehlgeschlagen: --")
        self.tasks_failed_label.setProperty("class", "error")
        status_grid.addWidget(self.tasks_failed_label, 1, 1)
        
        self.tasks_pending_label = QLabel("Tasks wartend: --")
        self.tasks_pending_label.setProperty("class", "warning")
        status_grid.addWidget(self.tasks_pending_label, 1, 2)
        
        layout.addLayout(status_grid)
        
        # Progress Bars
        progress_group = QGroupBox("System-Auslastung")
        progress_layout = QVBoxLayout(progress_group)
        
        # CPU Progress
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU:"))
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        cpu_layout.addWidget(self.cpu_progress)
        progress_layout.addLayout(cpu_layout)
        
        # Memory Progress
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("Speicher:"))
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        memory_layout.addWidget(self.memory_progress)
        progress_layout.addLayout(memory_layout)
        
        layout.addWidget(progress_group)
        
        # Aktuelle Aktivitäten
        activities_group = QGroupBox("Aktuelle Aktivitäten")
        activities_layout = QVBoxLayout(activities_group)
        
        self.activities_text = QTextEdit()
        self.activities_text.setMaximumHeight(200)
        self.activities_text.setReadOnly(True)
        activities_layout.addWidget(self.activities_text)
        
        layout.addWidget(activities_group)
        
        # Füllen Sie den restlichen Platz
        layout.addStretch()
        
        return tab
    
    def _create_logs_tab(self) -> QWidget:
        """Erstellt das Logs Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Überschrift
        title_label = QLabel("System Logs")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Log-Level Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Log-Level:"))
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        filter_layout.addWidget(self.log_level_combo)
        
        self.clear_logs_button = QPushButton("Logs löschen")
        self.clear_logs_button.setProperty("class", "secondary")
        filter_layout.addWidget(self.clear_logs_button)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Logs Text
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)
        
        return tab
    
    def _create_tasks_tab(self) -> QWidget:
        """Erstellt das Tasks Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Überschrift
        title_label = QLabel("Task-Verwaltung")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Task-Controls
        controls_layout = QHBoxLayout()
        
        self.refresh_tasks_button = QPushButton("Aktualisieren")
        controls_layout.addWidget(self.refresh_tasks_button)
        
        self.cancel_task_button = QPushButton("Task abbrechen")
        self.cancel_task_button.setProperty("class", "secondary")
        controls_layout.addWidget(self.cancel_task_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Tasks List
        self.tasks_text = QTextEdit()
        self.tasks_text.setReadOnly(True)
        layout.addWidget(self.tasks_text)
        
        return tab
    
    def _create_config_tab(self) -> QWidget:
        """Erstellt das Konfiguration Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Überschrift
        title_label = QLabel("System-Konfiguration")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Konfiguration Text
        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        layout.addWidget(self.config_text)
        
        # Konfiguration Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_config_button = QPushButton("Konfiguration speichern")
        self.save_config_button.setProperty("class", "accent")
        buttons_layout.addWidget(self.save_config_button)
        
        self.reload_config_button = QPushButton("Konfiguration neu laden")
        buttons_layout.addWidget(self.reload_config_button)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        return tab
    
    def _setup_connections(self):
        """Setup der Signal-Verbindungen"""
        # Buttons
        self.start_button.clicked.connect(self._on_start_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.automation_button.clicked.connect(self._on_automation_clicked)
        self.settings_button.clicked.connect(self._on_settings_clicked)
        
        # Logs
        self.clear_logs_button.clicked.connect(self._on_clear_logs_clicked)
        self.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        
        # Tasks
        self.refresh_tasks_button.clicked.connect(self._on_refresh_tasks_clicked)
        self.cancel_task_button.clicked.connect(self._on_cancel_task_clicked)
        
        # Konfiguration
        self.save_config_button.clicked.connect(self._on_save_config_clicked)
        self.reload_config_button.clicked.connect(self._on_reload_config_clicked)
    
    def _setup_timers(self):
        """Setup der Timer"""
        # Status-Update Timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_display)
        self.status_timer.start(1000)  # Jede Sekunde
    
    def _on_start_clicked(self):
        """Callback für Start-Button"""
        self.logger.info("Start-Button geklickt")
        # Hier würde das System gestartet werden
    
    def _on_stop_clicked(self):
        """Callback für Stop-Button"""
        self.logger.info("Stop-Button geklickt")
        # Hier würde das System gestoppt werden
    
    def _on_automation_clicked(self):
        """Callback für Automation-Button"""
        self.logger.info("Automation-Button geklickt")
        
        # Zeige Automation-Dialog
        dialog = AutomationDialog(self)
        if dialog.exec():
            selected_automations = dialog.get_selected_automations()
            self.logger.info(f"Automatisierungen ausgewählt: {selected_automations}")
    
    def _on_settings_clicked(self):
        """Callback für Settings-Button"""
        self.logger.info("Settings-Button geklickt")
        # Hier würde der Settings-Dialog geöffnet werden
    
    def _on_clear_logs_clicked(self):
        """Callback für Clear-Logs-Button"""
        self.logs_text.clear()
        self.logger.info("Logs gelöscht")
    
    def _on_log_level_changed(self, level: str):
        """Callback für Log-Level-Änderung"""
        self.logger.info(f"Log-Level geändert: {level}")
        # Hier würde das Log-Level geändert werden
    
    def _on_refresh_tasks_clicked(self):
        """Callback für Refresh-Tasks-Button"""
        self.logger.info("Tasks aktualisiert")
        # Hier würden die Tasks aktualisiert werden
    
    def _on_cancel_task_clicked(self):
        """Callback für Cancel-Task-Button"""
        self.logger.info("Task-Abbruch angefordert")
        # Hier würde ein Task abgebrochen werden
    
    def _on_save_config_clicked(self):
        """Callback für Save-Config-Button"""
        self.logger.info("Konfiguration gespeichert")
        # Hier würde die Konfiguration gespeichert werden
    
    def _on_reload_config_clicked(self):
        """Callback für Reload-Config-Button"""
        self.logger.info("Konfiguration neu geladen")
        # Hier würde die Konfiguration neu geladen werden
    
    def update_status(self, status: Dict[str, Any]):
        """Aktualisiert den Systemstatus"""
        self.current_status = status
        self._update_display()
    
    def _update_display(self):
        """Aktualisiert die Anzeige"""
        if not self.current_status:
            return
        
        # System-Status
        self.system_status_widget.update_status(self.current_status)
        
        # Agent-Status
        if 'agents' in self.current_status:
            self.agent_status_widget.update_agents(self.current_status['agents'])
        
        # Dashboard-Updates
        if 'uptime' in self.current_status:
            uptime_seconds = self.current_status['uptime']
            uptime_hours = uptime_seconds // 3600
            uptime_minutes = (uptime_seconds % 3600) // 60
            self.uptime_label.setText(f"Uptime: {uptime_hours}h {uptime_minutes}m")
        
        if 'memory_usage' in self.current_status:
            memory_mb = self.current_status['memory_usage']
            self.memory_label.setText(f"Speicher: {memory_mb:.1f} MB")
            self.memory_progress.setValue(int(memory_mb / 2048 * 100))  # 2GB als 100%
        
        if 'cpu_usage' in self.current_status:
            cpu_percent = self.current_status['cpu_usage']
            self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")
            self.cpu_progress.setValue(int(cpu_percent))
        
        # Task-Metriken
        if 'metrics' in self.current_status:
            metrics = self.current_status['metrics']
            
            if 'tasks_completed' in metrics:
                self.tasks_completed_label.setText(f"Tasks abgeschlossen: {metrics['tasks_completed']}")
            
            if 'tasks_failed' in metrics:
                self.tasks_failed_label.setText(f"Tasks fehlgeschlagen: {metrics['tasks_failed']}")
            
            if 'task_queue_size' in self.current_status:
                queue_size = self.current_status['task_queue_size']
                self.tasks_pending_label.setText(f"Tasks wartend: {queue_size}")
    
    def add_log_message(self, message: str, level: str = "INFO"):
        """Fügt eine Log-Nachricht hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        self.logs_text.append(log_entry)
        
        # Scroll zum Ende
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def add_activity(self, activity: str):
        """Fügt eine Aktivität hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        activity_entry = f"[{timestamp}] {activity}"
        
        self.activities_text.append(activity_entry)
        
        # Scroll zum Ende
        scrollbar = self.activities_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Event-Handler für Fenster-Schließen"""
        self.logger.info("Main Window wird geschlossen")
        self.closing.emit()
        event.accept()