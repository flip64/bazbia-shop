from django.shortcuts import render,redirect
from django.shortcuts import  get_object_or_404
from .models import Product, Category, Tag
from .forms import CategoryForm
from promotions.models import Banner



# ==============================
# ویو های مربوط به محصولات (Category)
# ==============================

def product_list(request):
    products = Product.objects.all()

    # فیلتر با دسته یا تگ
    category_slug = request.GET.get('category')
    tag_slug = request.GET.get('tag')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if tag_slug:
        products = products.filter(tags__slug=tag_slug)
    categories = Category.objects.filter(parent__isnull=True)
    banners = Banner.objects.all()

    context = {
        'products': products ,
        'show_banner': True,
        'categories': categories,
        'baners' : banners
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












# ==============================
# ویو های مربوط به دسته بندی (Category)
# ==============================

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'products/category_detail.html', {
        'category': category,
        'products': products
    })





def category_list(request):
    print("ok")
    top_categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'products/category_list.html', {'categories': top_categories})

def category_create(request):
    form = CategoryForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('products:category_list')
    return render(request, 'products/category_form.html', {'form': form})

def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('products:category_list')
    return render(request, 'products/category_form.html', {'form': form})
