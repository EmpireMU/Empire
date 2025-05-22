"""
Commands for the request system.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_object
from evennia.utils.utils import datetime_format
from evennia.utils.evtable import EvTable
from evennia.utils.search import search_object_attribute
from evennia.accounts.models import AccountDB
from typeclasses.requests import Request, RequestHandler
from datetime import datetime
from functools import wraps

def staff_only(func):
    """Decorator for staff-only commands."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            self.caller.msg("Only staff can use this command.")
            return
        return func(self, *args, **kwargs)
    return wrapper

def requires_request(func):
    """Decorator to handle request lookup and permission checks."""
    @wraps(func)
    def wrapper(self, request_id, *args, **kwargs):
        request = self._find_request(request_id)
        if not request:
            self.caller.msg("Request not found.")
            return
            
        # Check permissions unless it's a staff member
        if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
            if request.db.submitter != self.caller.account:
                self.caller.msg("You don't have permission to do that.")
                return
                
        return func(self, request, *args, **kwargs)
    return wrapper

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
        
    Examples:
        request/new Bug Report=The crafting menu is not working
        request/comment 42=Any update on this?
        request/close 42=Issue resolved
        
    Staff examples:
        request/assign 42=Bob
        request/status 42=In Progress
        request/cleanup
        
    This is an OOC command for communication between players and staff.
    Closed requests are automatically archived after 30 days.
    Archived requests are deleted after 60 days in the archive.
    
    Request numbers (#) are unique and may be reused after a request
    is permanently deleted from the archive.
    """
    
    key = "request"
    aliases = ["requests"]
    locks = "cmd:pperm(Player)"  # Only accounts with Player permission or higher
    help_category = "Communication"
    
    @property
    def request_handler(self):
        """Get the request handler."""
        return Request.get_or_create_handler()
    
    def _find_request(self, request_id):
        """Find a request by its ID number."""
        try:
            id_num = int(str(request_id).lstrip('#'))
            # Use Evennia's search functionality
            results = search_object_attribute(
                key="id",
                value=id_num,
                category="request",
                typeclass=Request.path()
            )
            return results[0] if results else None
        except (ValueError, IndexError):
            return None
        
    def _format_request_row(self, req):
        """Format a request for table display."""
        if not req or not req.pk:
            return None
            
        return [
            f"#{req.db.id}",
            req.db.title[:30],
            req.db.status,
            req.db.submitter.name if req.db.submitter else "Unknown",
            req.db.assigned_to.name if req.db.assigned_to else "Unassigned",
            datetime_format(req.db.date_created, "%Y-%m-%d"),
            datetime_format(req.db.date_modified, "%Y-%m-%d")
        ]
        
    def _list_requests(self, personal=True, show_archived=False):
        """List requests"""
        handler = self.request_handler
        requests = handler.archived_requests if show_archived else handler.active_requests
        
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
        request = create_object(
            typeclass="typeclasses.requests.Request",
            key="Request",  # The handler will manage this
            location=None,  # Requests don't need a location
            home=None,     # Or a home
            permissions=None,
            locks=None,
            aliases=None,
            tags=None,
            attributes=None,
            nohome=True
        )
        request.db.title = title
        request.db.text = text
        request.db.submitter = self.caller.account
        
        self.caller.msg(f"Request #{request.db.id} created successfully.")
        
    @requires_request
    def _view_request(self, request):
        """View a specific request"""
        header = f"""Request #{request.db.id}: {request.db.title}
Status: {request.db.status}  Category: {request.db.category}
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
        
    @requires_request
    def _add_comment(self, request, text):
        """Add a comment to a request"""
        request.add_comment(self.caller.account.name, text)
        self.caller.msg("Comment added.")
        
    @requires_request
    def _close_request(self, request, resolution):
        """Close a request"""
        request.change_status("Closed", resolution)
        self.caller.msg("Request closed.")
        
    @staff_only
    @requires_request
    def _assign_request(self, request, staff_name):
        """Assign a request to a staff member"""
        staff = AccountDB.objects.filter(username__iexact=staff_name).first()
        if not staff:
            self.caller.msg(f"Staff member '{staff_name}' not found.")
            return
            
        request.assign_to(staff)
        self.caller.msg(f"Request assigned to {staff.name}.")
        
    @staff_only
    @requires_request
    def _change_status(self, request, status):
        """Change request status"""
        try:
            request.change_status(status)
            self.caller.msg(f"Status changed to: {status}")
        except ValueError as e:
            self.caller.msg(str(e))
            
    @staff_only
    @requires_request
    def _change_category(self, request, category):
        """Change request category"""
        request.db.category = category
        request.db.date_modified = datetime.now()
        self.caller.msg(f"Category changed to: {category}")
        
    @staff_only
    @requires_request
    def _archive_request(self, request):
        """Archive a request"""
        if request.is_archived:
            self.caller.msg("This request is already archived.")
            return
            
        request.archive()
        self.caller.msg(f"Request #{request.db.id} has been archived.")
        
    @staff_only
    @requires_request
    def _unarchive_request(self, request):
        """Unarchive a request"""
        if not request.is_archived:
            self.caller.msg("This request is not archived.")
            return
            
        request.unarchive()
        self.caller.msg(f"Request #{request.db.id} has been unarchived.")
        
    @staff_only
    def _cleanup_old_requests(self):
        """Archive old closed requests and delete old archived ones"""
        handler = self.request_handler
        requests = handler.db.requests or []
        
        archived_count = 0
        deleted_count = 0
        
        # Process requests in reverse order since we'll be removing items
        for i in range(len(requests) - 1, -1, -1):
            request = requests[i]
            
            # Check for deletion first
            if request.is_archived and request.should_be_deleted():
                handler.remove_request(request)
                request.delete()
                deleted_count += 1
                continue
                
            # Then check for archiving
            if not request.is_archived and request.should_auto_archive():
                request.archive()
                archived_count += 1
                
        if archived_count or deleted_count:
            self.caller.msg(
                f"Archived {archived_count} old closed request{'s' if archived_count != 1 else ''}. "
                f"Deleted {deleted_count} old archived request{'s' if deleted_count != 1 else ''}."
            )
        else:
            self.caller.msg("No requests needed cleanup.")

    def func(self):
        """Main command function."""
        try:
            if not self.args and not self.switches:
                # No args, no switches - list active requests
                self._list_requests()
                return
                
            if "all" in self.switches:
                # List all requests (staff only)
                if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
                    self.caller.msg("Only staff can view all requests.")
                    return
                self._list_requests(personal=False)
                return
                
            if "archive" in self.switches:
                if len(self.switches) > 1 and "all" in self.switches:
                    # List all archived requests (staff only)
                    if not self.caller.locks.check_lockstring(self.caller, "perm(Admin)"):
                        self.caller.msg("Only staff can view all archived requests.")
                        return
                    self._list_requests(personal=False, show_archived=True)
                elif self.args:
                    # Archive a specific request (staff only)
                    self._archive_request(self.args)
                else:
                    # List personal archived requests
                    self._list_requests(show_archived=True)
                return
                
            if "unarchive" in self.switches:
                # Unarchive a request (staff only)
                self._unarchive_request(self.args)
                return
                
            if "cleanup" in self.switches:
                # Clean up old requests (staff only)
                self._cleanup_old_requests()
                return
                
            if "new" in self.switches:
                # Create a new request
                if not self.rhs:
                    self.caller.msg("Usage: request/new <title>=<text>")
                    return
                self._create_request(self.lhs, self.rhs)
                return
                
            if "comment" in self.switches:
                # Add a comment
                if not self.rhs:
                    self.caller.msg("Usage: request/comment <#>=<text>")
                    return
                self._add_comment(self.lhs, self.rhs)
                return
                
            if "close" in self.switches:
                # Close a request
                if not self.rhs:
                    self.caller.msg("Usage: request/close <#>=<resolution>")
                    return
                self._close_request(self.lhs, self.rhs)
                return
                
            if "assign" in self.switches:
                # Assign to staff
                if not self.rhs:
                    self.caller.msg("Usage: request/assign <#>=<staff>")
                    return
                self._assign_request(self.lhs, self.rhs)
                return
                
            if "status" in self.switches:
                # Change status
                if not self.rhs:
                    self.caller.msg("Usage: request/status <#>=<status>")
                    return
                self._change_status(self.lhs, self.rhs)
                return
                
            if "cat" in self.switches:
                # Change category
                if not self.rhs:
                    self.caller.msg("Usage: request/cat <#>=<category>")
                    return
                self._change_category(self.lhs, self.rhs)
                return
                
            # No switches but has args - view specific request
            self._view_request(self.args)
        except Exception as e:
            # Log the error but give a friendly message to the user
            self.caller.msg("An error occurred while processing your request. Please try again or contact an admin if the problem persists.")
            self.logger.log_trace()

class RequestCmdSet(CmdSet):
    """
    Command set for the request system.
    """
    
    key = "request_commands"
    
    def at_cmdset_creation(self):
        """Add commands to the command set"""
        self.add(CmdRequest()) 