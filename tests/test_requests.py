"""
Tests for the request system.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from evennia.scripts.scripts import DefaultScript
from commands.requests import CmdRequest
from typeclasses.requests import Request, VALID_STATUSES, DEFAULT_CATEGORIES
from datetime import datetime, timedelta
from evennia import create_script

class TestRequest(EvenniaTest):
    """Test cases for request functionality."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        
        # Set up command
        self.cmd = CmdRequest()
        self.cmd.caller = self.char1
        self.cmd.obj = self.char1
        
        # Set up message mocking
        self.caller = self.char1
        self.caller.msg = MagicMock()
        self.cmd.msg = self.caller.msg
        
        # Create a test request
        self.request = create_script(
            "typeclasses.requests.Request",
            key=f"Request-1",  # Use consistent key format
            desc="A test request"
        )
        
        # Initialize request properties
        self.request.db.id = 1
        self.request.db.title = "Test Request"
        self.request.db.text = "This is a test request."
        self.request.db.submitter = self.account
        self.request.db.date_created = datetime.now()
        self.request.db.date_modified = datetime.now()
        self.request.db.status = "Open"
        self.request.db.category = "General"
        self.request.db.comments = []
        self.request.db.resolution = ""
        self.request.db.date_closed = None
        self.request.db.date_archived = None
        self.request.db.assigned_to = None
        
        # Initialize command properties
        self.cmd.args = ""
        self.cmd.switches = []
        self.cmd.lhs = ""
        self.cmd.rhs = ""
        
        # Give admin permissions for staff-only actions
        self.caller.permissions.add("Admin")
        
    def test_request_creation(self):
        """Test creating a new request."""
        # Set up command arguments
        self.cmd.switches = ["new"]
        self.cmd.args = "New Request=This is a new request."
        self.cmd.lhs = "New Request"
        self.cmd.rhs = "This is a new request."
        
        # Run the command
        self.cmd.func()
        
        # Verify request was created
        requests = Request.objects.filter(db_key__startswith="Request-")
        self.assertTrue(len(requests) > 0)
        
        # Get the latest request
        request = requests.latest('id')
        
        # Verify request properties
        self.assertEqual(request.db.title, "New Request")
        self.assertEqual(request.db.text, "This is a new request.")
        self.assertEqual(request.db.submitter, self.account)
        self.assertEqual(request.db.status, "Open")
        self.assertEqual(request.db.category, "General")
        
    def test_status_changes(self):
        """Test changing request status."""
        # Set up command arguments
        self.cmd.switches = ["status"]
        self.cmd.args = "1=In Progress"
        self.cmd.lhs = "1"  # Request ID
        self.cmd.rhs = "In Progress"  # New status
        
        # Run the command
        self.cmd.func()
        
        # Verify status change
        request = Request.objects.get(db_key="Request-1")
        self.assertEqual(request.db.status, "In Progress")
        
    def test_comments(self):
        """Test adding and retrieving comments."""
        # Set up command arguments
        self.cmd.switches = ["comment"]
        self.cmd.args = "1=Test comment"
        self.cmd.lhs = "1"  # Request ID
        self.cmd.rhs = "Test comment"
        
        # Run the command
        self.cmd.func()
        
        # Verify comment was added
        request = Request.objects.get(db_key="Request-1")
        self.assertEqual(len(request.db.comments), 1)
        self.assertEqual(request.db.comments[0]["text"], "Test comment")
        self.assertEqual(request.db.comments[0]["author"], self.account)
        
    def test_assignment(self):
        """Test assigning requests."""
        # Set up command arguments
        self.cmd.switches = ["assign"]
        self.cmd.args = f"1={self.account.username}"  # Use username instead of ID
        self.cmd.lhs = "1"  # Request ID
        self.cmd.rhs = self.account.username
        
        # Run the command
        self.cmd.func()
        
        # Verify assignment
        request = Request.objects.get(db_key="Request-1")
        self.assertEqual(request.db.assigned_to, self.account)
        
    def test_archiving(self):
        """Test archiving and unarchiving requests."""
        # Set up command arguments for archiving
        self.cmd.switches = ["archive"]
        self.cmd.args = "1"
        self.cmd.lhs = "1"  # Request ID
        
        # Run archive command
        self.cmd.func()
        
        # Verify request is archived
        request = Request.objects.get(db_key="Request-1")
        self.assertIsNotNone(request.db.date_archived)
        
        # Test unarchiving
        self.cmd.switches = ["unarchive"]
        self.cmd.args = "1"
        self.cmd.lhs = "1"  # Request ID
        self.cmd.func()
        
        # Verify request is unarchived
        request = Request.objects.get(db_key="Request-1")
        self.assertIsNone(request.db.date_archived)
        
    def test_auto_archive(self):
        """Test auto-archiving of old requests."""
        # Set request as old and closed
        old_date = datetime.now() - timedelta(days=31)  # Past auto-archive threshold
        self.request.db.date_modified = old_date
        self.request.db.date_closed = old_date
        self.request.db.status = "Closed"
        
        # Set up cleanup command
        self.cmd.switches = ["cleanup"]
        self.cmd.args = ""
        
        # Run cleanup command
        self.cmd.func()
        
        # Verify request was auto-archived
        request = Request.objects.get(db_key="Request-1")
        self.assertIsNotNone(request.db.date_archived)
        
    def test_permissions(self):
        """Test permission checks."""
        # Create a request owned by another user
        other_request = create_script(
            "typeclasses.requests.Request",
            key="Request-2"
        )
        other_request.db.id = 2
        other_request.db.submitter = self.account2
        other_request.db.status = "Open"
        
        # Remove admin permissions
        self.caller.permissions.remove("Admin")
        
        # Try to close someone else's request
        self.cmd.switches = ["status"]
        self.cmd.args = "2=Closed"
        self.cmd.lhs = "2"  # Request ID
        self.cmd.rhs = "Closed"
        
        # Run the command
        self.cmd.func()
        
        # Verify request was not modified
        request = Request.objects.get(db_key="Request-2")
        self.assertEqual(request.db.status, "Open")  # Status should remain unchanged
        
    def test_viewing(self):
        """Test viewing requests."""
        # Set up command arguments
        self.cmd.switches = []
        self.cmd.args = "1"  # Request ID
        
        # Run the command
        self.cmd.func()
        
        # Verify output was sent to caller
        self.assertTrue(self.caller.msg.called)
        
    def test_categories(self):
        """Test request categories."""
        # Set up command arguments
        self.cmd.switches = ["cat"]
        self.cmd.args = "1=Bug"
        self.cmd.lhs = "1"  # Request ID
        self.cmd.rhs = "Bug"  # New category
        
        # Run the command
        self.cmd.func()
        
        # Verify category change
        request = Request.objects.get(db_key="Request-1")
        self.assertEqual(request.db.category, "Bug")
        
    def test_notifications(self):
        """Test request notifications."""
        # Mock the submitter's msg method
        self.account.msg = MagicMock()
        
        # Test notification on status change
        self.request.set_status("In Progress")
        self.account.msg.assert_called_with("[Request #1] Status changed from Open to In Progress")
        
        # Test notification on comment
        self.request.add_comment(self.account, "Test comment")  # Pass account object
        self.account.msg.assert_called_with("[Request #1] New comment by TestAccount")
        
        # Test offline notifications
        self.account.is_connected = False
        self.request.notify_all("Test notification")
        
        notifications = self.account.db.offline_request_notifications or []
        self.assertIn("[Request #1] Test notification", notifications) 