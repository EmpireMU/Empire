"""
Tests for character sheet functionality.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.charsheet import CmdSheet, get_trait_display, format_trait_section
from utils.trait_definitions import ATTRIBUTES, SKILLS, DISTINCTIONS

class TestCharSheet(EvenniaTest):
    """Test cases for character sheet functionality."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        self.cmd = CmdSheet()
        self.cmd.caller = self.char1
        self.cmd.obj = self.char1
        
        # Mock trait handlers
        self.char1.traits = MagicMock()
        self.char1.character_attributes = MagicMock()
        self.char1.skills = MagicMock()
        self.char1.distinctions = MagicMock()
        self.char1.signature_assets = MagicMock()
        self.char1.char_resources = MagicMock()
        
        # Set up test traits
        self.setup_test_traits()
    
    def setup_test_traits(self):
        """Set up test traits on the character."""
        # Mock trait objects
        class MockTrait:
            def __init__(self, key, name, value, desc=""):
                self.key = key
                self.name = name
                self.value = value
                self.desc = desc
                self.base = value
        
        # Set up plot points
        plot_points = MockTrait("plot_points", "Plot Points", 1)
        self.char1.traits.get.return_value = plot_points
        
        # Set up attributes
        self.attributes = {
            "prowess": MockTrait("prowess", "Prowess", 8, "Physical power"),
            "finesse": MockTrait("finesse", "Finesse", 6, "Agility")
        }
        self.char1.character_attributes.all.return_value = list(self.attributes.keys())
        self.char1.character_attributes.get.side_effect = lambda x: self.attributes.get(x)
        
        # Set up skills
        self.skills = {
            "fighting": MockTrait("fighting", "Fighting", 8, "Combat ability"),
            "stealth": MockTrait("stealth", "Stealth", 6, "Moving quietly")
        }
        self.char1.skills.all.return_value = list(self.skills.keys())
        self.char1.skills.get.side_effect = lambda x: self.skills.get(x)
        
        # Set up distinctions
        self.distinctions = {
            "warrior": MockTrait("warrior", "Warrior", 8, "Born fighter")
        }
        self.char1.distinctions.all.return_value = list(self.distinctions.keys())
        self.char1.distinctions.get.side_effect = lambda x: self.distinctions.get(x)
        
        # Set up signature assets
        self.assets = {
            "sword": MockTrait("sword", "Magic Sword", 6, "Ancient blade")
        }
        self.char1.signature_assets.all.return_value = list(self.assets.keys())
        self.char1.signature_assets.get.side_effect = lambda x: self.assets.get(x)
        
        # Set up resources
        self.resources = {
            "gold": MockTrait("gold", "Gold", 6, "Wealth")
        }
        self.char1.char_resources.all.return_value = list(self.resources.keys())
        self.char1.char_resources.get.side_effect = lambda x: self.resources.get(x)
    
    def test_get_trait_display(self):
        """Test trait display formatting."""
        # Test normal trait
        trait = self.attributes["prowess"]
        name, die, desc = get_trait_display(trait)
        self.assertEqual(name, "Prowess")
        self.assertEqual(die, "d8")
        self.assertEqual(desc, "Physical power")
        
        # Test trait without name (falls back to key)
        trait = MagicMock(key="test", value=6)
        del trait.name
        name, die, desc = get_trait_display(trait)
        self.assertEqual(name, "test")
        self.assertEqual(die, "d6")
        
        # Test trait without description
        trait = MagicMock(key="test", name="Test", value=6)
        del trait.desc
        name, die, desc = get_trait_display(trait)
        self.assertEqual(desc, "")
        
        # Test None trait
        name, die, desc = get_trait_display(None)
        self.assertEqual(name, "")
        self.assertEqual(die, "")
        self.assertEqual(desc, "")
    
    def test_format_trait_section(self):
        """Test trait section formatting."""
        # Test attributes section
        attributes = [self.attributes["prowess"], self.attributes["finesse"]]
        section = format_trait_section("Attributes", attributes)
        self.assertIn("Attributes", section)
        self.assertIn("Prowess", section)
        self.assertIn("d8", section)
        self.assertIn("Finesse", section)
        self.assertIn("d6", section)
        
        # Test resources section with descriptions
        resources = [self.resources["gold"]]
        section = format_trait_section("Resources", resources, show_desc=True)
        self.assertIn("Resources", section)
        self.assertIn("Gold", section)
        self.assertIn("d6", section)
        self.assertIn("Wealth", section)
        
        # Test empty section
        section = format_trait_section("Empty", [])
        self.assertEqual(section, "")
    
    def test_view_own_sheet(self):
        """Test viewing own character sheet."""
        # Call command with no args (view own sheet)
        self.cmd.args = ""
        self.cmd.func()
        
        # Check output contains all sections
        output = self.caller.msg.mock_calls[0][1][0]
        self.assertIn("Character Sheet", output)
        self.assertIn("Plot Points", output)
        self.assertIn("Prime Sets", output)
        self.assertIn("Additional Sets", output)
        
        # Check specific traits
        self.assertIn("Prowess", output)
        self.assertIn("d8", output)
        self.assertIn("Fighting", output)
        self.assertIn("Warrior", output)
        self.assertIn("Magic Sword", output)
        self.assertIn("Gold", output)
    
    def test_view_other_sheet(self):
        """Test viewing another character's sheet."""
        # Create another character
        other_char = self.char2
        
        # Set up mock traits on other character
        other_char.traits = MagicMock()
        other_char.character_attributes = MagicMock()
        other_char.skills = MagicMock()
        other_char.distinctions = MagicMock()
        
        # Try viewing without permission
        self.cmd.args = other_char.name
        self.cmd.func()
        self.assertIn("can only view your own", self.caller.msg.mock_calls[0][1][0])
        
        # Give permission and try again
        self.cmd.caller.permissions.add("Admin")
        self.cmd.func()
        # Should succeed but show empty sheet since we didn't mock traits
        self.assertIn("has no character sheet", self.caller.msg.mock_calls[1][1][0])
    
    def test_invalid_sheet_access(self):
        """Test invalid character sheet access."""
        # Try viewing non-existent character
        self.cmd.caller.permissions.add("Admin")
        self.cmd.args = "nonexistent"
        self.cmd.func()
        self.assertIn("Nothing found", self.caller.msg.mock_calls[0][1][0])
        
        # Try viewing object without traits
        obj = self.obj1
        self.cmd.args = obj.name
        self.cmd.func()
        self.assertIn("has no character sheet", self.caller.msg.mock_calls[1][1][0])

if __name__ == '__main__':
    unittest.main() 