"""
Tests for character sheet editor functionality.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.charsheet_editor import (
    CmdSetTrait,
    CmdDelTrait,
    CmdSetDistinction,
    CmdBiography,
    CmdBackground,
    CmdPersonality
)

class TestCharSheetEditor(EvenniaTest):
    """Test cases for character sheet editor functionality."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        
        # Set up commands
        self.cmd_settrait = CmdSetTrait()
        self.cmd_deltrait = CmdDelTrait()
        self.cmd_setdist = CmdSetDistinction()
        self.cmd_bio = CmdBiography()
        self.cmd_bg = CmdBackground()
        self.cmd_pers = CmdPersonality()
        
        # Set caller for all commands
        for cmd in [self.cmd_settrait, self.cmd_deltrait, self.cmd_setdist,
                   self.cmd_bio, self.cmd_bg, self.cmd_pers]:
            cmd.caller = self.char1
            cmd.obj = self.char1
        
        # Set up character trait handlers
        self.char1.traits = MagicMock()
        self.char1.character_attributes = MagicMock()
        self.char1.skills = MagicMock()
        self.char1.distinctions = MagicMock()
        self.char1.signature_assets = MagicMock()
        
        # Set up permissions
        self.char1.permissions.add("Admin")
    
    def test_set_trait(self):
        """Test setting traits."""
        # Test setting an attribute
        self.cmd_settrait.args = "self = attributes strength d8 Strong and tough"
        self.cmd_settrait.func()
        self.char1.character_attributes.add.assert_called_with(
            "strength", value=8, name="strength", description="Strong and tough"
        )
        
        # Test setting a skill
        self.cmd_settrait.args = "self = skills fighting d6 Combat training"
        self.cmd_settrait.func()
        self.char1.skills.add.assert_called_with(
            "fighting", value=6, name="fighting", description="Combat training"
        )
        
        # Test setting a signature asset
        self.cmd_settrait.args = "self = signature_assets sword d8 Magic blade"
        self.cmd_settrait.func()
        self.char1.signature_assets.add.assert_called_with(
            "sword", value=8, name="sword", description="Magic blade"
        )
        
        # Test invalid category
        self.cmd_settrait.args = "self = invalid strength d8"
        self.cmd_settrait.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("Invalid category", output)
        
        # Test invalid die size
        self.cmd_settrait.args = "self = attributes strength d7"
        self.cmd_settrait.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("Die size must be", output)
    
    def test_delete_trait(self):
        """Test deleting traits."""
        # Test deleting an attribute
        self.cmd_deltrait.args = "self = attributes strength"
        self.cmd_deltrait.func()
        self.char1.character_attributes.remove.assert_called_with("strength")
        
        # Test deleting a skill
        self.cmd_deltrait.args = "self = skills fighting"
        self.cmd_deltrait.func()
        self.char1.skills.remove.assert_called_with("fighting")
        
        # Test deleting a signature asset
        self.cmd_deltrait.args = "self = signature_assets sword"
        self.cmd_deltrait.func()
        self.char1.signature_assets.remove.assert_called_with("sword")
        
        # Test invalid category
        self.cmd_deltrait.args = "self = invalid strength"
        self.cmd_deltrait.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("Invalid category", output)
    
    def test_set_distinction(self):
        """Test setting distinctions."""
        # Test setting concept distinction
        self.cmd_setdist.args = "self = concept : Bold Explorer : Always seeking adventure"
        self.cmd_setdist.func()
        self.char1.distinctions.add.assert_called_with(
            "concept", value=8, desc="Always seeking adventure", name="Bold Explorer"
        )
        
        # Test setting culture distinction
        self.cmd_setdist.args = "self = culture : Islander : Born on the seas"
        self.cmd_setdist.func()
        self.char1.distinctions.add.assert_called_with(
            "culture", value=8, desc="Born on the seas", name="Islander"
        )
        
        # Test invalid slot
        self.cmd_setdist.args = "self = invalid : Test : Description"
        self.cmd_setdist.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("Invalid distinction slot", output)
    
    def test_biography(self):
        """Test biography command."""
        # Set up test data
        self.char1.db.background = "Test background"
        self.char1.db.personality = "Test personality"
        self.char1.get_display_desc = MagicMock(return_value="Test description")
        
        # Test viewing own biography
        self.cmd_bio.args = ""
        self.cmd_bio.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("Test background", output)
        self.assertIn("Test personality", output)
        self.assertIn("Test description", output)
        
        # Test viewing other's biography
        self.cmd_bio.args = "self"
        self.cmd_bio.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("Test background", output)
        self.assertIn("Test personality", output)
        self.assertIn("Test description", output)
    
    def test_background(self):
        """Test background command."""
        # Test viewing background
        self.char1.db.background = "Test background"
        self.cmd_bg.args = ""
        self.cmd_bg.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("Test background", output)
        
        # Test setting background
        self.cmd_bg.args = "self = New background"
        self.cmd_bg.func()
        self.assertEqual(self.char1.db.background, "New background")
        
        # Test setting without permission
        self.char1.permissions.remove("Admin")
        self.cmd_bg.args = "self = Another background"
        self.cmd_bg.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("don't have permission", output)
    
    def test_personality(self):
        """Test personality command."""
        # Test viewing personality
        self.char1.db.personality = "Test personality"
        self.cmd_pers.args = ""
        self.cmd_pers.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("Test personality", output)
        
        # Test setting personality
        self.cmd_pers.args = "self = New personality"
        self.cmd_pers.func()
        self.assertEqual(self.char1.db.personality, "New personality")
        
        # Test setting without permission
        self.char1.permissions.remove("Admin")
        self.cmd_pers.args = "self = Another personality"
        self.cmd_pers.func()
        output = self.caller.msg.mock_calls[-1][1][0]
        self.assertIn("don't have permission", output)

if __name__ == '__main__':
    unittest.main() 