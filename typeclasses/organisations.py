"""
Organizations

Organizations represent groups like noble houses, guilds, or factions.
They can have members with different ranks and provide resources to their members.
"""

from evennia.objects.objects import DefaultObject
from evennia.utils import lazy_property
from evennia.utils.search import search_object
from .objects import ObjectParent
from evennia.contrib.rpg.traits import TraitHandler


class Organisation(ObjectParent, DefaultObject):
    """
    An organization that characters can join.
    Organizations can have different ranks and provide resources to members.
    """
    
    MAX_RANKS = 10
    
    @lazy_property
    def members(self):
        """
        Get all members of this organization.
        Returns a dict of {char_id: rank_number}
        """
        return self.attributes.get('members', default={}, category='organisation')
        
    @lazy_property
    def org_resources(self):
        """
        TraitHandler that manages organization resources.
        Each trait represents a die pool (d4-d12).
        """
        return TraitHandler(self, db_attribute_key="org_resources")

    def at_object_creation(self):
        """
        Called when the organization is first created.
        """
        super().at_object_creation()
        
        # Initialize member list
        self.attributes.add('members', {}, category='organisation')
        
        # Set up organization properties
        self.db.description = "No description has been set."
        
        # Initialize default ranks
        self.db.ranks = {
            1: "Head of House",
            2: "Minister",
            3: "Noble Family",
            4: "Senior Servant"
        }
            
    def add_org_resource(self, name, die_size):
        """
        Add a resource to the organization.
        
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
        while name in self.org_resources.traits:
            counter += 1
            name = f"{base_name} {counter}"
            
        self.org_resources.add(name, die_size)
        return True
        
    def remove_org_resource(self, name):
        """
        Remove a resource from the organization.
        
        Args:
            name (str): Name of the resource to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        if name in self.org_resources.traits:
            self.org_resources.remove(name)
            return True
        return False
        
    def transfer_resource(self, resource_name, target):
        """
        Transfer a resource to a character or another organization.
        
        Args:
            resource_name (str): Name of the resource to transfer
            target (Character or Organisation): Who to transfer to
            
        Returns:
            bool: True if transferred successfully
            
        Raises:
            ValueError: If resource not found or target is invalid
        """
        if resource_name not in self.org_resources.traits:
            raise ValueError(f"Resource '{resource_name}' not found")
            
        from typeclasses.characters import Character
        if not (isinstance(target, type(self)) or isinstance(target, Character)):
            raise ValueError("Can only transfer resources to characters or organizations")
            
        # Get the die size before removing
        die_size = self.org_resources.traits[resource_name].current
        
        # Remove from self
        self.org_resources.remove(resource_name)
        
        # Add to target
        if isinstance(target, Character):
            target.add_resource(resource_name, die_size)
        else:
            target.add_org_resource(resource_name, die_size)
            
        return True
        
    def get_resources(self):
        """
        Get a formatted list of all resources.
        
        Returns:
            list: List of (name, die_size) tuples
        """
        resources = []
        for name, trait in self.org_resources.traits.items():
            resources.append((name, trait.current))
        return sorted(resources)
        
    def add_member(self, character, rank=4):
        """
        Add a character to the organization.
        
        Args:
            character: The character to add
            rank: The rank to give them (default: Senior Servant)
        """
        if not character.check_permstring("Admin"):
            return False
            
        # Add to organization's member list
        members = self.members
        members[character.id] = rank
        self.attributes.add('members', members, category='organisation')
        
        # Add to character's organization list
        orgs = character.attributes.get('organisations', default={}, category='organisations')
        orgs[self.id] = rank
        character.attributes.add('organisations', orgs, category='organisations')
        return True
        
    def remove_member(self, character):
        """
        Remove a character from the organization.
        
        Args:
            character: The character to remove
        """
        if not character.check_permstring("Admin"):
            return False
            
        # Remove from organization's member list
        members = self.members
        if character.id in members:
            del members[character.id]
            self.attributes.add('members', members, category='organisation')
        
        # Remove from character's organization list
        orgs = character.attributes.get('organisations', default={}, category='organisations')
        if self.id in orgs:
            del orgs[self.id]
            character.attributes.add('organisations', orgs, category='organisations')
        return True
            
    def set_rank(self, character, rank):
        """
        Set a character's rank in the organization.
        
        Args:
            character: The character to set rank for
            rank: The new rank number (1-10)
        """
        if not character.check_permstring("Admin"):
            return False
            
        if not isinstance(rank, int) or rank < 1 or rank > self.MAX_RANKS:
            return False
            
        # Update organization's member list
        members = self.members
        if character.id in members:
            members[character.id] = rank
            self.attributes.add('members', members, category='organisation')
            
            # Update character's organization list
            orgs = character.attributes.get('organisations', default={}, category='organisations')
            orgs[self.id] = rank
            character.attributes.add('organisations', orgs, category='organisations')
            return True
            
        return False
        
    def set_rank_name(self, rank, name):
        """
        Set the name for a rank number.
        
        Args:
            rank: The rank number (1-10)
            name: The name to give this rank
        """
        if not isinstance(rank, int) or rank < 1 or rank > self.MAX_RANKS:
            return False
            
        ranks = self.db.ranks or {}
        ranks[rank] = name
        self.db.ranks = ranks
        return True
        
    def get_rank_name(self, rank):
        """
        Get the name of a rank number.
        
        Args:
            rank: The rank number
            
        Returns:
            The rank name or None if invalid
        """
        return self.db.ranks.get(rank)
        
    def get_member_rank(self, character):
        """
        Get a character's rank in the organization.
        
        Args:
            character: The character to check
            
        Returns:
            The rank number or None if not a member
        """
        return self.members.get(character.id)
        
    def get_member_rank_name(self, character):
        """
        Get a character's rank name in the organization.
        
        Args:
            character: The character to check
            
        Returns:
            The rank name or None if not a member
        """
        rank = self.get_member_rank(character)
        if rank is not None:
            return self.get_rank_name(rank)
        return None

    def get_members(self):
        """
        Get all members of the organisation.
        
        Returns:
            List of (character, rank_number, rank_name) tuples
        """
        members = []
        for char_id, rank_num in self.members.items():
            # Search for character using Evennia's search with dbref
            chars = search_object(f"#{char_id}")
            if chars:
                char = chars[0]
                rank_name = self.get_rank_name(rank_num) or f"Rank {rank_num}"
                members.append((char, rank_num, rank_name))
        return sorted(members, key=lambda x: x[1])  # Sort by rank number
        
    def delete(self):
        """
        Delete the organisation and clean up all references.
        """
        # Remove all members
        for char_id in list(self.members.keys()):
            chars = search_object(f"#{char_id}")
            if chars:
                self.remove_member(chars[0])
        
        # Delete the organisation
        super().delete() 