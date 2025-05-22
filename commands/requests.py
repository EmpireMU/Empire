"""
Commands for the request system.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_script
from evennia.utils.utils import datetime_format
from evennia.utils.evtable import EvTable
from evennia.utils.search import search_script
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
    
    def _find_request(self, request_id):
        """Find a request by its ID number."""
        try:
            id_num = int(str(request_id).lstrip('#'))
            results = search_script(
                "typeclasses.requests.Request",
                id=id_num
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
        
    def _get_requests(self, show_archived=False):
        """Get all requests, optionally filtering for archived ones."""
        # First try direct database query
        self.caller.msg("DEBUG: Querying database for requests...")
        requests = ScriptDB.objects.filter(db_typeclass_path__contains="requests.Request")
        self.caller.msg(f"DEBUG: Database query found {requests.count()} scripts")
        
        # Show raw database entries
        for script_db in requests:
            self.caller.msg(f"DEBUG: Raw DB entry - path={script_db.db_typeclass_path}, key={script_db.db_key}")
        
        # Convert to list of typeclassed objects
        requests = [r.typeclass for r in requests]
        
        # Show details about each found script
        for r in requests:
            self.caller.msg(f"DEBUG: Found script key={r.key}, dbref={r.dbref}, id={r.id}, typeclass={r.__class__.__module__}.{r.__class__.__name__}")
            if hasattr(r, 'db'):
                self.caller.msg(f"DEBUG: - Request ID={r.db.id}, title={r.db.title}, archived={r.db.date_archived}")
            else:
                self.caller.msg(f"DEBUG: - No db attributes found")
        
        if not requests:
            return []
            
        # Filter based on archived status
        filtered = [r for r in requests if bool(r.db.date_archived is not None) == show_archived]
        self.caller.msg(f"DEBUG: After archive filtering, {len(filtered)} requests remain")
        
        # Show what's being returned
        for r in filtered:
            self.caller.msg(f"DEBUG: Returning request ID={r.db.id}, title={r.db.title}")
        
        return filtered
        
    def _list_requests(self, personal=True, show_archived=False):
        """List requests"""
        requests = self._get_requests(show_archived)
        
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
        
    def _create_request(self, title, text):
        """Create a new request"""
        if not title.strip():
            self.caller.msg("Request title cannot be empty.")
            return
        if not text.strip():
            self.caller.msg("Request text cannot be empty.")
            return

        # Create the request script
        self.caller.msg("DEBUG: Creating new request script...")
        request = create_script(
            "typeclasses.requests.Request",
            key=f"Request-{datetime.now().strftime('%Y%m%d-%H%M%S')}"  # More unique key
        )

        if not request:
            self.caller.msg("Failed to create request.")
            return

        # Set up the request
        self.caller.msg(f"DEBUG: Setting up request with ID {request.db.id}")
        request.db.title = title.strip()
        request.db.text = text.strip()
        request.db.submitter = self.caller.account
        
        self.caller.msg(f"Request #{request.db.id} created successfully.")
        request.notify_all(f"New request created: {title[:50]}{'...' if len(title) > 50 else ''}")
        
        # Debug: verify the request exists and is searchable
        found = search_script("typeclasses.requests.Request", id=request.db.id)
        self.caller.msg(f"DEBUG: Immediate search found {len(found)} matching requests")
        
    def _view_request(self, request_id):
        """View a specific request"""
        request = self._find_request(request_id)
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
            comments += f"\n[{datetime_format(comment['date'])}] {comment['author']}: {comment['text']}"
            
        resolution = ""
        if request.db.resolution:
            resolution = f"\nResolution:\n{request.db.resolution}"
            
        self.caller.msg(header + text + comments + resolution)
        
    def _add_comment(self, request_id, text):
        """Add a comment to a request"""
        request = self._find_request(request_id)
        if not self._check_request_access(request):
            return
            
        request.add_comment(self.caller.account.name, text)
        self.caller.msg("Comment added.")
        
    def _close_request(self, request_id, resolution):
        """Close a request"""
        request = self._find_request(request_id)
        if not self._check_request_access(request):
            return
            
        request.db.resolution = resolution
        request.set_status("Closed")
        self.caller.msg("Request closed.")
        
    def _assign_request(self, request_id, staff_name):
        """Assign a request to a staff member"""
        request = self._find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can assign requests
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to assign requests.")
            return
            
        staff = AccountDB.objects.get_account_from_string(staff_name)
        if not staff:
            self.caller.msg(f"Staff member '{staff_name}' not found.")
            return
            
        request.assign_to(staff)
        self.caller.msg(f"Request assigned to {staff.name}.")
        
    def _change_status(self, request_id, status):
        """Change request status"""
        request = self._find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can change status
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to change request status.")
            return
            
        try:
            request.set_status(status)
            self.caller.msg(f"Status changed to: {status}")
        except ValueError as e:
            self.caller.msg(str(e))
        
    def _change_category(self, request_id, category):
        """Change request category"""
        request = self._find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can change category
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to change request category.")
            return
            
        try:
            request.set_category(category)
            self.caller.msg(f"Category changed to: {category}")
        except ValueError as e:
            self.caller.msg(str(e))
        
    def _archive_request(self, request_id):
        """Archive a request"""
        request = self._find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can archive
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to archive requests.")
            return
            
        request.archive()
        self.caller.msg("Request archived.")
        
    def _unarchive_request(self, request_id):
        """Unarchive a request"""
        request = self._find_request(request_id)
        if not self._check_request_access(request):
            return
            
        # Only staff can unarchive
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to unarchive requests.")
            return
            
        request.unarchive()
        self.caller.msg("Request unarchived.")
        
    def _cleanup_old_requests(self):
        """Archive old closed requests"""
        # Only staff can run cleanup
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("You don't have permission to run cleanup.")
            return
            
        count = 0
        for request in self._get_requests(show_archived=False):
            if request.should_auto_archive():
                request.archive()
                count += 1
                
        self.caller.msg(f"Archived {count} old closed requests.")
        
    def func(self):
        """Handle the request command"""
        if not self.args and not self.switches:
            # List personal active requests
            self._list_requests()
            return
            
        if not self.switches:
            # View specific request
            self._view_request(self.args)
            return
            
        switch = self.switches[0].lower()
        
        if switch == "new":
            if not self.args or "=" not in self.args:
                self.caller.msg("Usage: request/new <title>=<text>")
                return
            self._create_request(self.lhs.strip(), self.rhs.strip())
            
        elif switch == "comment":
            if not self.args or "=" not in self.args:
                self.caller.msg("Usage: request/comment <#>=<text>")
                return
            self._add_comment(self.lhs, self.rhs)
            
        elif switch == "close":
            if not self.args or "=" not in self.args:
                self.caller.msg("Usage: request/close <#>=<resolution>")
                return
            self._close_request(self.lhs, self.rhs)
            
        elif switch == "assign":
            if not self.args or "=" not in self.args:
                self.caller.msg("Usage: request/assign <#>=<staff>")
                return
            self._assign_request(self.lhs, self.rhs)
            
        elif switch == "status":
            if not self.args or "=" not in self.args:
                self.caller.msg(f"Usage: request/status <#>=<status>\nValid statuses: {', '.join(VALID_STATUSES)}")
                return
            self._change_status(self.lhs, self.rhs)
            
        elif switch == "cat":
            if not self.args or "=" not in self.args:
                self.caller.msg(f"Usage: request/cat <#>=<category>\nValid categories: {', '.join(DEFAULT_CATEGORIES)}")
                return
            self._change_category(self.lhs, self.rhs)
            
        elif switch == "archive":
            if self.args == "all":
                self._list_requests(personal=False, show_archived=True)
            else:
                self._archive_request(self.args)
                
        elif switch == "unarchive":
            self._unarchive_request(self.args)
            
        elif switch == "cleanup":
            self._cleanup_old_requests()
            
        elif switch == "all":
            self._list_requests(personal=False)
            
        else:
            self.caller.msg("Invalid switch. See help request for valid options.")

class RequestCmdSet(CmdSet):
    """
    Command set for the request system.
    """
    
    key = "request_commands"
    
    def at_cmdset_creation(self):
        """Add request command to the command set."""
        self.add(CmdRequest()) 