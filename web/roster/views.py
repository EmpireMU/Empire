from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from evennia.objects.models import ObjectDB
from typeclasses.characters import STATUS_AVAILABLE, STATUS_ACTIVE, STATUS_GONE
from typeclasses.organisations import Organisation
import logging

logger = logging.getLogger('web')

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

def character_detail_view(request, char_name, char_id):
    """
    Detailed view for a specific character.
    Shows character's biography, traits, and other information.
    """
    # Get the character or 404
    character = get_object_or_404(ObjectDB, id=char_id, db_key__iexact=char_name)
    
    # Check if user can see traits (staff or character owner)
    can_see_traits = request.user.is_staff
    if hasattr(character, 'account') and character.account:
        can_see_traits = can_see_traits or (character.account.id == request.user.id)
    
    # Get character's basic info
    basic_info = {
        'name': character.db.full_name or character.name,
        'concept': character.distinctions.get('concept').name if character.distinctions.get('concept') else None,
        'gender': character.db.gender,
        'age': character.db.age,
        'birthday': character.db.birthday,
        'realm': character.db.realm,
        'culture': character.distinctions.get('culture').name if character.distinctions.get('culture') else None,
        'vocation': character.db.vocation,
        'notable_traits': character.db.notable_traits,
        'description': character.db.desc,
        'background': character.db.background,
        'personality': character.db.personality,
    }
    
    # Get character's organizations
    organizations = []
    for org_id, rank in character.organisations.items():
        try:
            org = ObjectDB.objects.get(id=org_id)
            rank_name = org.db.rank_names.get(rank, f"Rank {rank}")
            organizations.append({
                'name': org.name,
                'rank': rank_name
            })
        except ObjectDB.DoesNotExist:
            continue
    
    context = {
        'character': character,
        'basic_info': basic_info,
        'organizations': organizations,
        'can_see_traits': can_see_traits,
    }
    
    # Only include traits if user has permission
    if can_see_traits:
        # Get character's distinctions
        distinctions = {}
        for key in character.distinctions.all():
            trait = character.distinctions.get(key)
            distinctions[trait.name or key] = {
                'description': trait.desc or "No description",
                'value': f"d{trait.value}"
            }
        
        # Get character's attributes
        attributes = {}
        for key in character.character_attributes.all():
            trait = character.character_attributes.get(key)
            attributes[trait.name or key] = {
                'description': trait.desc or "No description",
                'value': f"d{trait.value}"
            }
        
        # Get character's skills
        skills = {}
        for key in character.skills.all():
            trait = character.skills.get(key)
            skills[trait.name or key] = {
                'description': trait.desc or "No description",
                'value': f"d{trait.value}"
            }
        
        # Get character's signature assets
        signature_assets = {}
        for key in character.signature_assets.all():
            trait = character.signature_assets.get(key)
            signature_assets[key] = {
                'description': trait.desc or "No description",
                'value': f"d{trait.value}"
            }
        
        # Add traits to context
        context.update({
            'distinctions': distinctions,
            'attributes': attributes,
            'skills': skills,
            'signature_assets': signature_assets,
        })
    
    return render(request, 'roster/character_detail.html', context)

@require_POST
@csrf_protect
def update_character_field(request, char_name, char_id):
    """
    API endpoint to update a character field.
    Only accessible by staff members.
    """
    try:
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        character = get_object_or_404(ObjectDB, id=char_id, db_key__iexact=char_name)
        field = request.POST.get('field')
        value = request.POST.get('value', '')
        
        if not field:
            return JsonResponse({'error': 'Missing field'}, status=400)
        
        # List of allowed fields for editing
        allowed_fields = [
            'full_name',
            'gender',
            'age',
            'birthday',
            'realm',
            'vocation',
            'desc',
            'background',
            'personality',
            'notable_traits'
        ]
        
        if field not in allowed_fields:
            return JsonResponse({'error': f'Invalid field: {field}'}, status=400)
        
        # Update the field using Evennia's db handler
        setattr(character.db, field, value)
        logger.info(f"Updated {char_name}'s {field}")
        
        return JsonResponse({
            'success': True,
            'value': value,
            'message': f'Successfully updated {field}'
        })
        
    except Exception as e:
        logger.error(f"Error updating character field: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'message': 'Server error occurred'
        }, status=500)
