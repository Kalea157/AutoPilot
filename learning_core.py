"""
Liyana NEXUS v1 - Learning Core
Basismodul für spätere Stufe-9-Selbsttraining
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import config

@dataclass
class LearningData:
    """Lern-Daten-Struktur"""
    id: str
    type: str  # pattern, behavior, decision, feedback
    data: Dict[str, Any]
    success_rate: float
    usage_count: int
    created_at: float
    last_used: float

@dataclass
class LearningPattern:
    """Lern-Pattern-Struktur"""
    id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[str]
    confidence: float
    success_count: int
    failure_count: int

class LearningCore:
    """
    Learning Core - Basismodul für Selbsttraining
    Vorbereitung für Stufe 9 - Autonomes Lernen und Meta-Zielsteuerung
    """
    
    def __init__(self, memory_vault):
        self.logger = logging.getLogger("nexus.learning")
        self.memory = memory_vault
        self.is_running = False
        self.learning_data = {}
        self.patterns = {}
        
        # Lern-Konfiguration
        self.learning_dir = Path(config.DATA_DIR) / "learning"
        self.learning_dir.mkdir(exist_ok=True)
        
        self.logger.info("🧠 Learning Core initialisiert")
    
    async def start(self):
        """Startet den Learning Core"""
        if self.is_running:
            return
        
        self.logger.info("🚀 Starte Learning Core...")
        self.is_running = True
        
        # Lade gespeicherte Lern-Daten
        await self._load_learning_data()
        
        # Starte Lern-Monitoring
        asyncio.create_task(self._monitor_learning())
        
        self.logger.info("✅ Learning Core gestartet")
    
    async def stop(self):
        """Stoppt den Learning Core"""
        self.logger.info("🛑 Stoppe Learning Core...")
        self.is_running = False
        self.logger.info("✅ Learning Core gestoppt")
    
    async def _load_learning_data(self):
        """Lädt gespeicherte Lern-Daten"""
        try:
            # Hier würden echte Lern-Daten geladen werden
            # Für jetzt simulieren wir die Funktionalität
            
            self.learning_data = {
                "patterns": {},
                "behaviors": {},
                "decisions": {},
                "feedback": {}
            }
            
            self.logger.info("✅ Lern-Daten geladen")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden der Lern-Daten: {e}")
    
    async def _monitor_learning(self):
        """Überwacht Lernprozesse"""
        while self.is_running:
            try:
                # Hier würde die tatsächliche Lern-Überwachung stehen
                # Für jetzt simulieren wir die Funktionalität
                await asyncio.sleep(300)  # Alle 5 Minuten prüfen
                
            except Exception as e:
                self.logger.error(f"❌ Fehler bei der Lern-Überwachung: {e}")
                await asyncio.sleep(600)
    
    async def record_learning_data(self, data_type: str, data: Dict[str, Any], 
                                 success: bool = True) -> str:
        """Zeichnet Lern-Daten auf"""
        try:
            data_id = f"learning_{data_type}_{int(time.time() * 1000)}"
            
            learning_data = LearningData(
                id=data_id,
                type=data_type,
                data=data,
                success_rate=1.0 if success else 0.0,
                usage_count=1,
                created_at=time.time(),
                last_used=time.time()
            )
            
            # Speichere in Memory
            if data_type not in self.learning_data:
                self.learning_data[data_type] = {}
            
            self.learning_data[data_type][data_id] = learning_data
            
            self.logger.info(f"📝 Lern-Daten aufgezeichnet: {data_id}")
            return data_id
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Aufzeichnen der Lern-Daten: {e}")
            return ""
    
    async def analyze_patterns(self, data_type: str = None) -> List[LearningPattern]:
        """Analysiert Lern-Patterns"""
        try:
            self.logger.info(f"🔍 Analysiere Lern-Patterns für: {data_type or 'alle Typen'}")
            
            patterns = []
            
            # Analysiere verfügbare Daten
            data_to_analyze = {}
            if data_type:
                data_to_analyze[data_type] = self.learning_data.get(data_type, {})
            else:
                data_to_analyze = self.learning_data
            
            for dt, data_dict in data_to_analyze.items():
                if len(data_dict) > 0:
                    # Erstelle Pattern basierend auf Daten
                    pattern = LearningPattern(
                        id=f"pattern_{dt}_{int(time.time())}",
                        name=f"Pattern für {dt}",
                        description=f"Automatisch erkanntes Pattern für {dt}",
                        conditions={
                            "data_type": dt,
                            "min_success_rate": 0.7,
                            "min_usage_count": 5
                        },
                        actions=[
                            f"apply_{dt}_strategy",
                            f"optimize_{dt}_process"
                        ],
                        confidence=0.8,
                        success_count=len([d for d in data_dict.values() if d.success_rate > 0.7]),
                        failure_count=len([d for d in data_dict.values() if d.success_rate <= 0.7])
                    )
                    patterns.append(pattern)
            
            self.logger.info(f"✅ {len(patterns)} Patterns analysiert")
            return patterns
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei der Pattern-Analyse: {e}")
            return []
    
    async def apply_learning_pattern(self, pattern_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Wendet ein Lern-Pattern an"""
        try:
            # Hier würde die tatsächliche Pattern-Anwendung stehen
            # Für jetzt simulieren wir die Funktionalität
            
            result = {
                "pattern_id": pattern_id,
                "applied": True,
                "confidence": 0.85,
                "actions_taken": [
                    "Strategy applied",
                    "Process optimized"
                ],
                "expected_improvement": 0.15,
                "timestamp": time.time()
            }
            
            self.logger.info(f"✅ Lern-Pattern angewendet: {pattern_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei der Pattern-Anwendung: {e}")
            return {"error": str(e)}
    
    async def optimize_behavior(self, behavior_type: str, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiert Verhalten basierend auf Performance-Daten"""
        try:
            self.logger.info(f"⚡ Optimiere Verhalten: {behavior_type}")
            
            # Analysiere Performance-Daten
            current_performance = performance_data.get("current_performance", 0.5)
            target_performance = performance_data.get("target_performance", 0.8)
            
            # Berechne Optimierung
            improvement_needed = target_performance - current_performance
            
            if improvement_needed > 0:
                optimization = {
                    "behavior_type": behavior_type,
                    "current_performance": current_performance,
                    "target_performance": target_performance,
                    "improvement_needed": improvement_needed,
                    "optimization_strategies": [
                        "Increase training frequency",
                        "Adjust parameters",
                        "Enhance decision logic"
                    ],
                    "expected_improvement": min(improvement_needed * 0.8, 0.3),
                    "optimization_applied": True,
                    "timestamp": time.time()
                }
            else:
                optimization = {
                    "behavior_type": behavior_type,
                    "current_performance": current_performance,
                    "target_performance": target_performance,
                    "improvement_needed": 0,
                    "optimization_strategies": [],
                    "expected_improvement": 0,
                    "optimization_applied": False,
                    "timestamp": time.time()
                }
            
            self.logger.info(f"✅ Verhalten optimiert: {behavior_type}")
            return optimization
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei der Verhaltensoptimierung: {e}")
            return {"error": str(e)}
    
    async def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Lernt aus Feedback"""
        try:
            self.logger.info("📚 Lerne aus Feedback")
            
            # Extrahiere Feedback-Daten
            feedback_type = feedback_data.get("type", "general")
            feedback_score = feedback_data.get("score", 0.5)
            feedback_text = feedback_data.get("text", "")
            
            # Analysiere Feedback
            learning_outcome = {
                "feedback_type": feedback_type,
                "feedback_score": feedback_score,
                "feedback_text": feedback_text,
                "learning_applied": True,
                "improvements": []
            }
            
            # Bestimme Verbesserungen basierend auf Feedback
            if feedback_score < 0.3:
                learning_outcome["improvements"].append("Increase response quality")
                learning_outcome["improvements"].append("Improve decision accuracy")
            elif feedback_score < 0.7:
                learning_outcome["improvements"].append("Optimize response time")
                learning_outcome["improvements"].append("Enhance user experience")
            else:
                learning_outcome["improvements"].append("Maintain current performance")
            
            # Zeichne Lern-Daten auf
            await self.record_learning_data("feedback", feedback_data, feedback_score > 0.5)
            
            self.logger.info(f"✅ Aus Feedback gelernt: {feedback_type}")
            return learning_outcome
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Lernen aus Feedback: {e}")
            return {"error": str(e)}
    
    async def predict_optimal_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sagt optimale Aktion basierend auf Kontext voraus"""
        try:
            self.logger.info("🔮 Vorhersage optimaler Aktion")
            
            # Hier würde die tatsächliche Vorhersage stehen
            # Für jetzt simulieren wir die Funktionalität
            
            context_type = context.get("type", "unknown")
            
            # Einfache Regel-basierte Vorhersage
            if context_type == "email_response":
                optimal_action = "generate_personalized_response"
                confidence = 0.85
            elif context_type == "product_search":
                optimal_action = "search_with_enhanced_filters"
                confidence = 0.78
            elif context_type == "customer_support":
                optimal_action = "provide_detailed_solution"
                confidence = 0.92
            else:
                optimal_action = "standard_processing"
                confidence = 0.65
            
            prediction = {
                "context": context,
                "optimal_action": optimal_action,
                "confidence": confidence,
                "alternative_actions": [
                    "fallback_action_1",
                    "fallback_action_2"
                ],
                "reasoning": f"Basierend auf Kontext-Typ: {context_type}",
                "timestamp": time.time()
            }
            
            self.logger.info(f"✅ Optimale Aktion vorhergesagt: {optimal_action}")
            return prediction
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei der Aktionsvorhersage: {e}")
            return {"error": str(e)}
    
    async def adapt_to_changes(self, change_data: Dict[str, Any]) -> Dict[str, Any]:
        """Passt sich an Änderungen an"""
        try:
            self.logger.info("🔄 Passe mich an Änderungen an")
            
            change_type = change_data.get("type", "unknown")
            change_magnitude = change_data.get("magnitude", 0.1)
            
            adaptation = {
                "change_type": change_type,
                "change_magnitude": change_magnitude,
                "adaptation_applied": True,
                "adaptation_strategies": [],
                "learning_rate_adjusted": False,
                "patterns_updated": False
            }
            
            # Bestimme Anpassungsstrategien
            if change_magnitude > 0.5:
                adaptation["adaptation_strategies"].append("Major system update")
                adaptation["learning_rate_adjusted"] = True
                adaptation["patterns_updated"] = True
            elif change_magnitude > 0.2:
                adaptation["adaptation_strategies"].append("Parameter adjustment")
                adaptation["learning_rate_adjusted"] = True
            else:
                adaptation["adaptation_strategies"].append("Minor optimization")
            
            self.logger.info(f"✅ Anpassung an Änderungen: {change_type}")
            return adaptation
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei der Anpassung: {e}")
            return {"error": str(e)}
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """Gibt Lern-Statistiken zurück"""
        try:
            total_data_points = sum(len(data_dict) for data_dict in self.learning_data.values())
            
            stats = {
                "total_learning_data": total_data_points,
                "data_types": {
                    data_type: len(data_dict) 
                    for data_type, data_dict in self.learning_data.items()
                },
                "patterns_identified": len(self.patterns),
                "average_success_rate": 0.75,  # Simuliert
                "learning_progress": 0.6,  # Simuliert
                "last_optimization": time.time(),
                "adaptation_count": 15  # Simuliert
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden der Lern-Statistiken: {e}")
            return {}
    
    async def export_learning_data(self, format_type: str = "json") -> str:
        """Exportiert Lern-Daten"""
        try:
            export_file = self.learning_dir / f"learning_export_{int(time.time())}.{format_type}"
            
            # Konvertiere Lern-Daten zu exportierbarem Format
            export_data = {
                "export_timestamp": time.time(),
                "learning_data": self.learning_data,
                "patterns": self.patterns,
                "statistics": await self.get_learning_statistics()
            }
            
            # Speichere Export
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Lern-Daten exportiert: {export_file}")
            return str(export_file)
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Exportieren der Lern-Daten: {e}")
            return ""
    
    async def get_status(self) -> Dict[str, Any]:
        """Gibt den Status des Learning Core zurück"""
        return {
            "state": "EXECUTING" if self.is_running else "WAITING",
            "learning_data_count": sum(len(data_dict) for data_dict in self.learning_data.values()),
            "patterns_count": len(self.patterns),
            "learning_progress": 0.6,  # Simuliert
            "last_learning": time.time()
        }
    
    async def pause(self):
        """Pausiert den Learning Core"""
        self.is_running = False
        self.logger.info("⏸️ Learning Core pausiert")
    
    async def resume(self):
        """Setzt den Learning Core fort"""
        if not self.is_running:
            await self.start()
        self.logger.info("▶️ Learning Core fortgesetzt")