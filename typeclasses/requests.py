"""
Request system for player-staff communication.

This module implements a ticket/request system allowing players to create
requests that staff can review and respond to.
"""

from evennia.objects.objects import DefaultObject
from evennia.scripts.scripts import DefaultScript
from evennia.utils import lazy_property
from evennia.utils.utils import datetime_format
from evennia.utils.search import search_object_attribute
from evennia.utils.create import create_script
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

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
        self.interval = 3600  # Run cleanup check every hour
        self.db.requests = []
        
    def at_repeat(self):
        """
        Called every self.interval seconds.
        Check for requests that need auto-archiving or deletion.
        """
        requests = self.db.requests or []
        
        for request in requests[:]:  # Copy list since we might modify it
            if request.is_archived and request.should_be_deleted():
                self.remove_request(request)
                request.delete()
            elif not request.is_archived and request.should_auto_archive():
                request.archive()
        
    def at_start(self):
        """Called when script starts running."""
        self.ndb.last_cleanup = datetime.now()
        
    def at_server_reload(self):
        """Called when server reloads."""
        # Re-validate request list, removing any deleted requests
        if self.db.requests:
            self.db.requests = [r for r in self.db.requests if r and r.pk]
        
    def add_request(self, request):
        """Add a request to the system."""
        if not self.db.requests:
            self.db.requests = []
        if request not in self.db.requests:
            self.db.requests.append(request)
        
    def remove_request(self, request):
        """Remove a request from the system."""
        if request in self.db.requests:
            self.db.requests.remove(request)
            
    @property
    def active_requests(self):
        """Get all non-archived requests."""
        return [r for r in self.db.requests if r and r.pk and not r.db.archived]
        
    @property
    def archived_requests(self):
        """Get all archived requests."""
        return [r for r in self.db.requests if r and r.pk and r.db.archived]

class Request(DefaultObject):
    """
    A request/ticket in the request system.
    
    This is an OOC system for communication between players and staff.
    
    Attributes:
        db.id (int): Unique request identifier
        db.title (str): Short description of the request
        db.text (str): Full details of the request
        db.category (str): Category of request (e.g., "Bug", "Question", "Character", etc.)
        db.status (str): Current status ("Open", "In Progress", "Resolved", "Closed")
        db.submitter (AccountDB): The account who submitted the request
        db.assigned_to (AccountDB): Staff member assigned to handle this request
        db.date_created (datetime): When the request was created
        db.date_modified (datetime): When the request was last modified
        db.comments (list): List of comments on this request
        db.resolution (str): Final resolution notes when request is closed
        db.date_closed (datetime): When the request was closed
        db.archived (bool): Whether this request has been archived
        db.date_archived (datetime): When the request was archived
    """
    
    def at_object_creation(self):
        """Set up the basic properties of the request."""
        super().at_object_creation()
        
        now = datetime.now()
        
        # Basic properties using Evennia's attribute system
        self.db.id = self._get_next_id()  # Unique identifier
        self.db.title = ""                # Short description
        self.db.text = ""                 # Full details
        self.db.category = "General"      # Request category
        self.db.status = "Open"           # Current status
        self.db.submitter = None          # Account who submitted
        self.db.assigned_to = None        # Staff member assigned
        self.db.date_created = now        # Creation timestamp
        self.db.date_modified = now       # Last modified timestamp
        self.db.comments = []             # List of comments
        self.db.resolution = ""           # Resolution notes
        self.db.date_closed = None        # When closed
        self.db.archived = False          # Archive status
        self.db.date_archived = None      # When archived
        
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
        # Use Evennia's search functionality
        existing = search_object_attribute(
            key="id",
            category="request",
            typeclass=cls.__path
        )
        
        used_ids = {obj.db.id for obj in existing if obj.db.id is not None}
        
        next_id = 1
        while next_id in used_ids:
            next_id += 1
            
        return next_id
        
    @property
    def is_closed(self):
        """Check if the request is closed."""
        return self.db.status == "Closed"
        
    @property
    def is_archived(self):
        """Check if the request is archived."""
        return bool(self.db.archived)
        
    def __str__(self):
        """String representation of the request."""
        return f"#{self.db.id}"
        
    def search_query(self):
        """Return search tags and aliases for searching."""
        return f"{self.db.id} {self.db.title} {self.db.text}"
        
    def store_offline_notification(self, account, message: str) -> None:
        """
        Store a notification for an offline user to be shown at next login.
        
        Args:
            account (AccountDB): The account to store the notification for
            message (str): The notification message
        """
        if not account:
            return
            
        # Get or initialize the offline notifications list
        notifications = account.db.offline_request_notifications or []
        notifications.append(f"[Request #{self.db.id}] {message}")
        account.db.offline_request_notifications = notifications

    def notify_users(self, message: str, exclude_account=None) -> None:
        """
        Send a notification about this request to relevant users.
        
        Args:
            message (str): The notification message
            exclude_account (AccountDB, optional): Account to exclude from notification
        """
        # Always notify the submitter (unless excluded)
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
        self.db.date_modified = datetime.now()
        
        # Notify about new comment
        self.notify_users(f"New comment by {author}: {text[:50]}{'...' if len(text) > 50 else ''}")
        
    def get_comments(self) -> List[Dict[str, Any]]:
        """Get all comments on this request."""
        return self.db.comments or []
        
    def assign_to(self, staff_account) -> None:
        """Assign the request to a staff member."""
        old_assigned = self.db.assigned_to
        self.db.assigned_to = staff_account
        self.db.date_modified = datetime.now()
        
        # Notify about assignment
        msg = f"Assigned to {staff_account.name}"
        if old_assigned:
            msg = f"Reassigned from {old_assigned.name} to {staff_account.name}"
        self.notify_users(msg)
        
    def change_status(self, new_status: str, resolution: Optional[str] = None) -> None:
        """Change the status of this request."""
        old_status = self.db.status
        valid_statuses = ["Open", "In Progress", "Resolved", "Closed"]
        if new_status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
            
        self.db.status = new_status
        if new_status == "Closed":
            self.db.date_closed = datetime.now()
            
        if resolution:
            self.db.resolution = resolution
        self.db.date_modified = datetime.now()
        
        # Notify about status change
        msg = f"Status changed from {old_status} to {new_status}"
        if resolution:
            msg += f"\nResolution: {resolution[:50]}{'...' if len(resolution) > 50 else ''}"
        self.notify_users(msg)
            
    def archive(self) -> None:
        """Archive this request."""
        self.db.archived = True
        self.db.date_archived = datetime.now()
        self.db.date_modified = datetime.now()
        
        # Notify about archiving
        self.notify_users("This request has been archived.")
        
    def unarchive(self) -> None:
        """Unarchive this request."""
        self.db.archived = False
        self.db.date_archived = None
        self.db.date_modified = datetime.now()
        
        # Notify about unarchiving
        self.notify_users("This request has been unarchived.")
        
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
        
    def at_post_unpuppet(self, account, session=None, **kwargs):
        """Called just after account stops puppeting."""
        super().at_post_unpuppet(account, session=session, **kwargs)
        # Update account reference if character is deleted
        if self.db.submitter and not self.db.submitter.pk:
            self.db.submitter = None 