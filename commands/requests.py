"""
Commands for the request system.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_script
from evennia.utils.utils import datetime_format
from evennia.utils.evtable import EvTable
from evennia.utils.search import search_script, search_account
from evennia.accounts.models import AccountDB
from typeclasses.requests import Request, VALID_STATUSES, DEFAULT_CATEGORIES
from datetime import datetime
from evennia.scripts.models import ScriptDB

class CmdRequest(MuxCommand):
    """
    Create and manage requests.
    
    Usage:
        request                     - List your active requests
        request <#>                - View a specific request
        request/new <title>=<text>  - Create a new request
        request/comment <#>=<text>  - Comment on a request
        request/close <#>=<text>    - Close your request with resolution
        request/archive            - List your archived requests
        
    Staff commands:
        request/all                 - List all active requests
        request/assign <#>=<staff>  - Assign request to staff member
        request/status <#>=<status> - Change request status
        request/cat <#>=<category>  - Change request category
        request/archive/all        - List all archived requests
        request/archive <#>        - Archive a request
        request/unarchive <#>      - Unarchive a request
        request/cleanup           - Archive all closed requests older than 30 days
        
    Valid statuses: Open, In Progress, Resolved, Closed
    Valid categories: Bug, Feature, Question, Character, General
    """
    
    key = "request"
    aliases = ["requests"]
    locks = "cmd:pperm(Player)"  # Only accounts with Player permission or higher
    help_category = "Communication"
    
    def find_request(self, request_id):
        """Find a request by its ID number."""
        try:
            id_num = int(str(request_id).lstrip('#'))
            key = f"Request-{id_num}"
            results = ScriptDB.objects.filter(
                db_typeclass_path__contains="requests.Request",
                db_key=key
            )
            return results[0] if results else None
        except (ValueError, IndexError):
            return None
            
    def _check_request_access(self, request):
        """Check if the caller has access to the request."""
        if not request:
            self.caller.msg("Request not found.")
            return False
            
        # Check permissions unless it's a staff member
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            if request.db.submitter != self.caller.account:
                self.caller.msg("You don't have permission to do that.")
                return False
                
        return True
        
    def _format_request_row(self, req):
        """Format a request for table display."""
        if not req or not hasattr(req, 'db'):
            return None
            
        return [
            f"#{req.db.id}",
            req.db.title[:30],
            req.status,
            req.db.submitter.name if req.db.submitter else "Unknown",
            req.db.assigned_to.name if req.db.assigned_to else "Unassigned",
            datetime_format(req.db.date_created, "%Y-%m-%d"),
            datetime_format(req.db.date_modified, "%Y-%m-%d")
        ]
        
    def get_requests(self, show_archived=False):
        """Get all requests, optionally filtering for archived ones."""
        requests = ScriptDB.objects.filter(db_typeclass_path__contains="requests.Request")
        
        if not requests:
            return []
            
        # Filter based on archived status
        filtered = [r for r in requests if bool(r.attributes.get('date_archived') is not None) == show_archived]
        return filtered
        
    def list_requests(self, personal=True, show_archived=False):
        """List requests"""
        requests = self.get_requests(show_archived)
        
        if personal:
            requests = [r for r in requests if r.db.submitter == self.caller.account]
            
        if not requests:
            status = "archived" if show_archived else "active"
            self.caller.msg(f"No {status} requests found.")
            return
            
        table = EvTable(
            "|w#|n",
            "|wTitle|n",
            "|wStatus|n",
            "|wSubmitter|n",
            "|wAssigned To|n",
            "|wCreated|n",
            "|wModified|n",
            border="table"
        )
        
        for req in requests:
            row = self._format_request_row(req)
            if row:
                table.add_row(*row)
            
        status = "Archived" if show_archived else "Active"
        self.caller.msg(f"{status} Requests:")
        self.caller.msg(str(table))
        
    def create_request(self, title, text):
        """Create a new request"""
        if not title.strip():
            self.caller.msg("Request title cannot be empty.")
            return
        if not text.strip():
            self.caller.msg("Request text cannot be empty.")
            return

        # Get the next ID first
        from typeclasses.requests import Request
        next_id = Request.get_next_id()

        # Create the request script
        request = create_script(
            "typeclasses.requests.Request",
            key=f"Request-{next_id}"  # Simple numbered key
        )

        if not request:
            self.caller.msg("Failed to create request.")
            return

        # Set up the request
        request.db.id = next_id
        request.db.title = title.strip()
        request.db.text = text.strip()
        request.db.submitter = self.caller.account
        
        self.caller.msg(f"Request #{request.db.id} created successfully.")
        request.notify_all(f"New request created: {title[:50]}{'...' if len(title) > 50 else ''}")
        
    def view_request(self, request_id):
        """View a specific request"""
        request = self.find_request(request_id)
        if not self._check_request_access(request):
            return
            
        header = f"""Request #{request.db.id}: {request.db.title}
