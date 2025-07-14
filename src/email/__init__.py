"""
Email handling components for the Super AI Agent
"""

from .fetcher import EmailFetcher, EmailMessage
from .sender import EmailSender, EmailResponse

__all__ = ['EmailFetcher', 'EmailMessage', 'EmailSender', 'EmailResponse']