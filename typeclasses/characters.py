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
        return TraitHandler(self)
        
    @lazy_property
    def distinctions(self):
        """
        Distinctions are always d8 and can be used as d4 for a plot point.
        Every character has three:
        1. Character concept (e.g. "Bold Adventurer")
        2. Cultural background
        3. How they are perceived by others
        """
        return TraitHandler(self, db_attribute_key="distinctions")
        
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
        return TraitHandler(self, db_attribute_key="attributes")
        
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
        return TraitHandler(self, db_attribute_key="skills")
        
    @lazy_property
    def resources(self):
        """
        Resources are organizational dice pools for:
        - Political Capital
        - Wealth
        - Military
        """
        return TraitHandler(self, db_attribute_key="resources")
        
    @lazy_property
    def signature_assets(self):
        """
        Signature Assets are remarkable items or NPC companions.
        Usually d8, sometimes d6, rarely d10 or d12.
        """
        return TraitHandler(self, db_attribute_key="signature_assets")
        
    def at_object_creation(self):
        """
        Called only once when object is first created.
        """
        # Everyone starts with 1 plot point
        self.traits.add("plot_points", "Plot Points", trait_type="counter", base=1, min=0)
        
        # Add attributes (all start at d6 - "typical person")
        self.attributes.add("prowess", "Prowess", trait_type="static", base=6,
                          desc="Strength, endurance and ability to fight")
        self.attributes.add("finesse", "Finesse", trait_type="static", base=6,
                          desc="Dexterity and agility")
        self.attributes.add("leadership", "Leadership", trait_type="static", base=6,
                          desc="Capacity as a leader")
        self.attributes.add("social", "Social", trait_type="static", base=6,
                          desc="Charisma and social navigation")
        self.attributes.add("acuity", "Acuity", trait_type="static", base=6,
                          desc="Perception and information processing")
        self.attributes.add("erudition", "Erudition", trait_type="static", base=6,
                          desc="Learning and recall ability")
                          
        # Add skills (start at d4 - "untrained")
        SKILL_LIST = [
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
        
        for skill_key, skill_name, skill_desc in SKILL_LIST:
            self.skills.add(skill_key, skill_name, trait_type="static", base=4,
                          desc=skill_desc)
                          
        # Add three empty distinction slots to be filled during character generation
        self.distinctions.add("concept", "Character Concept", trait_type="static", base=8,
                            desc="Core character concept (e.g. Bold Adventurer)")
        self.distinctions.add("culture", "Cultural Background", trait_type="static", base=8,
                            desc="Character's cultural origin")
        self.distinctions.add("reputation", "Reputation", trait_type="static", base=8,
                            desc="How others perceive the character")
                            
        # Resources and Signature Assets start empty - added through play
