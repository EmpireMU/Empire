"""
Tests for the organization system.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.organisations import CmdOrg, CmdResource
from typeclasses.organisations import Organisation
from evennia import create_object
from utils.org_utils import validate_rank, parse_equals, parse_comma, get_org, get_char, get_org_and_char

class TestOrganisation(EvenniaTest):
    """Test cases for organization functionality."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        
        # Set up command
        self.cmd = CmdOrg()
        self.cmd.caller = self.char1
        self.cmd.obj = self.char1
        
        # Set up message mocking
        self.caller = self.char1
        self.caller.msg = MagicMock()
        self.cmd.msg = self.caller.msg
        
        # Create a test organization
        self.org = create_object(
            typeclass=Organisation,
            key="Test House"
        )
        self.org.db.description = "A test noble house"
        self.org.db.members = {}  # Initialize empty members dict
        self.org.db.rank_names = {  # Initialize rank names
            1: "Head of House",      
            2: "Minister",        
            3: "Noble Family",       
            4: "Senior Servant",        
            5: "Servant",         
            6: "Junior Servant",        
            7: "Affiliate",   
            8: "Extended Family",      
            9: "",       
            10: ""     
        }
        
        # Initialize command properties
        self.cmd.args = ""
        self.cmd.switches = []
        self.cmd.lhs = ""
        self.cmd.rhs = ""
        
        # Give admin permissions for staff-only actions
        self.caller.permissions.add("Admin")
        
        # Add helper methods to command
        self.cmd._validate_rank = lambda rank_str, default=None: validate_rank(rank_str, default, self.caller)
        self.cmd._parse_equals = lambda usage_msg: parse_equals(self.cmd.args, usage_msg, self.caller)
        self.cmd._parse_comma = lambda text, expected_parts=2, usage_msg=None: parse_comma(text, expected_parts, usage_msg, self.caller)
        self.cmd._get_org = lambda org_name: get_org(org_name, self.caller)
        self.cmd._get_character = lambda char_name: get_char(char_name, self.caller)
        self.cmd._get_org_and_char = lambda org_name, char_name: get_org_and_char(org_name, char_name, self.caller)
        
    def test_org_creation(self):
        """Test creating a new organization."""
        # Set up command arguments
        self.cmd.switches = ["create"]
        self.cmd.args = "New House"
        
        # Run the command
        self.cmd.func()
        
        # Verify organization was created
        orgs = Organisation.objects.filter(db_key="New House")
        self.assertTrue(len(orgs) > 0)
        
        # Get the created organization
        org = orgs[0]
        
        # Verify organization properties
        self.assertEqual(org.db.description, "No description set.")
        self.assertEqual(len(org.db.rank_names), 10)  # Should have 10 ranks
        self.assertEqual(len(org.db.members), 0)  # Should start with no members
        
    def test_member_management(self):
        """Test adding, updating, and removing members."""
        # Test adding a member
        self.cmd.switches = ["member"]
        self.cmd.args = f"Test House={self.char1.name},5"  # Add as rank 5
        self.cmd.func()
        
        # Verify member was added
        self.assertIn(self.char1.id, self.org.db.members)
        self.assertEqual(self.org.get_member_rank(self.char1), 5)
        
        # Test updating member's rank
        self.cmd.args = f"Test House={self.char1.name},3"  # Promote to rank 3
        self.cmd.func()
        
        # Verify rank was updated
        self.assertEqual(self.org.get_member_rank(self.char1), 3)
        
        # Test removing a member
        self.cmd.switches = ["remove"]
        self.cmd.args = f"Test House={self.char1.name}"
        self.cmd.func()
        
        # Verify member was removed
        self.assertNotIn(self.char1.id, self.org.db.members)
        
    def test_rank_names(self):
        """Test setting and getting rank names."""
        # Test setting a rank name
        self.cmd.switches = ["rankname"]
        self.cmd.args = "Test House=5,Knight"  # Changed format to match command
        self.cmd.func()
        
        # Verify rank name was set
        self.assertEqual(self.org.db.rank_names[5], "Knight")
        
        # Test invalid rank number
        self.cmd.args = "Test House=11,Invalid"  # Rank 11 doesn't exist
        self.cmd.func()
        
        # Verify rank name wasn't set
        self.assertNotIn(11, self.org.db.rank_names)
        
    def test_permissions(self):
        """Test permission checks."""
        # Remove admin permissions
        self.caller.permissions.remove("Admin")
        
        # Try to create an organization
        self.cmd.switches = ["create"]
        self.cmd.args = "New House"
        self.cmd.func()
        
        # Verify organization wasn't created
        orgs = Organisation.objects.filter(db_key="New House")
        self.assertEqual(len(orgs), 0)
        
        # Try to delete an organization
        self.cmd.switches = ["delete"]
        self.cmd.args = "Test House"
        self.cmd.func()
        
        # Verify organization wasn't deleted
        self.assertIsNotNone(self.org.pk)
        
    def test_viewing(self):
        """Test viewing organization information."""
        # Add a member for testing
        self.org.add_member(self.char1, 3)
        
        # View organization info
        self.cmd.switches = []
        self.cmd.args = "Test House"
        self.cmd.func()
        
        # Verify output was sent
        self.assertTrue(self.caller.msg.called)
        
    def test_deletion(self):
        """Test deleting an organization."""
        # Add a member for testing cleanup
        self.org.add_member(self.char1, 3)
        
        # Delete the organization
        self.cmd.switches = ["delete"]
        self.cmd.args = "Test House"
        self.cmd.func()
        
        # First call should ask for confirmation
        self.assertTrue(self.caller.db.delete_org_confirming)
        
        # Second call should delete
        self.cmd.func()
        
        # Verify organization was deleted
        self.assertFalse(Organisation.objects.filter(db_key="Test House").exists())


