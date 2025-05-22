"""
Tests for Cortex Prime dice rolling command.
"""

from unittest.mock import MagicMock, patch
from evennia.utils.test_resources import EvenniaTest
from commands.cortex_roll import CmdCortexRoll, TraitDie
from evennia.contrib.rpg.traits import TraitHandler
from evennia.objects.objects import ObjectDB
from evennia import create_object, SESSION_HANDLER

class TestCortexRoll(EvenniaTest):
    """Test cases for Cortex Prime dice rolling functionality."""
    
    def setUp(self):
        """Set up test case."""
        super().setUp()
        self.cmd = CmdCortexRoll()
        self.cmd.caller = self.char1
        self.cmd.obj = self.char1
        
        # Set up message mocking
        self.caller = self.char1
        self.caller.msg = MagicMock()
        self.cmd.msg = self.caller.msg
        
        # Set up location message mocking
        self.char1.location.msg_contents = MagicMock()
        
        # Set up session
        self.session = MagicMock()
        self.session.sessid = 1  # Give it a real session ID
        self.cmd.session = self.session
        SESSION_HANDLER[1] = self.session  # Register the session
        
        # Initialize trait handlers
        if not hasattr(self.char1, 'char_attributes'):
            self.char1.char_attributes = TraitHandler(self.char1, db_attribute_key="char_attributes")
        if not hasattr(self.char1, 'skills'):
            self.char1.skills = TraitHandler(self.char1, db_attribute_key="skills")
        if not hasattr(self.char1, 'distinctions'):
            self.char1.distinctions = TraitHandler(self.char1, db_attribute_key="char_distinctions")
        if not hasattr(self.char1, 'signature_assets'):
            self.char1.signature_assets = TraitHandler(self.char1, db_attribute_key="signature_assets")
        if not hasattr(self.char1, 'char_resources'):
            self.char1.char_resources = TraitHandler(self.char1, db_attribute_key="char_resources")
        
        # Add test traits
        self.char1.char_attributes.add("strength", "Strength", trait_type="static", base=8)
        self.char1.char_attributes.add("agility", "Agility", trait_type="static", base=6)
        
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
        # Set up mock rolls with enough values for all tests
        mock_roll.side_effect = [6, 4, 8, 6, 4, 8]  # Two sets of rolls for two tests
        
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
        # Set up mock rolls with enough values for all tests
        mock_roll.side_effect = [6, 4, 8, 6, 4, 8]  # Two sets of rolls for two tests
        
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

    @patch('commands.cortex_roll.roll_die')
    def test_effect_die_display(self, mock_roll):
        """Test that effect die is displayed with 'd' prefix."""
        # Set up mock rolls to get a predictable effect die
        mock_roll.side_effect = [8, 6, 4]  # This will make d8 the effect die
        
        # Create a proper mock location
        mock_location = create_object(ObjectDB, key="Mock Room")
        mock_location.msg_contents = MagicMock()
        self.char1.location = mock_location
        
        # Set up test traits
        self.cmd.args = "strength fighting warrior"
        self.cmd.parse()
        self.cmd.func()
        
        # Check that msg_contents was called
        self.assertTrue(mock_location.msg_contents.called)
        
        # Get all messages sent to the room
        room_messages = [call[1][0] for call in mock_location.msg_contents.mock_calls]
        
        # Check that at least one message contains the effect die
        self.assertTrue(any("Effect Die: |wd8|n" in msg for msg in room_messages))
        
        # Reset mock
        mock_roll.reset_mock()

if __name__ == '__main__':
    unittest.main() 