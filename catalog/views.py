from django.shortcuts import render

from .models import Category, Product, Tag


def product_list(request):
    """Search and filter products.

    Reads the GET parameters produced by the form on the page:
      - ``q``        : free-text search against the product description
      - ``category`` : a single category id to filter by
      - ``tags``     : zero or more tag ids to filter by (OR semantics)

    The filters are applied as a chain, so any combination of them narrows
    the result set together.
    """
    products = Product.objects.select_related('category').prefetch_related('tags')

    # Search by description.
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(description__icontains=query)

    # Filter by category. Ignore non-numeric values so a malformed query
    # parameter (e.g. ?category=abc) can't raise a ValueError.
    category_id = request.GET.get('category', '').strip()
    if category_id.isdigit():
        products = products.filter(category_id=category_id)
    else:
        category_id = ''

    # Filter by tags: match products having ANY of the selected tags.
    # Keep only valid integer ids; drop anything non-numeric.
    selected_tag_ids = [tid for tid in request.GET.getlist('tags') if tid.isdigit()]
    if selected_tag_ids:
        products = products.filter(tags__in=selected_tag_ids).distinct()

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'tags': Tag.objects.all(),
        # Echo current selections back so the form keeps its state.
        'query': query,
        'selected_category': category_id,
        'selected_tag_ids': {int(tid) for tid in selected_tag_ids},
    }
    return render(request, 'catalog/product_list.html', context)
