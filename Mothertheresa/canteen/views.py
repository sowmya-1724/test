from django.shortcuts import render, get_object_or_404
from .models import item


def item_list(request):
    ob_items = item.objects.all()
    return render(request, 'item_list.html', {'items': ob_items})

def item_detail(request, pk):
    ob_item = get_object_or_404(item, pk=pk)
    return render(request, 'item_detail.html', {'item': ob_item})
