"""Resolve a category subtree without one query per descendant."""
from collections import defaultdict

from products.models import Category


def category_subtree_ids(slug):
    rows = list(Category.objects.values_list("id", "parent_id", "slug"))
    children = defaultdict(list)
    root_id = None
    for category_id, parent_id, category_slug in rows:
        children[parent_id].append(category_id)
        if category_slug == slug:
            root_id = category_id
    if root_id is None:
        return []
    visited = set()
    pending = [root_id]
    while pending:
        category_id = pending.pop()
        if category_id in visited:
            continue
        visited.add(category_id)
        pending.extend(children[category_id])
    return sorted(visited)
