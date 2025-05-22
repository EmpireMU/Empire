"""
Tests for Cortex Prime dice rolling command.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.cortex_roll import CmdCortexRoll, TraitDie

class TestCortexRoll(EvenniaTest):
    """Test cases for the Cortex roll command."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        self.cmd = CmdCortexRoll()
        self.cmd.caller = self.char1
        self.cmd.obj = self.char1
        
        # Mock character attributes
        self.char1.character_attributes = MagicMock()
        self.char1.skills = MagicMock()
        self.char1.distinctions = MagicMock()
        self.char1.signature_assets = MagicMock()
        self.char1.char_resources = MagicMock()
        
        # Set up some test traits
        self.setup_test_traits()
    
    def setup_test_traits(self):
        """Set up test traits on the character."""
        # Mock trait objects
        class MockTrait:
            def __init__(self, base):
                self.base = base
                
        # Set up attributes
        self.char1.character_attributes.all.return_value = ["strength", "agility"]
        self.char1.character_attributes.get.side_effect = lambda x: {
            "strength": MockTrait(8),
            "agility": MockTrait(6)
        }.get(x)
        
        # Set up skills
        self.char1.skills.all.return_value = ["fighting", "stealth"]
        self.char1.skills.get.side_effect = lambda x: {
            "fighting": MockTrait(8),
            "stealth": MockTrait(6)
        }.get(x)
        
        # Set up distinctions
        self.char1.distinctions.all.return_value = ["warrior"]
        self.char1.distinctions.get.side_effect = lambda x: {
            "warrior": MockTrait(8)
        }.get(x)
        
        # Set up signature assets
        self.char1.signature_assets.all.return_value = ["sword"]
        self.char1.signature_assets.get.side_effect = lambda x: {
            "sword": MockTrait(6)
        }.get(x)
    
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