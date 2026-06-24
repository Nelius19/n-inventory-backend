from django.db import transaction
from .models import House, HouseMember
import random


# Generate random invite code upto six character long
def generated_invite_code():
    ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choices(ALPHABET, k=6))

# Unique invite code
def unique_code():
    code = generated_invite_code()                          # assign generated invite code
    while House.objects.filter(invite_code=code).exists():  # check code exists, until code does not exists
        code = generated_invite_code()
    return code                                             # return unique code

# User house creation upon registeration
@transaction.atomic
def create_house_for(user):
    house_name = f"{user.username}-house"                   # username as part of house_name
    code = unique_code()                    

    # create and return objects
    house = House.objects.create(name=house_name, invite_code=code, owner=user)
    HouseMember.objects.create(role="owner", user=user, house=house)

    return house
