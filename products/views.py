from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Product, Category, Tag


def product_list(request):
    products = Product.objects.filter(is_active=True)

    # فیلتر با دسته یا تگ
    category_slug = request.GET.get('category')
    tag_slug = request.GET.get('tag')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if tag_slug:
        products = products.filter(tags__slug=tag_slug)
    categories = Category.objects.filter(parent__isnull=True)
    context = {
        'products': products ,
        'show_banner': True,
        'categories': categories

    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = product.variants.all()
    specifications = product.specifications.all()
    images = product.images.all()
    videos = product.videos.all()

    context = {
        'product': product,
        'variants': variants,
        'specifications': specifications,
        'images': images,
        'videos': videos
    }
    return render(request, 'products/product_detail.html', context)

from django.shortcuts import render, get_object_or_404


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'products/category_detail.html', {
        'category': category,
        'products': products
    })


def home(request):
    products = Product.objects.filter(is_active=True)

    # فیلتر با دسته یا تگ
    category_slug = request.GET.get('category')
    tag_slug = request.GET.get('tag')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if tag_slug:
        products = products.filter(tags__slug=tag_slug)

    context = {
        'products': products ,
        'show_banner': True,
        

    }
    return render(request, 'core/home.html', context)

