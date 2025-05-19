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
from utils.trait_definitions import ATTRIBUTES, SKILLS, DISTINCTIONS


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
        return TraitHandler(self, db_attribute_key="char_traits")
        
    @lazy_property
    def distinctions(self):
        """
        Distinctions are always d8 and can be used as d4 for a plot point.
        Every character has three:
        1. Character concept (e.g. "Bold Adventurer")
        2. Cultural background
        3. How they are perceived by others
        """
        return TraitHandler(self, db_attribute_key="char_distinctions")
        
    @lazy_property
    def character_attributes(self):
        """
        Character attributes (d4-d12)
        """
        return TraitHandler(self, db_attribute_key="char_attributes")
        
    @lazy_property
    def skills(self):
        """
        Character skills (d4-d12)
        """
        return TraitHandler(self, db_attribute_key="char_skills")
        
    @lazy_property
    def signature_assets(self):
        """
        Signature assets (d4-d12)
        """
        return TraitHandler(self, db_attribute_key="char_signature_assets")
        
    def at_object_creation(self):
        """
        Called only once when object is first created.
        Initialize all trait handlers and set up default traits.
        """
        # Call parent to set up basic character properties and permissions
        super().at_object_creation()

        # Initialize plot points
        self.traits.add("plot_points", value=1, min=0)

        # Initialize character background and personality
        self.db.background = "No background has been set."
        self.db.personality = "No personality has been set."

        # Initialize organization memberships
        self.db.organisations = {}

        # Initialize attributes
        for trait in ATTRIBUTES:
            existing = self.character_attributes.get(trait.key)
            if existing:
                existing.base = trait.default_value
            else:
                self.character_attributes.add(
                    trait.key,
                    value=trait.default_value,
                    desc=trait.description,
                    name=trait.name
                )
                # Ensure .base is set correctly
                self.character_attributes.get(trait.key).base = trait.default_value
            # Debug print
            self.msg(f"Attribute {trait.key}: default_value={trait.default_value}, base={self.character_attributes.get(trait.key).base}")

        # Initialize skills
        for trait in SKILLS:
            existing = self.skills.get(trait.key)
            if existing:
                existing.base = trait.default_value
            else:
                self.skills.add(
                    trait.key,
                    value=trait.default_value,
                    desc=trait.description,
                    name=trait.name
                )
                # Ensure .base is set correctly
                self.skills.get(trait.key).base = trait.default_value
            # Debug print
            self.msg(f"Skill {trait.key}: default_value={trait.default_value}, base={self.skills.get(trait.key).base}")

        # Initialize distinctions
        for trait in DISTINCTIONS:
            existing = self.distinctions.get(trait.key)
            if existing:
                existing.base = trait.default_value
            else:
                self.distinctions.add(
                    trait.key,
                    value=trait.default_value,
                    desc=trait.description,
                    name=trait.name
                )
                # Ensure .base is set correctly
                self.distinctions.get(trait.key).base = trait.default_value
            # Debug print
            self.msg(f"Distinction {trait.key}: default_value={trait.default_value}, base={self.distinctions.get(trait.key).base}")

        # Resources and signature assets are initialized empty
        # They will be added manually by the player or GM

    def at_init(self):
        """
        Called when object is first created and after it is loaded from cache.
        Ensures trait handlers are initialized.
        """
        # Call parent to set up basic object properties
        super().at_init()
        
        # Force initialize all trait handlers without sending messages
        _ = self.traits
        _ = self.distinctions
        _ = self.character_attributes
        _ = self.skills
        _ = self.signature_assets

    def at_post_puppet(self):
        """
        Called just after puppeting has completed.
        Ensures trait handlers and command set are available.
        """
        # Call parent to handle account-character connection
        super().at_post_puppet()
        
        # Ensure trait handlers are initialized
        _ = self.traits
        _ = self.distinctions
        _ = self.character_attributes
        _ = self.skills
        _ = self.signature_assets
