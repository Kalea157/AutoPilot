"""
Decision Engine für den Super-KI-Agenten
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from email_fetcher import EmailData
from email_analyzer import EmailAnalysis
from response_generator import GeneratedResponse

@dataclass
class DecisionResult:
    """Ergebnis einer Entscheidung"""
    action: str  # auto_send, require_approval, reject, escalate
    confidence: float
    reason: str
    requires_human: bool
    priority: str  # high, medium, low
    estimated_response_time: int  # Minuten

class DecisionEngine:
    """Intelligente Entscheidungsmaschine für E-Mail-Verarbeitung"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_ai_config()
        self.security_config = config_manager.get_security_config()
        self.logger = logging.getLogger(__name__)
        
        # Entscheidungsregeln
        self.decision_rules = {
            'auto_send': {
                'min_confidence': self.config.confidence_thresholds['auto_approve'],
                'max_priority': 'medium',
                'allowed_categories': ['Support', 'Inquiry', 'Feedback'],
                'blocked_senders': [],
                'required_keywords': []
            },
            'require_approval': {
                'min_confidence': self.config.confidence_thresholds['require_human'],
                'max_priority': 'high',
                'allowed_categories': ['Sales', 'Complaint', 'Appointment', 'Order'],
                'suspicious_patterns': ['urgent', 'money', 'payment', 'account']
            },
            'reject': {
                'max_confidence': self.config.confidence_thresholds['auto_reject'],
                'spam_indicators': 3,
                'blocked_categories': ['Spam'],
                'suspicious_senders': []
            },
            'escalate': {
                'min_priority': 'high',
                'sensitive_keywords': ['legal', 'complaint', 'urgent', 'ceo', 'manager'],
                'high_value_customers': []
            }
        }
    
    def make_decision(self, email_data: EmailData, analysis: EmailAnalysis, 
                     response: GeneratedResponse) -> DecisionResult:
        """Trifft Entscheidung über E-Mail-Verarbeitung"""
        try:
            self.logger.info(f"Treffe Entscheidung für E-Mail: {email_data.subject}")
            
            # Sammle Entscheidungsfaktoren
            factors = self._collect_decision_factors(email_data, analysis, response)
            
            # Bewerte verschiedene Aktionen
            action_scores = self._evaluate_actions(factors)
            
            # Wähle beste Aktion
            best_action = self._select_best_action(action_scores)
            
            # Erstelle Entscheidungsergebnis
            result = self._create_decision_result(best_action, factors)
            
            self.logger.info(f"Entscheidung getroffen: {result.action} (Confidence: {result.confidence:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Fehler bei Entscheidungsfindung: {e}")
            return self._fallback_decision()
    
    def _collect_decision_factors(self, email_data: EmailData, analysis: EmailAnalysis, 
                                response: GeneratedResponse) -> Dict[str, Any]:
        """Sammelt Faktoren für Entscheidungsfindung"""
        factors = {
            'email_data': email_data,
            'analysis': analysis,
            'response': response,
            
            # Confidence-Scores
            'analysis_confidence': analysis.confidence_level,
            'response_confidence': response.confidence_level,
            'overall_confidence': (analysis.confidence_level + response.confidence_level) / 2,
            
            # Kategorien und Prioritäten
            'category': analysis.category,
            'priority': analysis.priority_score,
            'urgency': analysis.urgency,
            'sentiment': analysis.sentiment,
            
            # Sicherheitsfaktoren
            'is_spam': analysis.is_spam,
            'suspicious_patterns': self._detect_suspicious_patterns(email_data),
            'sender_reputation': self._assess_sender_reputation(email_data),
            
            # Inhaltliche Faktoren
            'has_attachments': len(email_data.attachments) > 0,
            'content_length': len(email_data.body),
            'language_match': analysis.language == response.language,
            
            # Zeitliche Faktoren
            'email_age_hours': (datetime.now() - email_data.date).total_seconds() / 3600,
            'business_hours': self._is_business_hours(),
            
            # Automatisierungsfaktoren
            'can_auto_respond': self._can_auto_respond(analysis, response),
            'requires_special_handling': self._requires_special_handling(analysis)
        }
        
        return factors
    
    def _evaluate_actions(self, factors: Dict[str, Any]) -> Dict[str, float]:
        """Bewertet verschiedene Aktionen"""
        scores = {
            'auto_send': 0.0,
            'require_approval': 0.0,
            'reject': 0.0,
            'escalate': 0.0
        }
        
        # Auto-Send Bewertung
        if factors['overall_confidence'] >= self.decision_rules['auto_send']['min_confidence']:
            scores['auto_send'] += 0.4
        
        if factors['category'] in self.decision_rules['auto_send']['allowed_categories']:
            scores['auto_send'] += 0.3
        
        if factors['priority'] <= 0.7:  # Nicht zu hoch
            scores['auto_send'] += 0.2
        
        if factors['can_auto_respond']:
            scores['auto_send'] += 0.1
        
        # Require Approval Bewertung
        if factors['overall_confidence'] < self.decision_rules['auto_send']['min_confidence']:
            scores['require_approval'] += 0.4
        
        if factors['category'] in self.decision_rules['require_approval']['allowed_categories']:
            scores['require_approval'] += 0.3
        
        if factors['priority'] > 0.7:
            scores['require_approval'] += 0.2
        
        if factors['suspicious_patterns'] > 0:
            scores['require_approval'] += 0.1
        
        # Reject Bewertung
        if factors['is_spam']:
            scores['reject'] += 0.8
        
        if factors['overall_confidence'] <= self.decision_rules['reject']['max_confidence']:
            scores['reject'] += 0.6
        
        if factors['category'] in self.decision_rules['reject']['blocked_categories']:
            scores['reject'] += 0.4
        
        # Escalate Bewertung
        if factors['priority'] >= 0.9:
            scores['escalate'] += 0.5
        
        if factors['urgency'] == 'hoch':
            scores['escalate'] += 0.3
        
        if factors['requires_special_handling']:
            scores['escalate'] += 0.2
        
        return scores
    
    def _select_best_action(self, action_scores: Dict[str, float]) -> Tuple[str, float]:
        """Wählt beste Aktion basierend auf Scores"""
        best_action = max(action_scores, key=action_scores.get)
        best_score = action_scores[best_action]
        
        # Fallback auf require_approval wenn keine klare Entscheidung
        if best_score < 0.3:
            return 'require_approval', 0.5
        
        return best_action, best_score
    
    def _create_decision_result(self, action: str, factors: Dict[str, Any]) -> DecisionResult:
        """Erstellt Entscheidungsergebnis"""
        if action == 'auto_send':
            return DecisionResult(
                action='auto_send',
                confidence=factors['overall_confidence'],
                reason=f"Hohe Confidence ({factors['overall_confidence']:.2f}) und sichere Kategorie ({factors['category']})",
                requires_human=False,
                priority=self._determine_priority(factors),
                estimated_response_time=1
            )
        
        elif action == 'require_approval':
            return DecisionResult(
                action='require_approval',
                confidence=factors['overall_confidence'],
                reason=f"Benötigt menschliche Überprüfung (Confidence: {factors['overall_confidence']:.2f})",
                requires_human=True,
                priority=self._determine_priority(factors),
                estimated_response_time=30
            )
        
        elif action == 'reject':
            return DecisionResult(
                action='reject',
                confidence=factors['overall_confidence'],
                reason="E-Mail wird abgelehnt (Spam/Verdächtig)",
                requires_human=False,
                priority='low',
                estimated_response_time=0
            )
        
        else:  # escalate
            return DecisionResult(
                action='escalate',
                confidence=factors['overall_confidence'],
                reason="Hohe Priorität - Eskalation erforderlich",
                requires_human=True,
                priority='high',
                estimated_response_time=5
            )
    
    def _detect_suspicious_patterns(self, email_data: EmailData) -> int:
        """Erkennt verdächtige Muster"""
        suspicious_count = 0
        text = f"{email_data.subject} {email_data.body}".lower()
        
        suspicious_patterns = [
            'urgent', 'limited time', 'act now', 'click here', 'free money',
            'lottery', 'inheritance', 'viagra', 'casino', 'loan',
            'credit card', 'password', 'account suspended', 'verify now',
            'bank transfer', 'western union', 'bitcoin', 'crypto'
        ]
        
        for pattern in suspicious_patterns:
            if pattern in text:
                suspicious_count += 1
        
        return suspicious_count
    
    def _assess_sender_reputation(self, email_data: EmailData) -> float:
        """Bewertet Absender-Reputation"""
        # Einfache Reputationsbewertung
        sender = email_data.sender.lower()
        
        # Bekannte gute Domains
        good_domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'company.com']
        # Bekannte schlechte Domains
        bad_domains = ['spam.com', 'suspicious.net']
        
        domain = sender.split('@')[-1] if '@' in sender else ''
        
        if domain in good_domains:
            return 0.8
        elif domain in bad_domains:
            return 0.1
        else:
            return 0.5  # Neutral
    
    def _can_auto_respond(self, analysis: EmailAnalysis, response: GeneratedResponse) -> bool:
        """Prüft ob automatische Antwort möglich ist"""
        return (
            analysis.confidence_level >= 0.8 and
            response.confidence_level >= 0.8 and
            not analysis.is_spam and
            not analysis.requires_human and
            analysis.suggested_response_type == 'auto'
        )
    
    def _requires_special_handling(self, analysis: EmailAnalysis) -> bool:
        """Prüft ob spezielle Behandlung erforderlich ist"""
        special_keywords = ['legal', 'complaint', 'urgent', 'ceo', 'manager', 'executive']
        text = f"{analysis.required_action} {' '.join(analysis.key_concerns)}".lower()
        
        return any(keyword in text for keyword in special_keywords)
    
    def _is_business_hours(self) -> bool:
        """Prüft ob Geschäftszeiten"""
        now = datetime.now()
        # Montag-Freitag, 9-17 Uhr
        return (
            now.weekday() < 5 and  # Montag-Freitag
            9 <= now.hour <= 17
        )
    
    def _determine_priority(self, factors: Dict[str, Any]) -> str:
        """Bestimmt Priorität"""
        if factors['priority'] >= 0.8 or factors['urgency'] == 'hoch':
            return 'high'
        elif factors['priority'] >= 0.5 or factors['urgency'] == 'mittel':
            return 'medium'
        else:
            return 'low'
    
    def _fallback_decision(self) -> DecisionResult:
        """Fallback-Entscheidung bei Fehlern"""
        return DecisionResult(
            action='require_approval',
            confidence=0.1,
            reason="Fallback: Manuelle Überprüfung erforderlich",
            requires_human=True,
            priority='medium',
            estimated_response_time=60
        )
    
    def should_retry_decision(self, previous_decision: DecisionResult, 
                            retry_count: int) -> bool:
        """Bestimmt ob Entscheidung wiederholt werden soll"""
        max_retries = self.security_config.max_retry_attempts
        
        if retry_count >= max_retries:
            return False
        
        # Retry bei niedriger Confidence
        if previous_decision.confidence < 0.5:
            return True
        
        # Retry bei technischen Fehlern
        if previous_decision.action == 'error':
            return True
        
        return False
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Gibt Entscheidungsstatistiken zurück"""
        return {
            'total_decisions': 0,  # Wird in der Praxis erhöht
            'auto_send_count': 0,
            'require_approval_count': 0,
            'reject_count': 0,
            'escalate_count': 0,
            'average_confidence': 0.0,
            'average_response_time': 0.0
        }
    
    def update_decision_rules(self, new_rules: Dict[str, Any]):
        """Aktualisiert Entscheidungsregeln"""
        self.decision_rules.update(new_rules)
        self.logger.info("Entscheidungsregeln aktualisiert")
    
    def validate_decision(self, decision: DecisionResult) -> bool:
        """Validiert eine Entscheidung"""
        # Prüfe Confidence-Bereich
        if not (0.0 <= decision.confidence <= 1.0):
            return False
        
        # Prüfe gültige Aktionen
        valid_actions = ['auto_send', 'require_approval', 'reject', 'escalate']
        if decision.action not in valid_actions:
            return False
        
        # Prüfe Prioritäten
        valid_priorities = ['high', 'medium', 'low']
        if decision.priority not in valid_priorities:
            return False
        
        # Prüfe Response-Zeit
        if decision.estimated_response_time < 0:
            return False
        
        return True