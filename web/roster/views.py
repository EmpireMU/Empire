from django.shortcuts import render
from evennia.objects.models import ObjectDB
from typeclasses.characters import STATUS_AVAILABLE, STATUS_ACTIVE, STATUS_GONE
from typeclasses.organisations import Organisation

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
    
    # Get all organizations
    organizations = ObjectDB.objects.filter(db_typeclass_path='typeclasses.organisations.Organisation').order_by('db_key')
    
    # Helper function to get concept
    def get_concept(char):
        try:
            if hasattr(char, 'distinctions'):
                concept = char.distinctions.get("concept")
                if concept:
                    return concept.name
        except Exception:
            pass
        return "No concept set"

    # Helper function to get display name
    def get_display_name(char):
        return char.db.full_name or char.name

    # Helper function to get organization data for a character list
    def get_org_data(chars, org):
        org_chars = []
        for char in chars:
            try:
                # Get character's organizations safely
                char_orgs = char.attributes.get('organisations', default={}, category='organisations')
                if org.id in char_orgs:
                    rank = char_orgs[org.id]
                    rank_name = org.db.rank_names.get(rank, f"Rank {rank}")
                    org_chars.append({
                        'char': char,
                        'concept': get_concept(char),
                        'display_name': get_display_name(char),
                        'rank_name': rank_name,
                        'rank': rank  # Store rank for sorting
                    })
            except Exception:
                continue
                
        # Sort by rank (lower numbers first) then name
        return sorted(org_chars, key=lambda x: (x['rank'], x['char'].key.lower()))

    # Prepare organization data for each status
    org_data = {}
    for status, char_list in [('available', available_chars), 
                            ('active', active_chars), 
                            ('gone', gone_chars)]:
        status_orgs = []
        for org in organizations:
            org_chars = get_org_data(char_list, org)
            if org_chars:  # Only include organizations with members
                status_orgs.append((org, [
                    (char_data['char'], 
                     char_data['concept'], 
                     char_data['display_name'], 
                     char_data['rank_name']) 
                    for char_data in org_chars
                ]))
        org_data[status] = status_orgs

    # Prepare context with character data
    context = {
        'available_chars': [(char, get_concept(char), get_display_name(char)) for char in available_chars],
        'active_chars': [(char, get_concept(char), get_display_name(char)) for char in active_chars],
        'gone_chars': [(char, get_concept(char), get_display_name(char)) for char in gone_chars],
        'organizations': org_data
    }
    
    return render(request, 'roster/roster.html', context)
