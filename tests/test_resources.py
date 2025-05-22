"""
Tests for resource system functionality.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.organisations import CmdResource
from utils.resource_utils import get_unique_resource_name, validate_resource_owner
from utils.org_utils import get_org, get_char
from typeclasses.characters import Character
from typeclasses.organisations import Organisation
from evennia.contrib.rpg.traits import TraitHandler
from evennia import create_object

class TestResources(EvenniaTest):
    """Test cases for resource system functionality."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        self.cmd = CmdResource()
        self.cmd.caller = self.char1
        self.cmd.obj = self.char1
        
        # Set up message mocking
        self.caller = self.char1
        self.caller.msg = MagicMock()
        self.cmd.msg = self.caller.msg
        
        # Set up command attributes
        self.cmd.switches = []
        
        # Initialize trait handlers properly
        if not hasattr(self.char1, 'char_resources'):
            self.char1.char_resources = TraitHandler(self.char1, db_attribute_key="char_resources")
        
        # Create and set up an organization
        self.org = self.create_organisation()
        
        # Set up test resources
        self.setup_char_resources()
        
        # Set up permissions
        self.cmd.caller.permissions.add("Admin")
    
    def create_organisation(self):
        """Create a test organization."""
        org = create_object(Organisation, key="Test Org")
        if not hasattr(org, 'org_resources'):
            org.org_resources = TraitHandler(org, db_attribute_key="org_resources")
        
        # Add org resources
        org.org_resources.add("armory", "Armory", trait_type="static", base=8)
        org.org_resources.add("treasury", "Treasury", trait_type="static", base=6)
        
        return org
    
    def setup_char_resources(self):
        """Set up character resources."""
        # Add character resources
        self.char1.char_resources.add("gold", "Gold", trait_type="static", base=6)
        self.char1.char_resources.add("supplies", "Supplies", trait_type="static", base=4)
    
    def test_list_resources(self):
        """Test listing resources."""
        # Test listing character resources
        self.cmd.args = ""
        self.cmd.func()
        output = self.caller.msg.mock_calls[0][1][0]
        self.assertIn("gold", output)
        self.assertIn("d6", output)
        self.assertIn("supplies", output)
        self.assertIn("d4", output)
        
        # Test listing org resources
        self.cmd.args = f"{self.org.name}"
        self.cmd.func()
        output = self.caller.msg.mock_calls[1][1][0]
        self.assertIn("armory", output)
        self.assertIn("d8", output)
        self.assertIn("treasury", output)
        self.assertIn("d6", output)
    
    def test_view_resource(self):
        """Test viewing specific resources."""
        # Test viewing character resource
        self.cmd.args = "gold"
        self.cmd.func()
        output = self.caller.msg.mock_calls[0][1][0]
        self.assertIn("gold", output)
        self.assertIn("d6", output)
        
        # Test viewing non-existent resource
        self.cmd.args = "nonexistent"
        self.cmd.func()
        output = self.caller.msg.mock_calls[1][1][0]
        self.assertIn("No resource found", output)
    
    def test_create_char_resource(self):
        """Test creating character resources."""
        # Test creating valid resource
        self.cmd.args = f"{self.char1.name},weapon=8"
        self.cmd.func()
        output = self.caller.msg.mock_calls[0][1][0]
        self.assertIn("Added resource", output)
        self.assertIn("weapon", output)
        self.assertIn("d8", output)
        
        # Test invalid die size
        self.cmd.args = f"{self.char1.name},weapon=7"
        self.cmd.func()
        output = self.caller.msg.mock_calls[1][1][0]
        self.assertIn("Die size must be", output)
        
        # Test invalid character
        self.cmd.args = "nonexistent,weapon=8"
        self.cmd.func()
        output = self.caller.msg.mock_calls[2][1][0]
        self.assertIn("not found", output)
    
    def test_create_org_resource(self):
        """Test creating organization resources."""
        # Test creating valid resource
        self.cmd.args = f"{self.org.name},barracks=8"
        self.cmd.func()
        output = self.caller.msg.mock_calls[0][1][0]
        self.assertIn("Added resource", output)
        self.assertIn("barracks", output)
        self.assertIn("d8", output)
        
        # Test invalid die size
        self.cmd.args = f"{self.org.name},barracks=7"
        self.cmd.func()
        output = self.caller.msg.mock_calls[1][1][0]
        self.assertIn("Die size must be", output)
        
        # Test invalid organization
        self.cmd.args = "nonexistent,barracks=8"
        self.cmd.func()
        output = self.caller.msg.mock_calls[2][1][0]
        self.assertIn("not found", output)
    
    def test_transfer_resource(self):
        """Test transferring resources."""
        # Set up char2 resources
        if not hasattr(self.char2, 'char_resources'):
            self.char2.char_resources = TraitHandler(self.char2, db_attribute_key="char_resources")
        
        # Test char to char transfer
        self.cmd.args = f"{self.char1.name}:gold={self.char2.name}"
        self.cmd.func()
        output = self.caller.msg.mock_calls[0][1][0]
        self.assertIn("Transferred", output)
        
        # Test char to org transfer
        self.cmd.args = f"{self.char1.name}:supplies={self.org.name}"
        self.cmd.func()
        output = self.caller.msg.mock_calls[1][1][0]
        self.assertIn("Transferred", output)
        
        # Test org to char transfer
        self.cmd.args = f"{self.org.name}:armory={self.char1.name}"
        self.cmd.func()
        output = self.caller.msg.mock_calls[2][1][0]
        self.assertIn("Transferred", output)
        
        # Test invalid source
        self.cmd.args = "nonexistent:gold=target"
        self.cmd.func()
        output = self.caller.msg.mock_calls[3][1][0]
        self.assertIn("not found", output)
        
        # Test invalid target
        self.cmd.args = f"{self.char1.name}:gold=nonexistent"
        self.cmd.func()
        output = self.caller.msg.mock_calls[4][1][0]
        self.assertIn("not found", output)
        
        # Test non-existent resource
        self.cmd.args = f"{self.char1.name}:nonexistent={self.char2.name}"
        self.cmd.func()
        output = self.caller.msg.mock_calls[5][1][0]
        self.assertIn("not found", output)
    
    def test_delete_resource(self):
        """Test deleting resources."""
        # Test deleting character resource
        self.cmd.args = "gold"
        self.cmd.func()
        output = self.caller.msg.mock_calls[0][1][0]
        self.assertIn("Deleted resource", output)
        
        # Test deleting non-existent resource
        self.cmd.args = "nonexistent"
        self.cmd.func()
        output = self.caller.msg.mock_calls[1][1][0]
        self.assertIn("No resource found", output)
    
    def test_resource_utils(self):
        """Test resource utility functions."""
        # Test get_unique_resource_name
        name = get_unique_resource_name("gold", self.char1.char_resources)
        self.assertEqual(name, "gold_2")  # Since "gold" exists
        
        name = get_unique_resource_name("new", self.char1.char_resources)
        self.assertEqual(name, "new")  # New name should be unchanged
        
        # Test validate_resource_owner
        self.assertTrue(validate_resource_owner(self.char1))
        self.assertTrue(validate_resource_owner(self.org))
        
        obj = self.obj1  # Regular object without resources
        self.assertFalse(validate_resource_owner(obj))

if __name__ == '__main__':
    unittest.main() 