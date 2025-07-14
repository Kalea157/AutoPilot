"""
Email data models for Super-KI-Agent
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class EmailCategory(Enum):
    """Email categories"""
    REQUEST = "request"
    COMPLAINT = "complaint"
    ORDER = "order"
    SUPPORT = "support"
    INVOICE = "invoice"
    OTHER = "other"


class EmailSentiment(Enum):
    """Email sentiment"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class EmailUrgency(Enum):
    """Email urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmailLanguage(Enum):
    """Supported languages"""
    GERMAN = "de"
    ENGLISH = "en"
    FRENCH = "fr"
    SPANISH = "es"
    ITALIAN = "it"


@dataclass
class EmailAddress:
    """Email address model"""
    email: str
    name: Optional[str] = None
    
    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclass
class EmailAttachment:
    """Email attachment model"""
    filename: str
    content_type: str
    size: int
    data: bytes


@dataclass
class EmailAnalysis:
    """AI analysis results for an email"""
    sentiment: EmailSentiment
    category: EmailCategory
    urgency: EmailUrgency
    language: EmailLanguage
    confidence: float
    key_points: List[str]
    suggested_actions: List[str]
    priority_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "sentiment": self.sentiment.value,
            "category": self.category.value,
            "urgency": self.urgency.value,
            "language": self.language.value,
            "confidence": self.confidence,
            "key_points": self.key_points,
            "suggested_actions": self.suggested_actions,
            "priority_score": self.priority_score
        }


@dataclass
class EmailMessage:
    """Complete email message model"""
    # Basic email info
    message_id: str
    subject: str
    sender: EmailAddress
    recipients: List[EmailAddress]
    cc: List[EmailAddress]
    bcc: List[EmailAddress]
    
    # Content
    body_text: str
    body_html: Optional[str] = None
    attachments: List[EmailAttachment]
    
    # Metadata
    date_received: datetime
    date_sent: Optional[datetime] = None
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    
    # Processing info
    is_read: bool = False
    is_processed: bool = False
    analysis: Optional[EmailAnalysis] = None
    generated_response: Optional[str] = None
    decision: Optional[str] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if not hasattr(self, 'attachments') or self.attachments is None:
            self.attachments = []
    
    def get_priority_keywords(self) -> List[str]:
        """Extract priority keywords from subject and body"""
        priority_words = ["urgent", "wichtig", "dringend", "asap", "sofort", "kritisch"]
        text = f"{self.subject} {self.body_text}".lower()
        return [word for word in priority_words if word in text]
    
    def has_attachments(self) -> bool:
        """Check if email has attachments"""
        return len(self.attachments) > 0
    
    def get_attachment_count(self) -> int:
        """Get number of attachments"""
        return len(self.attachments)
    
    def get_total_size(self) -> int:
        """Get total size including attachments"""
        total = len(self.body_text.encode('utf-8'))
        if self.body_html:
            total += len(self.body_html.encode('utf-8'))
        for attachment in self.attachments:
            total += attachment.size
        return total
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "message_id": self.message_id,
            "subject": self.subject,
            "sender": {
                "email": self.sender.email,
                "name": self.sender.name
            },
            "recipients": [
                {"email": r.email, "name": r.name} for r in self.recipients
            ],
            "cc": [{"email": c.email, "name": c.name} for c in self.cc],
            "bcc": [{"email": b.email, "name": b.name} for b in self.bcc],
            "body_text": self.body_text,
            "body_html": self.body_html,
            "date_received": self.date_received.isoformat(),
            "date_sent": self.date_sent.isoformat() if self.date_sent else None,
            "thread_id": self.thread_id,
            "in_reply_to": self.in_reply_to,
            "is_read": self.is_read,
            "is_processed": self.is_processed,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "generated_response": self.generated_response,
            "decision": self.decision,
            "confidence": self.confidence,
            "attachment_count": self.get_attachment_count(),
            "total_size": self.get_total_size()
        }


@dataclass
class EmailResponse:
    """Generated email response"""
    original_email: EmailMessage
    response_text: str
    response_html: Optional[str] = None
    confidence: float
    decision: str
    requires_approval: bool
    auto_approved: bool = False
    approval_timeout: Optional[datetime] = None
    
    def is_approved(self) -> bool:
        """Check if response is approved"""
        return self.auto_approved or (not self.requires_approval)
    
    def is_expired(self) -> bool:
        """Check if approval timeout has expired"""
        if not self.approval_timeout:
            return False
        return datetime.now() > self.approval_timeout
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "original_email_id": self.original_email.message_id,
            "response_text": self.response_text,
            "response_html": self.response_html,
            "confidence": self.confidence,
            "decision": self.decision,
            "requires_approval": self.requires_approval,
            "auto_approved": self.auto_approved,
            "approval_timeout": self.approval_timeout.isoformat() if self.approval_timeout else None,
            "is_approved": self.is_approved(),
            "is_expired": self.is_expired()
        }