Status: {request.status}  Category: {request.category}
Submitted by: {request.db.submitter.name if request.db.submitter else "Unknown"}
Assigned to: {request.db.assigned_to.name if request.db.assigned_to else "Unassigned"}
Created: {datetime_format(request.db.date_created)}
Modified: {datetime_format(request.db.date_modified)}"""
        
        if request.is_archived:
            header += f"\nArchived: {datetime_format(request.db.date_archived)}"
        
        text = f"\nRequest:\n{request.db.text}\n"
        
        comments = "\nComments:"
        for comment in request.get_comments():
            comments += f"\n[{datetime_format(comment['date'])}] {comment['author'].name}: {comment['text']}"
            
        resolution = ""
        if request.db.resolution:
            resolution = f"\nResolution:\n{request.db.resolution}"
            
        self.caller.msg(header + text + comments + resolution)
        
    def add_comment(self, request_id, text):
        """Add a comment to a request"""
        request = self.find_request(request_id)
        if not self._check_request_access(request):
            return
            
        request.add_comment(self.caller.account, text)  # Pass account object
        self.caller.msg("Comment added.")
        
    def close_request(self, request_id, resolution):
        """Close a request"""
        request = self.find_request(request_id)
        if not self._check_request_access(request):
            return
            
        request.db.resolution = resolution
        request.set_status("Closed")
        self.caller.msg("Request closed.")
        
    def assign_request(self, request_id, staff_name):
        """Assign a request to a staff member"""
        request = self.find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can assign requests
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to assign requests.")
            return
            
        # Try to find the staff account
        staff = AccountDB.objects.filter(username=staff_name).first()
        if not staff:
            self.caller.msg(f"Staff member '{staff_name}' not found.")
            return
            
        request.assign_to(staff)
        self.caller.msg(f"Request assigned to {staff.name}.")
        
    def set_request_status(self, request_id, new_status):
        """Change a request's status"""
        request = self.find_request(request_id)
        if not request:
            self.caller.msg("Request not found.")
            return
            
        # Only staff can change status
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to change request status.")
            return
            
        try:
            request.set_status(new_status)
            self.caller.msg(f"Request status changed to {new_status}.")
        except ValueError as e:
            self.caller.msg(str(e))
            
    def set_request_category(self, request_id, new_category):
        """Change a request's category"""
        request = self.find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can change category
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to change request category.")
            return
            
        try:
            request.set_category(new_category)
            self.caller.msg(f"Request category changed to {new_category}.")
        except ValueError as e:
            self.caller.msg(str(e))
            
    def archive_request(self, request_id):
        """Archive a request"""
        request = self.find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can archive
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to archive requests.")
            return
            
        request.archive()
        self.caller.msg("Request archived.")
        
    def unarchive_request(self, request_id):
        """Unarchive a request"""
        request = self.find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can unarchive
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to unarchive requests.")
            return
            
        request.unarchive()
        self.caller.msg("Request unarchived.")
        
    def cleanup_requests(self):
        """Archive old closed requests"""
        # Only staff can run cleanup
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to run request cleanup.")
            return
            
        requests = self.get_requests(show_archived=False)
        archived = 0
        
        for request in requests:
            if request.should_auto_archive():
                request.archive()
                archived += 1
                
        if archived:
            self.caller.msg(f"Archived {archived} old closed request(s).")
        else:
            self.caller.msg("No requests needed archiving.")
            
    def func(self):
        """Process the request command."""
        if not self.args and not self.switches:
            # List personal active requests
            self.list_requests(personal=True, show_archived=False)
            return
            
        if "all" in self.switches:
            # List all active requests (staff only)
            if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
                self.caller.msg("You don't have permission to list all requests.")
                return
            self.list_requests(personal=False, show_archived=False)
            return
            
        if "archive" in self.switches:
            if not self.args:
                if "all" in self.switches:
                    # List all archived requests (staff only)
                    if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
                        self.caller.msg("You don't have permission to list all archived requests.")
                        return
                    self.list_requests(personal=False, show_archived=True)
                else:
                    # List personal archived requests
                    self.list_requests(personal=True, show_archived=True)
            else:
                # Archive a specific request
                self.archive_request(self.args)
            return
            
        if "unarchive" in self.switches:
            # Unarchive a request
            self.unarchive_request(self.args)
            return
            
        if "cleanup" in self.switches:
            # Run cleanup
            self.cleanup_requests()
            return
            
        if "new" in self.switches:
            # Create a new request
            if not self.rhs:
                self.caller.msg("Usage: request/new <title>=<text>")
                return
            self.create_request(self.lhs.strip(), self.rhs.strip())
            return
            
        if "comment" in self.switches:
            # Add a comment
            if not self.rhs:
                self.caller.msg("Usage: request/comment <#>=<text>")
                return
            self.add_comment(self.lhs, self.rhs.strip())
            return
            
        if "close" in self.switches:
            # Close a request
            if not self.rhs:
                self.caller.msg("Usage: request/close <#>=<resolution>")
                return
            self.close_request(self.lhs, self.rhs.strip())
            return
            
        if "assign" in self.switches:
            # Assign a request
            if not self.rhs:
                self.caller.msg("Usage: request/assign <#>=<staff>")
                return
            self.assign_request(self.lhs, self.rhs.strip())
            return
            
        if "status" in self.switches:
            # Change request status
            if not self.rhs:
                self.caller.msg(f"Usage: request/status <#>=<status>\nValid statuses: {', '.join(VALID_STATUSES)}")
                return
            self.set_request_status(self.lhs, self.rhs.strip())
            return
            
        if "cat" in self.switches:
            # Change request category
            if not self.rhs:
                self.caller.msg(f"Usage: request/cat <#>=<category>\nValid categories: {', '.join(DEFAULT_CATEGORIES)}")
                return
            self.set_request_category(self.lhs, self.rhs.strip())
            return
            
        # If we get here, we're viewing a specific request
        self.view_request(self.args)

class RequestCmdSet(CmdSet):
    """
    Command set for the request system.
    """
    
    key = "request_commands"
    
    def at_cmdset_creation(self):
        """Add request command to the command set."""
        self.add(CmdRequest()) 