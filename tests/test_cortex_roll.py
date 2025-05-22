"""
Tests for Cortex Prime dice rolling command.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.cortex_roll import CmdCortexRoll, TraitDie
from evennia.contrib.rpg.traits import TraitHandler

class TestCortexRoll(EvenniaTest):
    """Test cases for the Cortex roll command."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        self.cmd = CmdCortexRoll()
        self.cmd.caller = self.char1
        self.cmd.obj = self.char1
        
        # Set up trait handlers properly
        self.char1.character_attributes = TraitHandler(self.char1, db_attribute_key="character_attributes")
        self.char1.skills = TraitHandler(self.char1, db_attribute_key="skills")
        self.char1.distinctions = TraitHandler(self.char1, db_attribute_key="distinctions")
        self.char1.signature_assets = TraitHandler(self.char1, db_attribute_key="signature_assets")
        self.char1.char_resources = TraitHandler(self.char1, db_attribute_key="char_resources")
        
        # Set up test traits
        self.setup_test_traits()
    
    def setup_test_traits(self):
        """Set up test traits on the character."""
        # Add attributes
        self.char1.character_attributes.add("strength", "Strength", trait_type="static", base=8)
        self.char1.character_attributes.add("agility", "Agility", trait_type="static", base=6)
        
        # Add skills
        self.char1.skills.add("fighting", "Fighting", trait_type="static", base=8)
        self.char1.skills.add("stealth", "Stealth", trait_type="static", base=6)
        
        # Add distinctions
        self.char1.distinctions.add("warrior", "Warrior", trait_type="static", base=8)
        
        # Add signature assets
        self.char1.signature_assets.add("sword", "Magic Sword", trait_type="static", base=6)
    
    @patch('commands.cortex_roll.roll_die')
    def test_basic_roll(self, mock_roll):
        """Test basic dice rolling."""
        # Set up mock rolls
        mock_roll.side_effect = [6, 4, 8]  # Strength d8=6, Fighting d8=4, Warrior d8=8
        
        # Execute command
        self.cmd.args = "strength fighting warrior"
        self.cmd.parse()
        self.cmd.func()
        
        # Check that the right dice were rolled
        self.assertEqual(mock_roll.call_count, 3)
        mock_roll.assert_any_call(8)  # Strength d8
        mock_roll.assert_any_call(8)  # Fighting d8
        mock_roll.assert_any_call(8)  # Warrior d8
        
        # Reset mock
        mock_roll.reset_mock()
    
    @patch('commands.cortex_roll.roll_die')
    def test_roll_with_difficulty(self, mock_roll):
        """Test rolling against a difficulty."""
        # Set up mock rolls
        mock_roll.side_effect = [6, 4, 8]  # Total will be 14 (8 + 6)
        
        # Test numeric difficulty
        self.cmd.args = "strength fighting warrior vs 12"
        self.cmd.parse()
        self.cmd.func()
        
        # Test named difficulty
        self.cmd.args = "strength fighting warrior vs hard"
        self.cmd.parse()
        self.cmd.func()
        
        # Reset mock
        mock_roll.reset_mock()
    
    @patch('commands.cortex_roll.roll_die')
    def test_roll_with_step(self, mock_roll):
        """Test rolling with stepped dice."""
        # Set up mock rolls
        mock_roll.side_effect = [6, 4, 8]
        
        # Test stepping up
        self.cmd.args = "strength(U) fighting warrior"
        self.cmd.parse()
        self.cmd.func()
        
        # Test stepping down
        self.cmd.args = "strength(D) fighting warrior"
        self.cmd.parse()
        self.cmd.func()
        
        # Reset mock
        mock_roll.reset_mock()
    
    @patch('commands.cortex_roll.roll_die')
    def test_roll_with_hitches(self, mock_roll):
        """Test rolling with hitches (1s)."""
        # Set up mock rolls to include hitches
        mock_roll.side_effect = [1, 1, 8]  # Two hitches and one success
        
        self.cmd.args = "strength fighting warrior"
        self.cmd.parse()
        self.cmd.func()
        
        # Reset mock
        mock_roll.reset_mock()
    
    def test_invalid_rolls(self):
        """Test various invalid roll attempts."""
        # Test empty roll
        self.cmd.args = ""
        self.cmd.parse()
        self.assertFalse(self.cmd.dice)
        
        # Test unknown trait
        self.cmd.args = "nonexistent fighting warrior"
        self.cmd.parse()
        self.assertFalse(self.cmd.dice)
        
        # Test invalid difficulty
        self.cmd.args = "strength fighting warrior vs invalid"
        self.cmd.parse()
        self.assertFalse(self.cmd.dice)
        
        # Test too many dice
        self.cmd.args = "strength strength strength strength strength strength strength strength strength strength strength"
        self.cmd.parse()
        self.assertFalse(self.cmd.dice)

if __name__ == '__main__':
    unittest.main() 