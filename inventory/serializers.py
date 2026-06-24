from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Item, Category, HistoryLog


# 
class ItemSerializer(serializers.ModelSerializer):
    # remove comma in price before validation
    def to_internal_value(self, data):
        data = data.copy()                                      # avoid mutating original request data
        if data.get('price'):
            data["price"] = data["price"].replace(",","")       # remove comma and assign converted price back
        return data                                             # return full dict (into DRF for validation below)


    class Meta:
        model = Item
        fields = ['id', 'barcode', 'name',  'description', 'price', 'quantity', 'min_limit', 'category']


    # custom validation against item specific house, using barcode (contains intermediate validated data)
    def validate(self, attrs):
        barcode = attrs.get('barcode')
        house = attrs.get('house')

        # check if item barcode exists in that house
        item = Item.objects.filter(barcode=barcode, house=house).exists() 
        if item:
           raise serializers.ValidationError({"error": "Item with barcode already exists for this house"})

        return attrs
    
    # 
    def create(self, validated_data):
        # remove both ids
        validated_data.pop("house", None)
        validated_data.pop("category", None)

        # use the objects sent in context
        house = self.context["house"]
        category = self.context['category']

        return Item.objects.create(house=house, category=category, **validated_data)


# 
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'house']

        validators = [UniqueTogetherValidator(queryset=Category.objects.all(),
        fields= ['name', 'house'],
        message="Category already exists in this house"
        )]
    
    def validate(self, attrs):
        name = attrs.get('name')
        house = attrs.get('house')
        if Category.objects.filter(name=name, house=house).exists():
            raise serializers.ValidationError({"name": "Category already exists"})
        
        return attrs
    
# 
class HistoryLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    
    class Meta:
        model = HistoryLog
        fields = '__all__' 
        