"""
Request system for player-staff communication.

This module implements a ticket/request system allowing players to create
requests that staff can review and respond to.
"""

from evennia.objects.objects import DefaultObject
from evennia.scripts.scripts import DefaultScript
from evennia.utils.utils import datetime_format
from evennia.utils.search import search_object_attribute
from evennia.utils.create import create_script
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from functools import wraps

# Valid request statuses
VALID_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

# Default request categories
DEFAULT_CATEGORIES = ["Bug", "Feature", "Question", "Character", "Other"]

# Auto-archive and deletion thresholds (in days)
AUTO_ARCHIVE_DAYS = 30
AUTO_DELETE_DAYS = 60

def update_modified(func):
    """Decorator to update the modified timestamp."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.db.date_modified = datetime.now()
        return result
    return wrapper

class RequestHandler(DefaultScript):
    """
    Script to handle global request management.
    This follows Evennia's paradigm of using Scripts for global state.
    """
    def at_script_creation(self):
        """Set up the script."""
        self.key = "request_handler"
        self.desc = "Handles the request/ticket system"
        self.persistent = True
        self.interval = 86400  # Run cleanup check once per day
        self.db.requests = []
        
    def at_repeat(self):
        """
        Called every self.interval seconds.
        Check for requests that need auto-archiving or deletion.
        """
        for request in self._valid_requests(archived=True):
            if request.should_be_deleted():
                self.remove_request(request)
                request.delete()
                
        for request in self._valid_requests(archived=False):
            if request.should_auto_archive():
                request.archive()
        
    def at_start(self):
        """Called when script starts running."""
        self.ndb.last_cleanup = datetime.now()
        
    def at_server_reload(self):
        """Called when server reloads."""
        if self.db.requests:
            # Remove invalid references
            self.db.requests = [r for r in self.db.requests if r and r.pk]
            
    @property
    def requests(self):
        """Get or initialize the requests list."""
        if not self.db.requests:
            self.db.requests = []
        return self.db.requests
        
    def add_request(self, request):
        """Add a request to the system."""
        if request not in self.requests:
            self.requests.append(request)
        
    def remove_request(self, request):
        """Remove a request from the system."""
        if request in self.requests:
            self.requests.remove(request)
            
    def _valid_requests(self, archived=False):
        """Get valid requests filtered by archive status."""
        return [r for r in self.requests if r and r.pk and r.tags.has("Archived", category="request_status") == archived]
            
    @property
    def active_requests(self):
        """Get all non-archived requests."""
        return self._valid_requests(archived=False)
        
    @property
    def archived_requests(self):
        """Get all archived requests."""
        return self._valid_requests(archived=True)

class Request(DefaultObject):
    """
    A request/ticket in the request system.
    
    This is an OOC system for communication between players and staff.
    
    Tags:
        request_status: Current status (Open, In Progress, Resolved, Closed, Archived)
        request_category: Type of request (Bug, Feature, Question, etc.)
    
    Attributes:
        db.id (int): Unique request identifier
        db.title (str): Short description
        db.text (str): Full details
        db.submitter (AccountDB): Account who submitted
        db.assigned_to (AccountDB): Staff member assigned
        db.date_created (datetime): Creation timestamp
        db.date_modified (datetime): Last modified timestamp
        db.comments (list): List of comment dicts
        db.resolution (str): Resolution notes when closed
        db.date_closed (datetime): When request was closed
        db.date_archived (datetime): When request was archived
    """
    
    def at_object_creation(self):
        """Set up the basic properties of the request."""
        super().at_object_creation()
        
        now = datetime.now()
        
        # Basic properties using Evennia's attribute system
        self.db.id = self._get_next_id()
        self.db.title = ""
        self.db.text = ""
        self.db.submitter = None
        self.db.assigned_to = None
        self.db.date_created = now
        self.db.date_modified = now
        self.db.comments = []
        self.db.resolution = ""
        self.db.date_closed = None
        self.db.date_archived = None
        
        # Initial tags
        self.tags.add("Open", category="request_status")
        self.tags.add("Other", category="request_category")
        
        # Set up locks using Evennia's lock system
        self.locks.add(
            "get:false();"  # Cannot be picked up
            "edit:id(%(submitter)s) or perm(Admin);"  # Submitter or Admin can edit
            "view:id(%(submitter)s) or perm(Admin)"   # Submitter or Admin can view
        )
        
        # Add to the request handler
        self.add_to_handler()
        
    def add_to_handler(self):
        """Add this request to the global handler."""
        handler = self.get_or_create_handler()
        handler.add_request(self)
        
    @classmethod
    def get_or_create_handler(cls):
        """Get or create the request handler script."""
        from evennia import GLOBAL_SCRIPTS
        
        handler = GLOBAL_SCRIPTS.get("request_handler")
        if not handler:
            handler = create_script(RequestHandler)
        return handler
        
    @classmethod
    def _get_next_id(cls):
        """Get the next available ID, reusing deleted ones."""
        existing = search_object_attribute(
            key="id",
            category="request",
            typeclass=cls.path()
        )
        
        used_ids = {obj.db.id for obj in existing if obj.db.id is not None}
        
        next_id = 1
        while next_id in used_ids:
            next_id += 1
            
        return next_id
        
    def check_permission(self, account, action="view"):
        """
        Check if an account has permission for an action.
        
        Args:
            account (AccountDB): The account to check
            action (str): The action to check ("view" or "edit")
            
        Returns:
            bool: True if account has permission, False otherwise
        """
        return (
            account.locks.check_lockstring(account, "perm(Admin)") or
            (action in ["view", "edit"] and self.db.submitter == account)
        )
        
    @property
    def status(self):
        """Get current status from tags."""
        for status in VALID_STATUSES + ["Archived"]:
            if self.tags.has(status, category="request_status"):
                return status
        return "Unknown"
        
    @property
    def category(self):
        """Get current category from tags."""
        for category in DEFAULT_CATEGORIES:
            if self.tags.has(category, category="request_category"):
                return category
        return "Other"
        
    @property
    def is_closed(self):
        """Check if the request is closed."""
        return self.status == "Closed"
        
    @property
    def is_archived(self):
        """Check if the request is archived."""
        return self.tags.has("Archived", category="request_status")
        
    def __str__(self):
        """String representation of the request."""
        return f"#{self.db.id}"
        
    def set_status(self, new_status: str) -> None:
        """
        Change the request status.
        
        Args:
            new_status (str): New status to set
        """
        if new_status not in VALID_STATUSES and new_status != "Archived":
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
            
        # Remove old status tag
        old_status = self.status
        self.tags.remove(old_status, category="request_status")
        
        # Add new status tag
        self.tags.add(new_status, category="request_status")
        
        # Update timestamps
        self.db.date_modified = datetime.now()
        if new_status == "Closed":
            self.db.date_closed = datetime.now()
            
        # Notify about status change
        self.notify_all(f"Status changed from {old_status} to {new_status}")
        
    def set_category(self, new_category: str) -> None:
        """
        Change the request category.
        
        Args:
            new_category (str): New category to set
        """
        if new_category not in DEFAULT_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(DEFAULT_CATEGORIES)}")
            
        # Remove old category tag
        old_category = self.category
        self.tags.remove(old_category, category="request_category")
        
        # Add new category tag
        self.tags.add(new_category, category="request_category")
        
        # Update modified timestamp
        self.db.date_modified = datetime.now()
        
        # Notify about category change
        self.notify_all(f"Category changed from {old_category} to {new_category}")
        
    def add_comment(self, author: str, text: str) -> None:
        """Add a comment to the request."""
        if not self.db.comments:
            self.db.comments = []
            
        comment = {
            "author": author,
            "text": text,
            "date": datetime.now()
        }
        self.db.comments.append(comment)
        
        # Update modified timestamp
        self.db.date_modified = datetime.now()
        
        # Notify about new comment
        self.notify_all(f"New comment by {author}: {text[:50]}{'...' if len(text) > 50 else ''}")
        
    def get_comments(self) -> List[Dict[str, Any]]:
        """Get all comments on this request."""
        return self.db.comments or []
        
    def assign_to(self, staff_account) -> None:
        """Assign the request to a staff member."""
        old_assigned = self.db.assigned_to
        self.db.assigned_to = staff_account
        
        # Update modified timestamp
        self.db.date_modified = datetime.now()
        
        # Notify about assignment
        msg = f"Assigned to {staff_account.name}"
        if old_assigned:
            msg = f"Reassigned from {old_assigned.name} to {staff_account.name}"
        self.notify_all(msg)
        
    def archive(self) -> None:
        """Archive this request."""
        if not self.is_archived:
            self.set_status("Archived")
            self.db.date_archived = datetime.now()
            self.notify_all("This request has been archived.")
        
    def unarchive(self) -> None:
        """Unarchive this request."""
        if self.is_archived:
            # Restore to closed status if it was closed
            new_status = "Closed" if self.db.date_closed else "Open"
            self.set_status(new_status)
            self.db.date_archived = None
            self.notify_all("This request has been unarchived.")
        
    def should_auto_archive(self) -> bool:
        """Check if this request should be automatically archived."""
        if not self.is_closed or not self.db.date_closed:
            return False
            
        archive_after = timedelta(days=30)
        return datetime.now() - self.db.date_closed > archive_after
        
    def should_be_deleted(self) -> bool:
        """Check if this archived request should be deleted."""
        if not self.is_archived or not self.db.date_archived:
            return False
            
        delete_after = timedelta(days=60)
        return datetime.now() - self.db.date_archived > delete_after
        
    def notify_all(self, message: str, exclude_account: Optional['AccountDB'] = None) -> None:
        """
        Send a notification to all relevant parties.
        
        Args:
            message (str): The message to send
            exclude_account (AccountDB, optional): Account to exclude from notification
        """
        # Notify submitter if not excluded
        if self.db.submitter and self.db.submitter != exclude_account:
            if self.db.submitter.is_connected:
                self.db.submitter.msg(f"[Request #{self.db.id}] {message}")
            else:
                self.store_offline_notification(self.db.submitter, message)
                
        # Notify assigned staff member if different from submitter
        if self.db.assigned_to and self.db.assigned_to != self.db.submitter and self.db.assigned_to != exclude_account:
            if self.db.assigned_to.is_connected:
                self.db.assigned_to.msg(f"[Request #{self.db.id}] {message}")
            else:
                self.store_offline_notification(self.db.assigned_to, message)
                
    def store_offline_notification(self, account: 'AccountDB', message: str) -> None:
        """
        Store a notification for an offline user.
        
        Args:
            account (AccountDB): The account to store the notification for
            message (str): The notification message
        """
        if not account:
            return
            
        notifications = account.db.offline_request_notifications or []
        notifications.append(f"[Request #{self.db.id}] {message}")
        account.db.offline_request_notifications = notifications

    def search_query(self) -> str:
        """Return search tags and aliases for searching."""
        return f"{self.db.id} {self.db.title} {self.db.text}"
        
    def at_post_unpuppet(self, account, session=None, **kwargs):
        """Called just after account stops puppeting."""
        super().at_post_unpuppet(account, session=session, **kwargs)
        # Update account reference if character is deleted
        if self.db.submitter and not self.db.submitter.pk:
            self.db.submitter = None 