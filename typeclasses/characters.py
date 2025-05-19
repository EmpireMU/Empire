"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

from evennia.objects.objects import DefaultCharacter
from evennia.utils import lazy_property
from evennia.contrib.rpg.traits import TraitHandler
from .objects import ObjectParent
from utils.character_setup import initialize_traits


class Character(ObjectParent, DefaultCharacter):
    """
    The Character represents a playable character in the game world.
    It implements the Empire's Cortex Prime ruleset using Evennia's trait system.
    
    Prime Sets (one die from each is used in almost every roll):
    - Distinctions (d8, can be used as d4 for plot point)
    - Attributes (d4-d12, representing innate capabilities)
    - Skills (d4-d12, representing training and expertise)
    
    Additional Sets:
    - Resources (organizational dice pools)
    - Signature Assets (remarkable items or NPC companions)
    """

    @lazy_property
    def traits(self):
        """Main trait handler for general traits like plot points."""
        return self._traits if hasattr(self, '_traits') else TraitHandler(self)
        
    @lazy_property
    def distinctions(self):
        """
        Distinctions are always d8 and can be used as d4 for a plot point.
        Every character has three:
        1. Character concept (e.g. "Bold Adventurer")
        2. Cultural background
        3. How they are perceived by others
        """
        return self._distinctions if hasattr(self, '_distinctions') else TraitHandler(self, db_attribute_key="distinctions")
        
    @lazy_property
    def attributes(self):
        """
        Attributes represent raw ability (d4-d12):
        - d4: Notable deficiency
        - d6: Typical person
        - d8: Notable strength
        - d10: Rarely-surpassed excellence
        - d12: Peak of human performance
        """
        return self._attributes if hasattr(self, '_attributes') else TraitHandler(self, db_attribute_key="attributes")
        
    @lazy_property
    def skills(self):
        """
        Skills represent training/expertise (d4-d12):
        - d4: Untrained, likely to cause trouble
        - d6: Comfortable, knows their limits
        - d8: Expert
        - d10: Top of their field
        - d12: Legendary
        """
        return self._skills if hasattr(self, '_skills') else TraitHandler(self, db_attribute_key="skills")
        
    @lazy_property
    def resources(self):
        """
        Resources are organizational dice pools for:
        - Political Capital
        - Wealth
        - Military
        """
        return self._resources if hasattr(self, '_resources') else TraitHandler(self, db_attribute_key="resources")
        
    @lazy_property
    def signature_assets(self):
        """
        Signature Assets are remarkable items or NPC companions.
        Usually d8, sometimes d6, rarely d10 or d12.
        """
        return self._signature_assets if hasattr(self, '_signature_assets') else TraitHandler(self, db_attribute_key="signature_assets")
        
    def at_object_creation(self):
        """
        Called only once when object is first created.
        Initialize all traits using the standard initialization function.
        """
        success, message = initialize_traits(self)
        if not success:
            self.msg(f"Warning: Failed to initialize traits: {message}")
    
    def at_post_puppet(self):
        """
        Called just after puppeting has completed.
        Ensures traits are properly initialized.
        """
        super().at_post_puppet()
        
        # Make sure traits are initialized
        if not all(hasattr(self, attr) for attr in ['_traits', '_attributes', '_skills', '_distinctions', '_resources', '_signature_assets']):
            success, message = initialize_traits(self)
            if not success:
                self.msg(f"Warning: Failed to initialize traits: {message}")
    
    # Resources and Signature Assets start empty - added through play
