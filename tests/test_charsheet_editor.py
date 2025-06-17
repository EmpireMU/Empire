"""
Tests for character sheet editor functionality.
"""

import unittest
from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.charsheet_editor import (
    CmdSetTrait,
    CmdDeleteTrait,
    CmdSetDistinction,
    CmdBiography,
    CmdBackground,
    CmdPersonality,
    CmdSetAge,
    CmdSetBirthday,
    CmdSetGender,
    CmdSetSpecialEffects
)
from evennia.contrib.rpg.traits import TraitHandler

class TestCharSheetEditor(EvenniaTest):
    """Test cases for character sheet editor functionality."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        self.cmd_settrait = CmdSetTrait()
        self.cmd_settrait.caller = self.char1
        self.cmd_settrait.obj = self.char1
        self.cmd_settrait.msg = MagicMock()
        
        self.cmd_setdist = CmdSetDistinction()
        self.cmd_setdist.caller = self.char1
        self.cmd_setdist.obj = self.char1
        self.cmd_setdist.msg = MagicMock()
        
        self.cmd_bg = CmdBackground()
        self.cmd_bg.caller = self.char1
        self.cmd_bg.obj = self.char1
        self.cmd_bg.msg = MagicMock()
        
        self.cmd_pers = CmdPersonality()
        self.cmd_pers.caller = self.char1
        self.cmd_pers.obj = self.char1
        self.cmd_pers.msg = MagicMock()
        
        self.cmd_bio = CmdBiography()
        self.cmd_bio.caller = self.char1
        self.cmd_bio.obj = self.char1
        self.cmd_bio.msg = MagicMock()

        self.cmd_age = CmdSetAge()
        self.cmd_age.caller = self.char1
        self.cmd_age.obj = self.char1
        self.cmd_age.msg = MagicMock()

        self.cmd_birthday = CmdSetBirthday()
        self.cmd_birthday.caller = self.char1
        self.cmd_birthday.obj = self.char1
        self.cmd_birthday.msg = MagicMock()

        self.cmd_gender = CmdSetGender()
        self.cmd_gender.caller = self.char1
        self.cmd_gender.obj = self.char1
        self.cmd_gender.msg = MagicMock()
        
        # Initialize trait handlers
        if not hasattr(self.char1, 'character_attributes'):
            self.char1.character_attributes = TraitHandler(self.char1, db_attribute_key="character_attributes")
        if not hasattr(self.char1, 'skills'):
            self.char1.skills = TraitHandler(self.char1, db_attribute_key="skills")
        if not hasattr(self.char1, 'distinctions'):
            self.char1.distinctions = TraitHandler(self.char1, db_attribute_key="char_distinctions")
        if not hasattr(self.char1, 'signature_assets'):
            self.char1.signature_assets = TraitHandler(self.char1, db_attribute_key="char_signature_assets")
        if not hasattr(self.char1, 'powers'):
            self.char1.powers = TraitHandler(self.char1, db_attribute_key="powers")
        
        # Add test traits
        self.char1.character_attributes.add("strength", "Strength", trait_type="static", base=8, desc="Strong and tough")
        self.char1.skills.add("fighting", "Fighting", trait_type="static", base=6, desc="Combat training")
        self.char1.signature_assets.add("sword", "Sword", trait_type="static", base=8, desc="Magic blade")
        self.char1.powers.add("test_power", "Test Power", trait_type="static", base=8, desc="A test power")
        
        # Set up test commands
        self.cmd_deltrait = CmdDeleteTrait()
        self.cmd_deltrait.caller = self.char1
        self.cmd_deltrait.obj = self.char1
        self.cmd_deltrait.msg = MagicMock()
        
        # Set up permissions
        self.char1.permissions.add("Admin")
        self.char1.permissions.add("Builder")
        
        # Set up biography data
        self.char1.db.background = "Test background"
        self.char1.db.personality = "Test personality"
        self.char1.db.age = "25"
        self.char1.db.birthday = "January 1st"
        self.char1.db.gender = "Female"
        self.char1.get_display_desc = MagicMock(return_value="Test description")
    
    def test_set_trait(self):
        """Test setting traits."""
        # Test setting an attribute
        self.cmd_settrait.args = "self = attributes strength d8 Strong and tough"
        self.cmd_settrait.func()
        trait = self.char1.character_attributes.get("strength")
        self.assertIsNotNone(trait)
        self.assertEqual(trait.value, 8)  # Trait values are stored as integers
        self.assertEqual(trait.desc, "Strong and tough")
        
        # Test setting a skill
        self.cmd_settrait.args = "self = skills fighting d6 Combat training"
        self.cmd_settrait.func()
        trait = self.char1.skills.get("fighting")
        self.assertIsNotNone(trait)
        self.assertEqual(trait.value, 6)  # Trait values are stored as integers
        self.assertEqual(trait.desc, "Combat training")
        
        # Test setting a signature asset
        self.cmd_settrait.args = "self = signature_assets sword d8 Magic blade"
        self.cmd_settrait.func()
        trait = self.char1.signature_assets.get("sword")
        self.assertIsNotNone(trait)
        self.assertEqual(trait.value, 8)  # Trait values are stored as integers
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
        # Add some signature assets to delete (these are not protected)
        self.char1.signature_assets.add("test_sword", "Test Sword", trait_type="static", base=8, desc="Magic blade")
        self.char1.signature_assets.add("test_armor", "Test Armor", trait_type="static", base=6, desc="Protective gear")
        
        # Test deleting signature assets (allowed)
        self.cmd_deltrait.args = "self = signature_assets test_sword"
        self.cmd_deltrait.func()
        self.assertIsNone(self.char1.signature_assets.get("test_sword"))
        
        self.cmd_deltrait.args = "self = signature_assets test_armor" 
        self.cmd_deltrait.func()
        self.assertIsNone(self.char1.signature_assets.get("test_armor"))
        
        # Test trying to delete protected attributes (should fail)
        self.char1.character_attributes.add("test_str", "Test Strength", trait_type="static", base=8, desc="Strong and tough")
        self.cmd_deltrait.args = "self = attributes test_str"
        self.cmd_deltrait.func()
        # The trait should still exist since it's protected
        self.assertIsNotNone(self.char1.character_attributes.get("test_str"))
        # Check that the error message was sent
        self.assertIn("Cannot delete", self.cmd_deltrait.msg.mock_calls[-1][1][0])
        
        # Test invalid category
        self.cmd_deltrait.args = "self = invalid test_str"
        self.cmd_deltrait.func()
        self.assertIn("Invalid category", self.cmd_deltrait.msg.mock_calls[-1][1][0])
    def test_biography(self):
        """Test biography command."""
        # Set up test distinctions
        self.char1.distinctions.add("concept", "Bold Explorer", trait_type="static", base=8, desc="Always seeking adventure")
        self.char1.distinctions.add("culture", "Islander", trait_type="static", base=8, desc="Born on the seas")
        self.char1.distinctions.add("vocation", "Merchant", trait_type="static", base=8, desc="Trading across the realms")
        
        # Test viewing own biography
        self.cmd_bio.args = ""
        self.cmd_bio.func()
        output = self.cmd_bio.msg.mock_calls[-1][1][0]
        # Check concept
        self.assertIn("Concept: Bold Explorer", output)
        self.assertIn("Always seeking adventure", output)
        # Check demographics line
        self.assertIn("Gender: Female | Age: 25 | Birthday: January 1st", output)
        # Check culture and vocation line
        self.assertIn("Culture: Islander | Vocation: Merchant", output)
        # Verify descriptions are not shown for culture and vocation
        self.assertNotIn("Born on the seas", output)
        self.assertNotIn("Trading across the realms", output)
        # Check main sections
        self.assertIn("Description:", output)
        self.assertIn("Test description", output)
        self.assertIn("Background:", output)
        self.assertIn("Test background", output)
        self.assertIn("Personality:", output)
        self.assertIn("Test personality", output)
        
        # Test viewing other's biography
        self.cmd_bio.args = "self"
        self.cmd_bio.func()
        output = self.cmd_bio.msg.mock_calls[-1][1][0]
        # Check concept
        self.assertIn("Concept: Bold Explorer", output)
        self.assertIn("Always seeking adventure", output)
        # Check demographics line
        self.assertIn("Gender: Female | Age: 25 | Birthday: January 1st", output)
        # Check culture and vocation line
        self.assertIn("Culture: Islander | Vocation: Merchant", output)
        # Verify descriptions are not shown for culture and vocation
        self.assertNotIn("Born on the seas", output)
        self.assertNotIn("Trading across the realms", output)
        # Check main sections
        self.assertIn("Description:", output)
        self.assertIn("Test description", output)
        self.assertIn("Background:", output)
        self.assertIn("Test background", output)
        self.assertIn("Personality:", output)
        self.assertIn("Test personality", output)
        
        # Test with no demographics set
        self.char1.db.gender = None
        self.char1.db.age = None
        self.char1.db.birthday = None
        self.cmd_bio.func()
        output = self.cmd_bio.msg.mock_calls[-1][1][0]
        self.assertIn("No demographics set", output)
    def test_background(self):
        """Test background command."""
        # Test viewing background
        self.cmd_bg.args = ""
        self.cmd_bg.func()
        self.assertIn("Test background", self.cmd_bg.msg.mock_calls[-1][1][0])
        
        # Test setting background with permission
        self.cmd_bg.args = "self = New background"
        self.cmd_bg.lhs = "self"
        self.cmd_bg.rhs = "New background"
        self.cmd_bg.func()
        self.assertEqual(self.char1.db.background, "New background")
        
        # Test setting without permission - mock the access method
        with unittest.mock.patch.object(self.cmd_bg, 'access', return_value=False):
            self.cmd_bg.args = "self = Another background"
            self.cmd_bg.lhs = "self"
            self.cmd_bg.rhs = "Another background"
            self.cmd_bg.func()
            self.assertIn("You don't have permission to edit backgrounds", self.cmd_bg.msg.mock_calls[-1][1][0])
            # Verify background wasn't changed
            self.assertEqual(self.char1.db.background, "New background")
    def test_personality(self):
        """Test personality command."""
        # Test viewing personality
        self.cmd_pers.args = ""
        self.cmd_pers.func()
        self.assertIn("Test personality", self.cmd_pers.msg.mock_calls[-1][1][0])
        
        # Test setting personality with permission
        self.cmd_pers.args = "self = New personality"
        self.cmd_pers.lhs = "self"
        self.cmd_pers.rhs = "New personality"
        self.cmd_pers.func()
        self.assertEqual(self.char1.db.personality, "New personality")
        
        # Test setting without permission - mock the access method
        with unittest.mock.patch.object(self.cmd_pers, 'access', return_value=False):
            self.cmd_pers.args = "self = Another personality"
            self.cmd_pers.lhs = "self"
            self.cmd_pers.rhs = "Another personality"
            self.cmd_pers.func()
            self.assertIn("You don't have permission to edit personalities", self.cmd_pers.msg.mock_calls[-1][1][0])
            # Verify personality wasn't changed
            self.assertEqual(self.char1.db.personality, "New personality")
    
    def test_set_distinction(self):
        """Test setting distinctions."""
        # Test setting concept distinction
        self.cmd_setdist.args = "self = concept : Bold Explorer : Always seeking adventure"
        self.cmd_setdist.func()
        trait = self.char1.distinctions.get("concept")
        self.assertIsNotNone(trait)
        self.assertEqual(trait.value, 8)  # All distinctions are d8
        self.assertEqual(trait.desc, "Always seeking adventure")
        self.assertEqual(trait.name, "Bold Explorer")
        
        # Test setting culture distinction
        self.cmd_setdist.args = "self = culture : Islander : Born on the seas"
        self.cmd_setdist.func()
        trait = self.char1.distinctions.get("culture")
        self.assertIsNotNone(trait)
        self.assertEqual(trait.value, 8)  # All distinctions are d8
        self.assertEqual(trait.desc, "Born on the seas")
        self.assertEqual(trait.name, "Islander")
        
        # Test invalid slot
        self.cmd_setdist.args = "self = invalid : Test : Description"
        self.cmd_setdist.func()
        self.cmd_setdist.msg.assert_called_with("Invalid slot. Must be one of: concept, culture, reputation")

    def test_set_age(self):
        """Test age command."""
        # Test setting age with permission
        self.cmd_age.args = "self = 30"
        self.cmd_age.func()
        self.assertEqual(self.char1.db.age, "30")
        
        # Test invalid command format
        self.cmd_age.args = "self"  # Missing =
        self.cmd_age.func()
        self.assertIn("Usage: setage", self.cmd_age.msg.mock_calls[-1][1][0])
        
        # Test empty command
        self.cmd_age.args = ""
        self.cmd_age.func()
        self.assertIn("Usage: setage", self.cmd_age.msg.mock_calls[-1][1][0])

    def test_set_birthday(self):
        """Test birthday command."""
        # Test setting birthday with permission
        self.cmd_birthday.args = "self = December 25th"
        self.cmd_birthday.func()
        self.assertEqual(self.char1.db.birthday, "December 25th")
        
        # Test invalid command format
        self.cmd_birthday.args = "self"  # Missing =
        self.cmd_birthday.func()
        self.assertIn("Usage: setbirthday", self.cmd_birthday.msg.mock_calls[-1][1][0])
        
        # Test empty command
        self.cmd_birthday.args = ""
        self.cmd_birthday.func()
        self.assertIn("Usage: setbirthday", self.cmd_birthday.msg.mock_calls[-1][1][0])

    def test_set_gender(self):
        """Test gender command."""
        # Test setting gender with permission
        self.cmd_gender.args = "self = Female"
        self.cmd_gender.func()
        self.assertEqual(self.char1.db.gender, "Female")
        
        # Test invalid command format
        self.cmd_gender.args = "self"  # Missing =
        self.cmd_gender.func()
        self.assertIn("Usage: setgender", self.cmd_gender.msg.mock_calls[-1][1][0])
        
        # Test empty command
        self.cmd_gender.args = ""
        self.cmd_gender.func()
        self.assertIn("Usage: setgender", self.cmd_gender.msg.mock_calls[-1][1][0])

    def test_special_effects_command(self):
        """Test the setsfx command."""
        # Set up the command
        cmd = CmdSetSpecialEffects()
        cmd.caller = self.char1
        cmd.obj = self.char1
        cmd.msg = MagicMock()
        
        # Test setting special effects
        cmd.args = "self = Has a magical aura that glows softly in darkness"
        cmd.func()
        self.assertEqual(self.char1.db.special_effects, "Has a magical aura that glows softly in darkness")
        cmd.msg.assert_called_with("Set special effects for Char:\nHas a magical aura that glows softly in darkness")
        
        # Test clearing special effects
        cmd.msg.reset_mock()
        cmd.args = "self = "
        cmd.func()
        self.assertEqual(self.char1.db.special_effects, "")
        cmd.msg.assert_called_with("Cleared special effects for Char.")
        
        # Test invalid syntax
        cmd.msg.reset_mock()
        cmd.args = "invalid syntax"
        cmd.func()
        cmd.msg.assert_called_with("Usage: setsfx <character> = <special effects text>")

if __name__ == '__main__':
    unittest.main() 