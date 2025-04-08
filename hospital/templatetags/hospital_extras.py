from django import template

register = template.Library()

@register.filter
def get_item(queryset, item_id):
    try:
        return queryset.get(id=item_id)
    except:
        return None 