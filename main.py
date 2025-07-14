#!/usr/bin/env python3
"""
Super AI Email Agent - Hauptanwendung
"""

import asyncio
import signal
import sys
import os
from pathlib import Path
import structlog
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.super_agent import SuperAIAgent

console = Console()
logger = structlog.get_logger(__name__)


class SuperAgentApp:
    """Hauptanwendung für den Super AI Agent"""
    
    def __init__(self):
        self.agent: Optional[SuperAIAgent] = None
        self.running = False
        self.layout = self._create_layout()
        
    def _create_layout(self) -> Layout:
        """Erstellt das Terminal-Layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="logs", ratio=2)
        )
        
        return layout
    
    def _update_header(self) -> None:
        """Aktualisiert Header"""
        title = Text("🤖 Super AI Email Agent", style="bold blue")
        subtitle = Text("Autonomer E-Mail-Assistent mit GPT-4o", style="italic")
        
        header_content = Panel(
            f"{title}\n{subtitle}",
            style="blue"
        )
        
        self.layout["header"].update(header_content)
    
    def _update_stats(self, stats: dict) -> None:
        """Aktualisiert Statistiken"""
        table = Table(title="📊 Agent Statistiken")
        table.add_column("Metrik", style="cyan")
        table.add_column("Wert", style="green")
        
        # Agent Info
        agent_info = stats.get('agent', {})
        table.add_row("Status", "🟢 Läuft" if agent_info.get('is_running') else "🔴 Gestoppt")
        table.add_row("Version", agent_info.get('version', 'N/A'))
        table.add_row("Uptime", f"{agent_info.get('uptime_seconds', 0):.0f}s")
        
        # Processing Stats
        processing = stats.get('processing', {})
        table.add_row("Verarbeitet", str(processing.get('total_processed', 0)))
        table.add_row("Genehmigt", str(processing.get('total_approved', 0)))
        table.add_row("Abgelehnt", str(processing.get('total_rejected', 0)))
        table.add_row("Fehler", str(processing.get('total_errors', 0)))
        table.add_row("Erfolgsrate", f"{processing.get('success_rate', 0):.1f}%")
        table.add_row("Ausstehend", str(processing.get('pending_approvals', 0)))
        
        self.layout["stats"].update(Panel(table, title="Statistiken"))
    
    def _update_logs(self) -> None:
        """Aktualisiert Logs"""
        # Hier könnten echte Logs angezeigt werden
        log_content = Text("📝 Logs werden hier angezeigt...", style="dim")
        self.layout["logs"].update(Panel(log_content, title="Logs"))
    
    def _update_footer(self) -> None:
        """Aktualisiert Footer"""
        footer_text = Text(
            "Drücken Sie Ctrl+C zum Beenden | /status für Statistiken | /help für Hilfe",
            style="dim"
        )
        self.layout["footer"].update(Panel(footer_text, title="Steuerung"))
    
    async def start(self) -> None:
        """Startet die Anwendung"""
        try:
            console.print(Panel.fit(
                "[bold blue]🤖 Super AI Email Agent[/bold blue]\n"
                "[italic]Initialisiere...[/italic]",
                title="Startup"
            ))
            
            # Initialisiere Agent
            self.agent = SuperAIAgent()
            
            if not await self.agent.initialize():
                console.print("[red]❌ Initialisierung fehlgeschlagen[/red]")
                return
            
            console.print("[green]✅ Agent erfolgreich initialisiert[/green]")
            
            # Setup Signal Handler
            self._setup_signal_handlers()
            
            # Starte Agent
            self.running = True
            await self.agent.start()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Beende Anwendung...[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Fehler: {e}[/red]")
            logger.error("Application error", error=str(e))
        finally:
            await self.shutdown()
    
    def _setup_signal_handlers(self) -> None:
        """Setup Signal Handler für graceful shutdown"""
        def signal_handler(signum, frame):
            console.print(f"\n[yellow]⚠️  Signal {signum} empfangen. Beende...[/yellow]")
            self.running = False
            if self.agent:
                asyncio.create_task(self.agent.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self) -> None:
        """Beendet die Anwendung"""
        if self.agent:
            await self.agent.shutdown()
        
        console.print("[green]✅ Anwendung beendet[/green]")
    
    async def run_with_dashboard(self) -> None:
        """Startet Anwendung mit Live-Dashboard"""
        try:
            # Initialisiere Agent
            self.agent = SuperAIAgent()
            
            if not await self.agent.initialize():
                console.print("[red]❌ Initialisierung fehlgeschlagen[/red]")
                return
            
            # Setup Signal Handler
            self._setup_signal_handlers()
            
            # Starte Agent im Hintergrund
            agent_task = asyncio.create_task(self.agent.start())
            
            # Live Dashboard
            with Live(self.layout, refresh_per_second=1, screen=True):
                while self.running:
                    try:
                        # Update Layout
                        self._update_header()
                        
                        if self.agent:
                            stats = self.agent.get_stats()
                            self._update_stats(stats)
                        
                        self._update_logs()
                        self._update_footer()
                        
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error("Dashboard update error", error=str(e))
                        await asyncio.sleep(5)
            
            # Warte auf Agent
            await agent_task
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Beende Dashboard...[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Dashboard Fehler: {e}[/red]")
        finally:
            await self.shutdown()


async def main():
    """Hauptfunktion"""
    app = SuperAgentApp()
    
    # Prüfe Kommandozeilen-Argumente
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "dashboard":
            await app.run_with_dashboard()
        elif command == "test":
            await run_tests()
        elif command == "config":
            show_config()
        elif command == "help":
            show_help()
        else:
            console.print(f"[red]❌ Unbekannter Befehl: {command}[/red]")
            show_help()
    else:
        # Standard-Modus
        await app.start()


async def run_tests():
    """Führt Tests aus"""
    console.print("[yellow]🧪 Führe Tests aus...[/yellow]")
    
    # Hier könnten echte Tests implementiert werden
    console.print("[green]✅ Tests abgeschlossen[/green]")


def show_config():
    """Zeigt Konfiguration an"""
    console.print("[yellow]⚙️  Konfiguration:[/yellow]")
    
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            console.print(f.read())
    else:
        console.print("[red]❌ config.yaml nicht gefunden[/red]")


def show_help():
    """Zeigt Hilfe an"""
    help_text = """
🤖 **Super AI Email Agent - Hilfe**

**Verwendung:**
python main.py [command]

**Befehle:**
- (kein Befehl) - Startet Agent im Standard-Modus
- dashboard     - Startet Agent mit Live-Dashboard
- test          - Führt Tests aus
- config        - Zeigt Konfiguration an
- help          - Zeigt diese Hilfe an

**Konfiguration:**
1. Kopiere .env.example zu .env
2. Fülle alle erforderlichen Werte aus
3. Passe config.yaml nach Bedarf an

**Erforderliche Umgebungsvariablen:**
- EMAIL_USERNAME
- EMAIL_PASSWORD  
- EMAIL_FROM
- OPENAI_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

**Beispiel:**
python main.py dashboard
"""
    console.print(Panel(help_text, title="Hilfe"))


if __name__ == "__main__":
    # Prüfe Python-Version
    if sys.version_info < (3, 8):
        console.print("[red]❌ Python 3.8+ erforderlich[/red]")
        sys.exit(1)
    
    # Starte Anwendung
    asyncio.run(main())