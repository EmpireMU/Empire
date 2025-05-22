"""
Tests for character sheet editor functionality.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.charsheet_editor import (
    CmdSetTrait,
    CmdDeleteTrait,
    CmdSetDistinction,
    CmdBiography,
    CmdBackground,
    CmdPersonality
)
from evennia.contrib.rpg.traits import TraitHandler

class TestCharSheetEditor(EvenniaTest):
    """Test cases for character sheet editor functionality."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        
        # Initialize trait handlers
        if not hasattr(self.char1, 'char_attributes'):
            self.char1.char_attributes = TraitHandler(self.char1, db_attribute_key="char_attributes")
        if not hasattr(self.char1, 'skills'):
            self.char1.skills = TraitHandler(self.char1, db_attribute_key="skills")
        if not hasattr(self.char1, 'distinctions'):
            self.char1.distinctions = TraitHandler(self.char1, db_attribute_key="char_distinctions")
        if not hasattr(self.char1, 'signature_assets'):
            self.char1.signature_assets = TraitHandler(self.char1, db_attribute_key="char_signature_assets")
        
        # Set up test commands
        self.cmd_settrait = CmdSetTrait()
        self.cmd_settrait.caller = self.char1
        self.cmd_settrait.obj = self.char1
        self.cmd_settrait.msg = MagicMock()

        self.cmd_deltrait = CmdDeleteTrait()
        self.cmd_deltrait.caller = self.char1
        self.cmd_deltrait.obj = self.char1
        self.cmd_deltrait.msg = MagicMock()
        
        # Set up additional commands
        self.cmd_setdist = CmdSetDistinction()
        self.cmd_setdist.caller = self.char1
        self.cmd_setdist.obj = self.char1
        self.cmd_setdist.msg = MagicMock()
        
        self.cmd_bio = CmdBiography()
        self.cmd_bio.caller = self.char1
        self.cmd_bio.obj = self.char1
        self.cmd_bio.msg = MagicMock()
        
        self.cmd_bg = CmdBackground()
        self.cmd_bg.caller = self.char1
        self.cmd_bg.obj = self.char1
        self.cmd_bg.msg = MagicMock()
        
        self.cmd_pers = CmdPersonality()
        self.cmd_pers.caller = self.char1
        self.cmd_pers.obj = self.char1
        self.cmd_pers.msg = MagicMock()
        
        # Set up permissions
        self.char1.permissions.add("Admin")
    
    def test_set_trait(self):
        """Test setting traits."""
        # Test setting an attribute
        self.cmd_settrait.args = "self = attributes strength d8 Strong and tough"
        self.cmd_settrait.func()
        trait = self.char1.char_attributes.get("strength")
        self.assertIsNotNone(trait)
        self.assertEqual(int(trait.base), 8)
        self.assertEqual(trait.desc, "Strong and tough")
        
        # Test setting a skill
        self.cmd_settrait.args = "self = skills fighting d6 Combat training"
        self.cmd_settrait.func()
        trait = self.char1.skills.get("fighting")
        self.assertIsNotNone(trait)
        self.assertEqual(int(trait.base), 6)
        self.assertEqual(trait.desc, "Combat training")
        
        # Test setting a signature asset
        self.cmd_settrait.args = "self = signature_assets sword d8 Magic blade"
        self.cmd_settrait.func()
        trait = self.char1.signature_assets.get("sword")
        self.assertIsNotNone(trait)
        self.assertEqual(int(trait.base), 8)
        self.assertEqual(trait.desc, "Magic blade")
        
        # Test invalid category
        self.cmd_settrait.args = "self = invalid strength d8"
        self.cmd_settrait.func()
        self.assertIn("Invalid category", self.cmd_settrait.msg.mock_calls[-1][1][0])
        
        # Test invalid die size
        self.cmd_settrait.args = "self = attributes strength d7"
        self.cmd_settrait.func()
        self.assertIn("Die size must be", self.cmd_settrait.msg.mock_calls[-1][1][0])
    
    def test_delete_trait(self):
        """Test deleting traits."""
        # Add some traits to delete
        self.char1.char_attributes.add("strength", trait_type="static", base=8)
        self.char1.skills.add("fighting", trait_type="static", base=6)
        self.char1.signature_assets.add("sword", trait_type="static", base=8)
        
        # Test deleting an attribute
        self.cmd_deltrait.args = "self = attributes strength"
        self.cmd_deltrait.func()
        self.assertIsNone(self.char1.char_attributes.get("strength"))
        
        # Test deleting a skill
        self.cmd_deltrait.args = "self = skills fighting"
        self.cmd_deltrait.func()
        self.assertIsNone(self.char1.skills.get("fighting"))
        
        # Test deleting a signature asset
        self.cmd_deltrait.args = "self = signature_assets sword"
        self.cmd_deltrait.func()
        self.assertIsNone(self.char1.signature_assets.get("sword"))
        
        # Test invalid category
        self.cmd_deltrait.args = "self = invalid strength"
        self.cmd_deltrait.func()
        self.assertIn("Invalid category", self.cmd_deltrait.msg.mock_calls[-1][1][0])
    
    def test_set_distinction(self):
        """Test setting distinctions."""
        # Test setting concept distinction
        self.cmd_setdist.args = "self = concept : Bold Explorer : Always seeking adventure"
        self.cmd_setdist.func()
        trait = self.char1.distinctions.get("concept")
        self.assertIsNotNone(trait)
        self.assertEqual(int(trait.base), 8)  # All distinctions are d8
        self.assertEqual(trait.desc, "Always seeking adventure")
        self.assertEqual(trait.name, "Bold Explorer")
        
        # Test setting culture distinction
        self.cmd_setdist.args = "self = culture : Islander : Born on the seas"
        self.cmd_setdist.func()
        trait = self.char1.distinctions.get("culture")
        self.assertIsNotNone(trait)
        self.assertEqual(int(trait.base), 8)  # All distinctions are d8
        self.assertEqual(trait.desc, "Born on the seas")
        self.assertEqual(trait.name, "Islander")
        
        # Test invalid slot
        self.cmd_setdist.args = "self = invalid : Test : Description"
        self.cmd_setdist.func()
        self.assertIn("Invalid distinction slot", self.cmd_setdist.msg.mock_calls[-1][1][0])
    
    def test_biography(self):
        """Test biography command."""
        # Set up test data
        self.char1.db.background = "Test background"
        self.char1.db.personality = "Test personality"
        self.char1.get_display_desc = MagicMock(return_value="Test description")
        
        # Test viewing own biography
        self.cmd_bio.args = ""
        self.cmd_bio.func()
        self.assertIn("Test background", self.cmd_bio.msg.mock_calls[-1][1][0])
        self.assertIn("Test personality", self.cmd_bio.msg.mock_calls[-1][1][0])
        self.assertIn("Test description", self.cmd_bio.msg.mock_calls[-1][1][0])
        
        # Test viewing other's biography
        self.cmd_bio.args = "self"
        self.cmd_bio.func()
        self.assertIn("Test background", self.cmd_bio.msg.mock_calls[-1][1][0])
        self.assertIn("Test personality", self.cmd_bio.msg.mock_calls[-1][1][0])
        self.assertIn("Test description", self.cmd_bio.msg.mock_calls[-1][1][0])
    
    def test_background(self):
        """Test background command."""
        # Test viewing background
        self.char1.db.background = "Test background"
        self.cmd_bg.args = ""
        self.cmd_bg.func()
        self.assertIn("Test background", self.cmd_bg.msg.mock_calls[-1][1][0])
        
        # Test setting background with permission
        self.cmd_bg.args = "self = New background"
        self.cmd_bg.func()
        self.assertEqual(self.char1.db.background, "New background")
        
        # Test setting without permission
        self.char1.permissions.clear()  # Remove all permissions
        self.cmd_bg.args = "self = Another background"
        self.cmd_bg.func()
        self.assertIn("don't have permission", self.cmd_bg.msg.mock_calls[-1][1][0])
    
    def test_personality(self):
        """Test personality command."""
        # Test viewing personality
        self.char1.db.personality = "Test personality"
        self.cmd_pers.args = ""
        self.cmd_pers.func()
        self.assertIn("Test personality", self.cmd_pers.msg.mock_calls[-1][1][0])
        
        # Test setting personality with permission
        self.cmd_pers.args = "self = New personality"
        self.cmd_pers.func()
        self.assertEqual(self.char1.db.personality, "New personality")
        
        # Test setting without permission
        self.char1.permissions.clear()  # Remove all permissions
        self.cmd_pers.args = "self = Another personality"
        self.cmd_pers.func()
        self.assertIn("don't have permission", self.cmd_pers.msg.mock_calls[-1][1][0])

if __name__ == '__main__':
    unittest.main() 