from sqlalchemy.ext.declarative import declarative_base

# Create Base for all models
Base = declarative_base()

from .user import User
from .contest import Contest
from .entry import Entry
from .official_rules import OfficialRules
from .notification import Notification
from .admin_profile import AdminProfile
from .sms_template import SMSTemplate
from .sponsor_profile import SponsorProfile
from .role_audit import RoleAudit, ContestApprovalAudit

__all__ = [
    "Base",
    "User", 
    "Contest", 
    "Entry", 
    "OfficialRules", 
    "Notification", 
    "AdminProfile", 
    "SMSTemplate",
    "SponsorProfile",
    "RoleAudit",
    "ContestApprovalAudit"
]
