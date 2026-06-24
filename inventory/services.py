from inventory.models import HistoryLog

#
def destock_activity_log(item, old_quantity, new_quantity, user_id):
    HistoryLog.objects.create(
        item=item,
        house=item.house,
        user_id=user_id,
        action='destock',
        old_quantity=old_quantity,
        new_quantity=new_quantity,
        note='Barcode scan'
    )
