"""
Liyana NEXUS v1 - Cyberpunk Theme
Cyberpunk-2030-Design mit Neon-Akzenten
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFrame

class CyberpunkTheme:
    """Cyberpunk-Theme für Liyana NEXUS v1"""
    
    # Farben
    PRIMARY_COLOR = "#00ff41"      # Neon-Grün
    SECONDARY_COLOR = "#ff0080"    # Neon-Pink
    ACCENT_COLOR = "#0080ff"       # Neon-Blau
    BACKGROUND_COLOR = "#0a0a0a"   # Dunkel
    DARK_BACKGROUND = "#050505"    # Sehr dunkel
    LIGHT_BACKGROUND = "#1a1a1a"   # Hell-dunkel
    TEXT_COLOR = "#ffffff"         # Weiß
    MUTED_TEXT = "#888888"         # Grau
    ERROR_COLOR = "#ff0040"        # Rot
    WARNING_COLOR = "#ff8000"      # Orange
    SUCCESS_COLOR = "#00ff80"      # Hellgrün
    
    # Schriftarten
    FONT_FAMILY = "Consolas"
    FONT_SIZE_SMALL = 10
    FONT_SIZE_NORMAL = 12
    FONT_SIZE_LARGE = 14
    FONT_SIZE_TITLE = 18
    FONT_SIZE_HEADER = 24
    
    @staticmethod
    def apply_theme(app: QApplication):
        """Wendet das Cyberpunk-Theme auf die Anwendung an"""
        # Lade Schriftart
        CyberpunkTheme._load_fonts()
        
        # Erstelle Palette
        palette = CyberpunkTheme._create_palette()
        app.setPalette(palette)
        
        # Setze Stylesheet
        stylesheet = CyberpunkTheme._create_stylesheet()
        app.setStyleSheet(stylesheet)
        
        # Setze Fenster-Icon (falls vorhanden)
        # app.setWindowIcon(QIcon("path/to/icon.png"))
    
    @staticmethod
    def _load_fonts():
        """Lädt Cyberpunk-Schriftarten"""
        # Versuche Consolas zu laden
        font_db = QFontDatabase()
        font_db.addApplicationFont(":/fonts/consolas.ttf")
        
        # Fallback-Schriftarten
        fallback_fonts = ["Consolas", "Courier New", "Monaco", "Menlo", "DejaVu Sans Mono"]
        
        for font_name in fallback_fonts:
            if font_name in QFontDatabase().families():
                CyberpunkTheme.FONT_FAMILY = font_name
                break
    
    @staticmethod
    def _create_palette() -> QPalette:
        """Erstellt eine Cyberpunk-Palette"""
        palette = QPalette()
        
        # Definiere Farben
        primary = QColor(CyberpunkTheme.PRIMARY_COLOR)
        secondary = QColor(CyberpunkTheme.SECONDARY_COLOR)
        accent = QColor(CyberpunkTheme.ACCENT_COLOR)
        background = QColor(CyberpunkTheme.BACKGROUND_COLOR)
        dark_bg = QColor(CyberpunkTheme.DARK_BACKGROUND)
        light_bg = QColor(CyberpunkTheme.LIGHT_BACKGROUND)
        text = QColor(CyberpunkTheme.TEXT_COLOR)
        muted_text = QColor(CyberpunkTheme.MUTED_TEXT)
        error = QColor(CyberpunkTheme.ERROR_COLOR)
        warning = QColor(CyberpunkTheme.WARNING_COLOR)
        success = QColor(CyberpunkTheme.SUCCESS_COLOR)
        
        # Setze Palette-Farben
        palette.setColor(QPalette.Window, background)
        palette.setColor(QPalette.WindowText, text)
        palette.setColor(QPalette.Base, dark_bg)
        palette.setColor(QPalette.AlternateBase, light_bg)
        palette.setColor(QPalette.ToolTipBase, dark_bg)
        palette.setColor(QPalette.ToolTipText, text)
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.PlaceholderText, muted_text)
        palette.setColor(QPalette.Button, dark_bg)
        palette.setColor(QPalette.ButtonText, text)
        palette.setColor(QPalette.BrightText, primary)
        palette.setColor(QPalette.Highlight, accent)
        palette.setColor(QPalette.HighlightedText, text)
        palette.setColor(QPalette.Link, primary)
        palette.setColor(QPalette.LinkVisited, secondary)
        
        return palette
    
    @staticmethod
    def _create_stylesheet() -> str:
        """Erstellt das Cyberpunk-Stylesheet"""
        return f"""
        /* Hauptfenster */
        QMainWindow {{
            background-color: {CyberpunkTheme.BACKGROUND_COLOR};
            color: {CyberpunkTheme.TEXT_COLOR};
            font-family: "{CyberpunkTheme.FONT_FAMILY}";
            font-size: {CyberpunkTheme.FONT_SIZE_NORMAL}px;
        }}
        
        /* Menüleiste */
        QMenuBar {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
            border-bottom: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            padding: 5px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 12px;
            margin: 2px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
            color: {CyberpunkTheme.BACKGROUND_COLOR};
        }}
        
        /* Menüs */
        QMenu {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
            border: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            padding: 5px;
        }}
        
        QMenu::item {{
            padding: 8px 20px;
            margin: 2px;
        }}
        
        QMenu::item:selected {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
            color: {CyberpunkTheme.BACKGROUND_COLOR};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
            border: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            border-radius: 5px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: {CyberpunkTheme.FONT_SIZE_NORMAL}px;
        }}
        
        QPushButton:hover {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
            color: {CyberpunkTheme.BACKGROUND_COLOR};
            border-color: {CyberpunkTheme.PRIMARY_COLOR};
        }}
        
        QPushButton:pressed {{
            background-color: {CyberpunkTheme.ACCENT_COLOR};
            border-color: {CyberpunkTheme.ACCENT_COLOR};
        }}
        
        QPushButton:disabled {{
            background-color: {CyberpunkTheme.MUTED_TEXT};
            border-color: {CyberpunkTheme.MUTED_TEXT};
            color: {CyberpunkTheme.DARK_BACKGROUND};
        }}
        
        /* Sekundäre Buttons */
        QPushButton[class="secondary"] {{
            border-color: {CyberpunkTheme.SECONDARY_COLOR};
        }}
        
        QPushButton[class="secondary"]:hover {{
            background-color: {CyberpunkTheme.SECONDARY_COLOR};
        }}
        
        /* Akzent-Buttons */
        QPushButton[class="accent"] {{
            border-color: {CyberpunkTheme.ACCENT_COLOR};
        }}
        
        QPushButton[class="accent"]:hover {{
            background-color: {CyberpunkTheme.ACCENT_COLOR};
        }}
        
        /* Labels */
        QLabel {{
            color: {CyberpunkTheme.TEXT_COLOR};
            font-family: "{CyberpunkTheme.FONT_FAMILY}";
        }}
        
        QLabel[class="title"] {{
            font-size: {CyberpunkTheme.FONT_SIZE_TITLE}px;
            font-weight: bold;
            color: {CyberpunkTheme.PRIMARY_COLOR};
        }}
        
        QLabel[class="header"] {{
            font-size: {CyberpunkTheme.FONT_SIZE_HEADER}px;
            font-weight: bold;
            color: {CyberpunkTheme.SECONDARY_COLOR};
        }}
        
        QLabel[class="muted"] {{
            color: {CyberpunkTheme.MUTED_TEXT};
        }}
        
        QLabel[class="success"] {{
            color: {CyberpunkTheme.SUCCESS_COLOR};
        }}
        
        QLabel[class="warning"] {{
            color: {CyberpunkTheme.WARNING_COLOR};
        }}
        
        QLabel[class="error"] {{
            color: {CyberpunkTheme.ERROR_COLOR};
        }}
        
        /* Textfelder */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
            border: 2px solid {CyberpunkTheme.MUTED_TEXT};
            border-radius: 5px;
            padding: 8px;
            font-family: "{CyberpunkTheme.FONT_FAMILY}";
            font-size: {CyberpunkTheme.FONT_SIZE_NORMAL}px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {CyberpunkTheme.PRIMARY_COLOR};
        }}
        
        /* Combobox */
        QComboBox {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
            border: 2px solid {CyberpunkTheme.MUTED_TEXT};
            border-radius: 5px;
            padding: 8px;
            font-family: "{CyberpunkTheme.FONT_FAMILY}";
        }}
        
        QComboBox:focus {{
            border-color: {CyberpunkTheme.PRIMARY_COLOR};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {CyberpunkTheme.PRIMARY_COLOR};
        }}
        
        /* Listen */
        QListWidget, QTreeWidget, QTableWidget {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
            border: 2px solid {CyberpunkTheme.MUTED_TEXT};
            border-radius: 5px;
            font-family: "{CyberpunkTheme.FONT_FAMILY}";
        }}
        
        QListWidget::item, QTreeWidget::item {{
            padding: 5px;
            margin: 2px;
        }}
        
        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
            color: {CyberpunkTheme.BACKGROUND_COLOR};
        }}
        
        /* Scrollbars */
        QScrollBar:vertical {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {CyberpunkTheme.ACCENT_COLOR};
        }}
        
        QScrollBar:horizontal {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {CyberpunkTheme.ACCENT_COLOR};
        }}
        
        /* Tabs */
        QTabWidget::pane {{
            border: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
        }}
        
        QTabBar::tab {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
            border: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            border-bottom: none;
            padding: 10px 20px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
            color: {CyberpunkTheme.BACKGROUND_COLOR};
        }}
        
        QTabBar::tab:hover {{
            background-color: {CyberpunkTheme.ACCENT_COLOR};
        }}
        
        /* Group Box */
        QGroupBox {{
            font-weight: bold;
            color: {CyberpunkTheme.PRIMARY_COLOR};
            border: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            border: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            border-radius: 5px;
            text-align: center;
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
        }}
        
        QProgressBar::chunk {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
            border-radius: 3px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            color: {CyberpunkTheme.TEXT_COLOR};
            border-top: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
        }}
        
        /* Toolbar */
        QToolBar {{
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
            border: none;
            spacing: 5px;
            padding: 5px;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: 2px solid transparent;
            border-radius: 5px;
            padding: 5px;
        }}
        
        QToolButton:hover {{
            border-color: {CyberpunkTheme.PRIMARY_COLOR};
        }}
        
        QToolButton:pressed {{
            background-color: {CyberpunkTheme.PRIMARY_COLOR};
        }}
        
        /* Dialog */
        QDialog {{
            background-color: {CyberpunkTheme.BACKGROUND_COLOR};
        }}
        
        /* Frame */
        QFrame[class="cyberpunk-border"] {{
            border: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            border-radius: 5px;
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
        }}
        
        QFrame[class="glow"] {{
            border: 2px solid {CyberpunkTheme.PRIMARY_COLOR};
            border-radius: 5px;
            background-color: {CyberpunkTheme.DARK_BACKGROUND};
        }}
        """
    
    @staticmethod
    def create_glow_effect(widget: QWidget, color: str = None):
        """Erstellt einen Glow-Effekt für ein Widget"""
        if color is None:
            color = CyberpunkTheme.PRIMARY_COLOR
        
        # Erstelle Animation
        animation = QPropertyAnimation(widget, b"styleSheet")
        animation.setDuration(2000)
        animation.setLoopCount(-1)  # Endlos
        
        # Glow-Effekt
        glow_styles = [
            f"border: 2px solid {color}; border-radius: 5px;",
            f"border: 3px solid {color}; border-radius: 5px; box-shadow: 0 0 10px {color};",
            f"border: 2px solid {color}; border-radius: 5px;"
        ]
        
        for style in glow_styles:
            animation.addKeyFrame(animation.currentTime(), style)
            animation.setCurrentTime(animation.currentTime() + 1000)
        
        animation.start()
        return animation
    
    @staticmethod
    def create_pulse_animation(widget: QWidget, color: str = None):
        """Erstellt eine Pulsier-Animation"""
        if color is None:
            color = CyberpunkTheme.PRIMARY_COLOR
        
        animation = QPropertyAnimation(widget, b"styleSheet")
        animation.setDuration(1500)
        animation.setLoopCount(-1)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Pulsier-Effekt
        pulse_styles = [
            f"background-color: {CyberpunkTheme.DARK_BACKGROUND}; border: 2px solid {color};",
            f"background-color: {color}; border: 2px solid {color};",
            f"background-color: {CyberpunkTheme.DARK_BACKGROUND}; border: 2px solid {color};"
        ]
        
        for i, style in enumerate(pulse_styles):
            animation.addKeyFrame(i * 750, style)
        
        animation.start()
        return animation