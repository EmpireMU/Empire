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
from commands.cortex_roll import CortexCmdSet


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
        Attributes represent raw ability (d4-d12):
        - d4: Notable deficiency
        - d6: Typical person
        - d8: Notable strength
        - d10: Rarely-surpassed excellence
        - d12: Peak of human performance
        """
        return TraitHandler(self, db_attribute_key="char_attributes")
        
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
        return TraitHandler(self, db_attribute_key="char_skills")
        
    @lazy_property
    def resources(self):
        """
        Resources are organizational dice pools for:
        - Political Capital
        - Wealth
        - Military
        """
        return TraitHandler(self, db_attribute_key="char_resources")
        
    @lazy_property
    def signature_assets(self):
        """
        Signature Assets are remarkable items or NPC companions.
        Usually d8, sometimes d6, rarely d10 or d12.
        """
        return TraitHandler(self, db_attribute_key="char_signature_assets")
        
    def at_object_creation(self):
        """
        Called only once when object is first created.
        Initialize all trait handlers and set up default traits.
        """
        super().at_object_creation()

        # Add Cortex Prime command set
        self.cmdset.add(CortexCmdSet, persistent=True)

        # Initialize plot points
        self.traits.add(key="plot_points", name="Plot Points", value=1, min=0)

        # Initialize default attributes (d6 - "typical person")
        ATTRIBUTES = [
            ("prowess", "Prowess", "Strength, endurance and ability to fight"),
            ("finesse", "Finesse", "Dexterity and agility"),
            ("leadership", "Leadership", "Capacity as a leader"),
            ("social", "Social", "Charisma and social navigation"),
            ("acuity", "Acuity", "Perception and information processing"),
            ("erudition", "Erudition", "Learning and recall ability")
        ]
        for key, name, desc in ATTRIBUTES:
            self.character_attributes.add(key=key, name=name, value=6, desc=desc)

        # Initialize default skills (d4 - "untrained")
        SKILLS = [
            ("administration", "Administration", "Organizing affairs of large groups"),
            ("arcana", "Arcana", "Knowledge of magic"),
            ("athletics", "Athletics", "General physical feats"),
            ("dexterity", "Dexterity", "Precision physical feats"),
            ("diplomacy", "Diplomacy", "Protocol and high politics"),
            ("direction", "Direction", "Leading in non-combat"),
            ("exploration", "Exploration", "Wilderness and ruins"),
            ("fighting", "Fighting", "Melee combat"),
            ("influence", "Influence", "Personal persuasion"),
            ("learning", "Learning", "Education and research"),
            ("making", "Making", "Crafting and building"),
            ("medicine", "Medicine", "Healing and medical knowledge"),
            ("perception", "Perception", "Awareness and searching"),
            ("performance", "Performance", "Entertainment arts"),
            ("presentation", "Presentation", "Style and bearing"),
            ("rhetoric", "Rhetoric", "Public speaking"),
            ("seafaring", "Seafaring", "Sailing and navigation"),
            ("shooting", "Shooting", "Ranged combat"),
            ("warfare", "Warfare", "Military leadership and strategy")
        ]
        for key, name, desc in SKILLS:
            self.skills.add(key=key, name=name, value=4, desc=desc)

        # Initialize distinction slots (d8)
        DISTINCTIONS = [
            ("concept", "Character Concept", "Core character concept (e.g. Bold Adventurer)"),
            ("culture", "Cultural Background", "Character's cultural origin"),
            ("reputation", "Reputation", "How others perceive the character")
        ]
        for key, name, desc in DISTINCTIONS:
            self.distinctions.add(key=key, name=name, value=8, desc=desc)

    def at_init(self):
        """
        Called when object is first created and after it is loaded from cache.
        """
        super().at_init()
        # Ensure trait handlers are initialized
        _ = self.traits
        _ = self.distinctions
        _ = self.character_attributes
        _ = self.skills
        _ = self.resources
        _ = self.signature_assets

    def at_post_puppet(self):
        """
        Called just after puppeting has completed.
        """
        super().at_post_puppet()
        # Ensure trait handlers are initialized
        _ = self.traits
        _ = self.distinctions
        _ = self.character_attributes
        _ = self.skills
        _ = self.resources
        _ = self.signature_assets
        
        # Ensure Cortex Prime command set is available
        self.cmdset.add(CortexCmdSet, persistent=True)
