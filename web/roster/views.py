from django.shortcuts import render
from evennia.objects.models import ObjectDB
from typeclasses.characters import STATUS_AVAILABLE, STATUS_ACTIVE, STATUS_GONE

def roster_view(request):
    """
    Main view for the character roster.
    Shows available, active, and retired characters.
    """
    # Get characters by status
    available_chars = ObjectDB.objects.filter(db_attributes__db_key='status', 
                                           db_attributes__db_value=STATUS_AVAILABLE).order_by('db_key')
    active_chars = ObjectDB.objects.filter(db_attributes__db_key='status',
                                        db_attributes__db_value=STATUS_ACTIVE).order_by('db_key')
    gone_chars = ObjectDB.objects.filter(db_attributes__db_key='status',
                                      db_attributes__db_value=STATUS_GONE).order_by('db_key')
    
    # Helper function to get concept
    def get_concept(char):
        if hasattr(char, 'distinctions'):
            concept = char.distinctions.get("concept")
            if concept:
                return concept.name
        return "No concept set"

    # Helper function to get display name
    def get_display_name(char):
        return char.db.full_name or char.name

    # Prepare context with character data
    context = {
        'available_chars': [(char, get_concept(char), get_display_name(char)) for char in available_chars],
        'active_chars': [(char, get_concept(char), get_display_name(char)) for char in active_chars],
        'gone_chars': [(char, get_concept(char), get_display_name(char)) for char in gone_chars],
    }
    
    return render(request, 'roster/roster.html', context)