class TestResource(EvenniaTest):
    """Test cases for organization resources."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        
        # Set up command
        self.cmd = CmdResource()
        self.cmd.caller = self.char1
        self.cmd.obj = self.char1
        
        # Set up message mocking
        self.caller = self.char1
        self.caller.msg = MagicMock()
        self.cmd.msg = self.caller.msg
        
        # Create a test organization
        self.org = create_object(
            typeclass=Organisation,
            key="Test House"
        )
        self.org.db.description = "A test noble house"
        self.org.db.members = {}  # Initialize empty members dict
        self.org.db.rank_names = {  # Initialize rank names
            1: "Head of House",      
            2: "Minister",        
            3: "Noble Family",       
            4: "Senior Servant",        
            5: "Servant",         
            6: "Junior Servant",        
            7: "Affiliate",   
            8: "Extended Family",      
            9: "",       
            10: ""     
        }
        
        # Initialize command properties
        self.cmd.args = ""
        self.cmd.switches = []
        self.cmd.lhs = ""
        self.cmd.rhs = ""
        
        # Give admin permissions for staff-only actions
        self.caller.permissions.add("Admin")
        
        # Add helper methods to command
        self.cmd._parse_equals = lambda usage_msg: parse_equals(self.cmd.args, usage_msg, self.caller)
        self.cmd._parse_comma = lambda text, expected_parts=2, usage_msg=None: parse_comma(text, expected_parts, usage_msg, self.caller)
        self.cmd._get_org = lambda org_name: get_org(org_name, self.caller)
        self.cmd._get_char = lambda char_name: get_char(char_name, self.caller, check_resources=True)
        
    def test_resource_creation(self):
        """Test creating organization resources."""
        # Create a resource
        self.cmd.switches = ["org"]
        self.cmd.args = "Test House,armory=8"
        self.cmd.func()
        
        # Verify resource was created
        self.assertIsNotNone(self.org.org_resources.get("armory"))
        self.assertEqual(self.org.org_resources.get("armory").value, 8)
        
    def test_resource_transfer(self):
        """Test transferring resources."""
        # Create a resource first
        self.org.add_org_resource("gold", 6)
        
        # Transfer to a character
        self.cmd.switches = ["transfer"]
        self.cmd.args = f"Test House:gold={self.char1.name}"
        self.cmd.func()
        
        # Verify resource was transferred
        self.assertIsNone(self.org.org_resources.get("gold"))
        self.assertIsNotNone(self.char1.char_resources.get("gold"))
        
    def test_resource_deletion(self):
        """Test deleting resources."""
        # Create a resource first
        self.org.add_org_resource("armory", 8)
        
        # Delete the resource
        self.cmd.switches = ["delete"]
        self.cmd.args = "Test House,armory"
        self.cmd.func()
        
        # Verify resource was deleted
        self.assertIsNone(self.org.org_resources.get("armory"))
        
    def test_resource_permissions(self):
        """Test resource permission checks."""
        # Create a resource first
        self.org.add_org_resource("armory", 8)
        
        # Remove admin permissions
        self.caller.permissions.remove("Admin")
        
        # Try to create a resource
        self.cmd.switches = ["org"]
        self.cmd.args = "Test House,armory=8"
        self.cmd.func()
        
        # Verify resource wasn't created
        self.assertIsNone(self.org.org_resources.get("armory"))
        
    def test_resource_listing(self):
        """Test listing resources."""
        # Create some resources
        self.org.add_org_resource("armory", 8)
        self.org.add_org_resource("treasury", 6)
        
        # List resources
        self.cmd.switches = []
        self.cmd.args = ""
        self.cmd.func()
        
        # Verify output was sent
        self.assertTrue(self.caller.msg.called) 