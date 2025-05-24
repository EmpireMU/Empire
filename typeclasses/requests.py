"""
Request system for player-staff communication.

This module implements a ticket/request system allowing players to create
requests that staff can review and respond to.
"""

from evennia.scripts.scripts import DefaultScript
from evennia.utils.utils import datetime_format
from evennia.utils.search import search_script
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Valid request statuses
VALID_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

# Default request categories
DEFAULT_CATEGORIES = ["Bug", "Feature", "Question", "Character", "General"]

# Auto-archive and deletion thresholds (in days)
AUTO_ARCHIVE_DAYS = 30
AUTO_DELETE_DAYS = 60

class Request(DefaultScript):
    """
    A request/ticket in the request system.
    
    This is an OOC system for communication between players and staff.
    """
    
    def at_script_creation(self):
        """Set up the basic properties of the request."""
        super().at_script_creation()
        
        now = datetime.now()
        
        # Basic properties using Evennia's attribute system
        self.db.id = self.get_next_id()
        self.db.title = ""
        self.db.text = ""
        self.db.submitter = None
        self.db.assigned_to = None
        self.db.date_created = now
        self.db.date_modified = now
        self.db.comments = []
        self.db.resolution = ""
        self.db.date_closed = None
        self.db.date_archived = None  # Explicitly set to None for filtering
        self.db.status = "Open"
        self.db.category = "General"
        
        # Make sure this script never repeats or times out
        self.interval = -1  # -1 means never repeat
        self.persistent = True

    @classmethod
    def get_next_id(cls):
        """Get the next available request ID."""
        from evennia.scripts.models import ScriptDB
        
        # Find all requests using direct database query
        requests = ScriptDB.objects.filter(db_typeclass_path__contains="requests.Request")
        if not requests.exists():
            return 1
            
        # Get the highest ID and increment
        max_id = 0
        for request in requests:
            try:
                if request.db.id and request.db.id > max_id:
                    max_id = request.db.id
            except AttributeError:
                continue
                
        return max_id + 1

    @property
    def status(self):
        """Get the current status."""
        return self.db.status
        
    @property
    def category(self):
        """Get the current category."""
        return self.db.category
        
    @property
    def is_closed(self):
        """Check if the request is closed."""
        return self.status == "Closed"
        
    @property
    def is_archived(self):
        """Check if the request is archived."""
        return bool(self.db.date_archived)
        
    def set_status(self, new_status):
        """Change the request status."""
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
            
        old_status = self.status
        self.db.status = new_status
        
        # Update timestamps
        self.db.date_modified = datetime.now()
        if new_status == "Closed":
            self.db.date_closed = datetime.now()
            
        self.notify_all(f"Status changed from {old_status} to {new_status}")
        
    def set_category(self, new_category):
        """Change the request category."""
        if new_category not in DEFAULT_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(DEFAULT_CATEGORIES)}")
            
        old_category = self.category
        self.db.category = new_category
        
        # Update timestamp
        self.db.date_modified = datetime.now()
        
        self.notify_all(f"Category changed from {old_category} to {new_category}")
        
    def assign_to(self, staff_account):
        """Assign the request to a staff member."""
        old_assigned = self.db.assigned_to
        self.db.assigned_to = staff_account
        self.db.date_modified = datetime.now()
        
        msg = f"Assigned to {staff_account.name}"
        if old_assigned:
            msg = f"Reassigned from {old_assigned.name} to {staff_account.name}"
        self.notify_all(msg)
        
    def add_comment(self, author, text):
        """Add a comment to the request.
        
        Args:
            author (AccountDB): The account adding the comment
            text (str): The comment text
        """
        comment = {
            "author": author,  # Store the account object
            "text": text,
            "date": datetime.now()
        }
        
        if not self.db.comments:
            self.db.comments = []
            
        self.db.comments.append(comment)
        self.db.date_modified = datetime.now()
        
        self.notify_all(f"New comment by {author.name}")
        
    def get_comments(self):
        """Get all comments on this request."""
        return self.db.comments or []
        
    def archive(self):
        """Archive this request."""
        if not self.is_archived:
            self.db.date_archived = datetime.now()
            self.db.date_modified = datetime.now()
            self.notify_all("This request has been archived.")
            
    def unarchive(self):
        """Unarchive this request."""
        if self.is_archived:
            self.db.date_archived = None
            self.db.date_modified = datetime.now()
            self.notify_all("This request has been unarchived.")
            
    def should_auto_archive(self):
        """Check if this request should be automatically archived."""
        if not self.is_closed or not self.db.date_closed:
            return False
            
        archive_after = timedelta(days=AUTO_ARCHIVE_DAYS)
        return datetime.now() - self.db.date_closed > archive_after
        
    def should_be_deleted(self):
        """Check if this archived request should be deleted."""
        if not self.is_archived or not self.db.date_archived:
            return False
            
        delete_after = timedelta(days=AUTO_DELETE_DAYS)
        return datetime.now() - self.db.date_archived > delete_after
        
    def notify_all(self, message, exclude_account=None):
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
                
    def store_offline_notification(self, account, message):
        """Store a notification for an offline user."""
        if not account:
            return
            
        notifications = account.db.offline_request_notifications or []
        notifications.append(f"[Request #{self.db.id}] {message}")
        account.db.offline_request_notifications = notifications
        
    @classmethod
    def get_or_create_handler(cls):
        """Get the request handler object."""
        # This is a compatibility method for the old system
        # It's not needed anymore since we're using objects directly
        return None 

    def migrate_category(self):
        """
        Migrate the request's category to a valid one if it's no longer valid.
        Returns True if migration was needed, False otherwise.
        """
        if self.db.category not in DEFAULT_CATEGORIES:
            old_category = self.db.category
            self.db.category = "General"
            self.db.date_modified = datetime.now()
            self.notify_all(f"Category migrated from {old_category} to General (old category no longer valid)")
            return True
        return False

    @classmethod
    def migrate_all_categories(cls):
        """
        Migrate all requests with invalid categories to use valid ones.
        Returns the number of requests that were migrated.
        """
        count = 0
        for request in search_script("typeclasses.requests.Request"):
            if request.migrate_category():
                count += 1
        return count 