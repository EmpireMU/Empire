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

    @lazy_property
    def char_resources(self):
        """
        TraitHandler that manages character resources.
        Each trait represents a die pool (d4-d12).
        """
        return TraitHandler(self, db_attribute_key="char_resources")

    @lazy_property
    def organisations(self):
        """
        Get all organizations this character belongs to.
        Returns a dict of {org_id: rank_number}
        """
        return self.attributes.get('organisations', default={}, category='organisations')
        
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
        self.attributes.add('organisations', {}, category='organisations')

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

        # Initialize resources handler
        _ = self.char_resources

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
        _ = self.organisations
        _ = self.char_resources

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
        _ = self.organisations
        _ = self.char_resources

    def add_resource(self, name, die_size):
        """
        Add a resource to the character.
        
        Args:
            name (str): Name of the resource
            die_size (int): Size of the die (4, 6, 8, 10, or 12)
            
        Returns:
            bool: True if added successfully
            
        Raises:
            ValueError: If die size is invalid
        """
        valid_sizes = [4, 6, 8, 10, 12]
        if die_size not in valid_sizes:
            raise ValueError(f"Die size must be one of: {', '.join(map(str, valid_sizes))}")
            
        # For multiple resources with same name, append a number
        base_name = name
        counter = 1
        while self.char_resources.get(base_name):
            counter += 1
            base_name = f"{name} {counter}"
            
        # Add the resource with the die size as the base value
        self.char_resources.add(
            base_name,
            base=die_size  # Use base instead of value
        )
        return True
        
    def remove_resource(self, name):
        """
        Remove a resource from the character.
        
        Args:
            name (str): Name of the resource to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        if self.char_resources.get(name):
            self.char_resources.remove(name)
            return True
        return False
        
    def transfer_resource(self, resource_name, target):
        """
        Transfer a resource to another character or organization.
        
        Args:
            resource_name (str): Name of the resource to transfer
            target (Character or Organisation): Who to transfer to
            
        Returns:
            bool: True if transferred successfully
            
        Raises:
            ValueError: If resource not found or target is invalid
        """
        trait = self.char_resources.get(resource_name)
        if not trait:
            raise ValueError(f"Resource '{resource_name}' not found")
            
        from typeclasses.organisations import Organisation
        if not (isinstance(target, type(self)) or isinstance(target, Organisation)):
            raise ValueError("Can only transfer resources to characters or organizations")
            
        # Get the die size before removing
        die_size = trait.value
        
        # Remove from self
        self.char_resources.remove(resource_name)
        
        # Add to target
        if isinstance(target, Organisation):
            target.add_org_resource(resource_name, die_size)
        else:
            target.add_resource(resource_name, die_size)
            
        return True
        
    def get_resources(self):
        """
        Get a formatted list of all resources.
        
        Returns:
            list: List of (name, die_size) tuples
        """
        resources = []
        for key in self.char_resources.all():
            trait = self.char_resources.get(key)
            resources.append((key, trait.value))
        return sorted(resources)
