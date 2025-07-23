from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import SignUpForm



def home(request):

    # فیلتر با دسته یا تگ
        
    context = {}
    
    return render(request, 'core/home.html', context)







def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            next_url = request.GET.get('next') or 'products:product_list'
            return redirect(next_url)
              
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

def login_view(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next') or 'products:root_product'
            
            return redirect("products:root_product")
        else:
            return render(request, 'core/login.html', {'error': 'نام کاربری یا رمز اشتباه است'})
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('products:root_product')
