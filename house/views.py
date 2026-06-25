from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .serializers import HouseMemberSerializer
from .models import House, HouseMember
from .services import unique_code


#
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getMemberShip(request):
    print("USER:", request.user)
    print("AUTH:", request.user.is_authenticated)
    print("COOKIES:", request.COOKIES)

    memberships = HouseMember.objects.filter(
        user=request.user
    ).select_related("house")                                   # foreign key relation

    serializer = HouseMemberSerializer(memberships, many=True)
    return Response(serializer.data, status=200)


# get members of a selected house owned by current user
@api_view(['GET'])
def house_members(request, house_id):
    if not HouseMember.objects.filter(user=request.user, house_id=house_id, role="owner").exists():
        return Response({"error": "Not authorized"}, status=403)        
    
    # get all members of the selected house
    members = HouseMember.objects.filter(house_id=house_id).exclude(role="owner").select_related("user")

    serializer = HouseMemberSerializer(members, many=True)

    return Response(serializer.data, status=200)


#
@api_view(['DELETE'])
def remove_member(request, house_id, member_id):
    is_owner = HouseMember.objects.filter(
        user=request.user,
        house_id=house_id,
        role="owner"
    ).exists()

    if not is_owner:
        return Response({"error": "Not authorized"}, status=403)

    HouseMember.objects.filter(
        id=member_id,
        house_id=house_id
    ).exclude(role="owner").delete()

    return Response({"deleted": True}, status=200)


# 
@api_view(["POST"])
def create_house(request):
    code = unique_code()
    user = request.user
    new_house_name = request.data.get('house_name')

    # check if house name matches any of the user current houses
    house = House.objects.filter(owner=user, name__iexact=new_house_name).exists()
    if house:
        return Response({"error": "House name already exists"}, status=400)

    # create new house and member objects
    house = House.objects.create(name = new_house_name, invite_code = code, owner = user)
    HouseMember.objects.create(role="owner", user=user, house=house)

    return Response({"success": True}, status=200)


#
@api_view(["PUT"])
def edit_house(request):
    user = request.user
    house_id = request.data.get('id')
    new_house_name = request.data.get('name')

    # check if new house name matches, including (My House, my house, MY HOUSE) with __iexact
    house = House.objects.filter(owner=user, name__iexact=new_house_name).exclude(id=house_id).exists()
    if house:
        return Response({"error": "House name already exists"}, status=400)
   
    # update database with new house name
    house = House.objects.get(id=house_id, owner=user)
    house.name = new_house_name
    house.save()

    return Response({"message": "House name changed successfully"})


#
@api_view(['DELETE'])
def delete_house(request, house_id):
    house = House.objects.get(owner=request.user, id=house_id)

    house.delete()

    return Response({"message": True}, status=200)


# Join house with invite code
@api_view(['POST'])
def join_house (request):
    code = request.data.get('invite_code')

     # check if invite code exists
    house = House.objects.filter(invite_code=code).first()                         
    if not house:
        return Response({"error": "Invalid invite code"}, status=400)
    
    # check if user already joined the house
    member = HouseMember.objects.filter(user=request.user, house=house).exists()
    if member:
        return Response({"error": "Already a member"}, status=400)   
    
    # add user to house
    HouseMember.objects.create(
        house = house,
        user = request.user,
        role = "member"
    )

    return Response({"message": "Joined successfully"}, status=201)


# 
@api_view(['DELETE'])
def leave_house(request, house_id):

    house_member = HouseMember.objects.filter(user=request.user, house=house_id)

    house_member.delete()

    return Response({"helloo"})
