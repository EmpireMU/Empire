"""
Resources

Resources represent dice pools that can be owned and transferred between characters
and organizations. They track their history and origin.
"""

from evennia.objects.objects import DefaultObject
from evennia.utils import lazy_property
from .objects import ObjectParent


class Resource(ObjectParent, DefaultObject):
    """
    A resource represents a die pool (d4-d12) that can be owned and transferred.
    Resources track their history and origin.
    
    Properties:
    - die_size: The size of the die (4-12)
    - owner: The character or organization that owns this resource
    - origin: Where this resource came from originally
    - history: List of ownership transfers
    """
    
    VALID_DIE_SIZES = [4, 6, 8, 10, 12]
    
    def at_object_creation(self):
        """
        Called when the resource is first created.
        Initialize all properties.
        """
        super().at_object_creation()
        
        # Set up basic properties
        self.db.die_size = 6  # Default to d6
        self.db.owner = None  # Will be set when assigned
        self.db.origin = None  # Will be set at creation
        self.db.history = []  # List of (timestamp, from_obj, to_obj) tuples
        
    @property
    def die_size(self):
        """Get the current die size."""
        return self.db.die_size
        
    @die_size.setter
    def die_size(self, value):
        """
        Set the die size, validating it's a proper die type.
        
        Args:
            value (int): The die size (4, 6, 8, 10, or 12)
            
        Raises:
            ValueError: If the die size is invalid
        """
        if value not in self.VALID_DIE_SIZES:
            raise ValueError(f"Die size must be one of: {', '.join(map(str, self.VALID_DIE_SIZES))}")
        self.db.die_size = value
        
    @property
    def owner(self):
        """Get the current owner."""
        return self.db.owner
        
    def set_owner(self, new_owner, transfer_from=None):
        """
        Set a new owner and record the transfer in history.
        
        Args:
            new_owner: The new owner (Character or Organization)
            transfer_from: Who is transferring the resource (for history)
        """
        from evennia.utils.create import create_script
        
        # If this is the first owner, set as origin
        if not self.db.origin:
            self.db.origin = new_owner
            
        # Record the transfer in history
        if transfer_from or self.db.owner:
            timestamp = create_script().start_time  # Current time
            self.db.history.append((timestamp, transfer_from or self.db.owner, new_owner))
            
        # Update the owner
        self.db.owner = new_owner
        
    def get_history(self):
        """
        Get the formatted transfer history.
        
        Returns:
            list: List of formatted history strings
        """
        history = []
        for timestamp, from_obj, to_obj in self.db.history:
            from_name = from_obj.name if from_obj else "Unknown"
            to_name = to_obj.name if to_obj else "Unknown"
            history.append(f"{timestamp}: {from_name} -> {to_name}")
        return history
        
    def return_appearance(self, looker):
        """
        This formats a description for the resource.
        
        Args:
            looker (Object): Object doing the looking.
        """
        text = [f"|c{self.name}|n"]
        text.append(f"A d{self.die_size} resource.")
            
        if self.db.owner:
            text.append(f"\nCurrently owned by: {self.db.owner.name}")
            
        if self.db.origin:
            text.append(f"Originally from: {self.db.origin.name}")
            
        if self.db.history:
            text.append("\nTransfer History:")
            text.extend(self.get_history())
            
        return "\n".join(text) 