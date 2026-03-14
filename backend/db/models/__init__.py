# db/models/__init__.py

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .organisation import Organisation
from .organisation_phone import OrganisationPhoneNumber
from .company import Company
from .farmer import Farmer
from .farmer_query import FarmerQuery
from .farmer_questions import FarmerQuestion
from .product import Product
from .brand import Brand
from .kb_entry import KBEntry
from .organisation_kb import OrganisationKnowledgeBase
from .knowledge_base import KnowledgeEntry
from .advisory import Advisory
from .call_session import CallSession
from .call_state import CallState
from .call_transcript import CallTranscript
from .call_summary import CallSummary
from .call_metrics import CallMetrics
from .case import Case
from .escalation import Escalation
from .audit import AuditLog
from .conversation_memory import ConversationMemory

__all__ = [
    "User",
    "Organisation", 
    "OrganisationPhoneNumber",
    "Company",
    "Farmer",
    "FarmerQuery",
    "FarmerQuestion",
    "Product",
    "Brand",
    "KBEntry",
    "OrganisationKnowledgeBase",
    "KnowledgeEntry",
    "Advisory",
    "CallSession",
    "CallState",
    "CallTranscript",
    "CallSummary",
    "CallMetrics",
    "Case",
    "Escalation",
    "AuditLog",
    "ConversationMemory"
]
