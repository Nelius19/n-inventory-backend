from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Item, Category, HistoryLog
from house.models import House, HouseMember
from .serializers import ItemSerializer, CategorySerializer, HistoryLogSerializer
from django.db.models import Q
from django.db.models import F
from .services import destock_activity_log
from notifications.services import check_low_stock_notification


# Add item if barcode exist in current user house
@api_view(['POST'])
def scan_item(request):
    barcode = request.data.get("barcode")
    house_id = request.data.get("current_house")
    new_qty = int(request.data.get("quantity"))
    
    # Check if an item barcode exists in current house
    item = Item.objects.filter(barcode=barcode, house=house_id).exists()
    if not item:
        return Response({"exists": False, "error": "Item does not exists"}, status=404)
    
    # If item exist in house, update the item quantity
    house = request.user.houses.get(id=house_id)
    house_item = house.items.get(barcode=barcode)
    house_item.quantity += new_qty
    house_item.save()

    return Response({"message": "Updated successfully"}, status=200)    


# Create new item for current user house
@api_view(['POST'])
def create_item(request):
    house = request.user.houses.get(pk=request.data.get('house'))       # get current user house object
    category = house.categories.get(pk=request.data.get('category'))    # get selected category object

    # pass them as extra data in context (foreign keys)
    serializer = ItemSerializer( data=request.data, context={"house": house, "category": category})  

    # if data is valid, save to database
    if serializer.is_valid():
        serializer.save()
        return Response({"success": True}, status=201)
    return Response(serializer.errors, status=400)


# Fetch items per house
@api_view(['GET'])
def fetch_items(request, house_id):
    items = Item.objects.filter(
        house_id=house_id
        ).filter(
            Q(house__owner=request.user) |
            Q(house__members__user=request.user)
        ).distinct()

    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=200)


# 
@api_view(['POST'])
def destock_item(request, house_id):
    
    barcode = request.data.get('barcode')

    # check if user is a member of the house being access
    membership = HouseMember.objects.filter(user=request.user, house_id=house_id).first()
    if not membership:
        return Response({"error": "Invalid House"}, status=400)

    # Get item object of selected house
    item = Item.objects.filter(barcode=barcode, house_id=house_id).first()
    if not item:
        return Response({"error": "Item not found in house"}, status=404)
    
    # Check item quantity
    if item.quantity <= 0:
        return Response({"error" : "Out of stock"}, status=400)

    old_quantity = item.quantity

    # Reduce quantity and save
    item.quantity -= 1
    item.save(update_fields=['quantity'])

    new_quantity = item.quantity

    destock_activity_log(item, old_quantity, new_quantity, request.user.id)    # pass data to services.py
    check_low_stock_notification(request.user, item)

    return Response({"destock": True}, status=200)


# Edit item
@api_view(['PUT'])
def edit_item(request, item_id):

    # get object of an item belonging to a user/house and update the item details
    item = Item.objects.get(pk=item_id, house__owner=request.user)
    category = item.house.categories.get(pk=request.data['category']) 
    
    serializer = ItemSerializer(item, data=request.data, partial=True)

    if serializer.is_valid(raise_exception=True):
        serializer.save(category=category)
        return Response({"updated": True}, status=200)
    return Response(serializer.errors, 400)


#   Delete item
@api_view(['DELETE'])
def delete_item(request, item_id):
    item = Item.objects.get(pk=item_id, house__owner=request.user)
    
    item.delete()

    return Response({"deleted": True}, status=200)


# create category per house
@api_view(['POST'])
def create_category(request):
    serializer = CategorySerializer(data=request.data)

    # Get the selected house that belongs to the logged-in user
    house = request.user.houses.get(id=request.data.get("house"))
    if serializer.is_valid():
        serializer.save(house=house)                    # Save category name plus extra data user house id
        return Response(serializer.data, status=201)    # Convert obj to python dict to json response
    print(serializer.errors)
    return Response(serializer.errors, status=400)
    

# fetch category per house
@api_view(['GET'])
def fetch_categories (request):
    house_id = request.query_params.get('id')

    house = request.user.houses.get(id=house_id)                # Get user houses link with foreign key
    categories = house.categories.all()                         # Get all item categories for that house
    serializer = CategorySerializer(categories, many=True)      # many=true return an array of objects

    return Response(serializer.data, status=200)


#
@api_view(['PUT'])
def edit_category(request, category_id, house_id):

    new_category = request.data.get("category")
    
    # check if new category name is exactly in user house
    if Category.objects.filter(name__iexact=new_category, house_id=house_id).exclude(id=category_id).exists():
        return Response({"error": f"'{new_category}' already exists for this house"}, status=400)

    # update database with new category name
    category = Category.objects.get(id=category_id, house_id=house_id)
    category.name = new_category
    category.save()

    return Response({"success": "Name changed successfully"}, status=200)


#1539
@api_view(['DELETE'])
def delete_category(request, category_id, house_id):
    category = Category.objects.get(id=category_id, house_id=house_id)

    category.delete()

    return Response({"delete": "Deleted"}, status=200)


#
@api_view(['GET'])
def fetch_item_history(request, house_id):
    history_log = HistoryLog.objects.filter(house_id=house_id).select_related('user', 'item', 'house')    

    serializer = HistoryLogSerializer(history_log, many=True)

    return Response(serializer.data, status=200)
