# orders/management/commands/cleanup_carts.py
# (اول پوشه management/commands رو بسازید)

from django.core.management.base import BaseCommand
from orders.models import Cart
from django.db.models import Count

class Command(BaseCommand):
    help = 'پاکسازی سبدهای خرید تکراری'
    
    def handle(self, *args, **options):
        self.stdout.write('شروع پاکسازی سبدهای خرید...')
        
        # پاکسازی سبدهای تکراری کاربران
        duplicate_users = Cart.objects.filter(
            user__isnull=False
        ).values('user').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for dup in duplicate_users:
            user_id = dup['user']
            carts = Cart.objects.filter(user_id=user_id).order_by('created_at')
            
            # اولین کالت رو نگه دار، بقیه رو پاک کن
            main_cart = carts.first()
            for cart in carts[1:]:
                # انتقال آیتم‌ها به کالت اصلی
                for item in cart.items.all():
                    item.cart = main_cart
                    item.save()
                cart.delete()
                self.stdout.write(f'  - کالت تکراری کاربر {user_id} پاک شد')
        
        # پاکسازی سبدهای تکراری session_key
        duplicate_sessions = Cart.objects.filter(
            session_key__isnull=False
        ).values('session_key').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for dup in duplicate_sessions:
            session_key = dup['session_key']
            carts = Cart.objects.filter(session_key=session_key).order_by('created_at')
            
            main_cart = carts.first()
            for cart in carts[1:]:
                for item in cart.items.all():
                    item.cart = main_cart
                    item.save()
                cart.delete()
                self.stdout.write(f'  - کالت تکراری session {session_key} پاک شد')
        
        self.stdout.write(self.style.SUCCESS('پاکسازی با موفقیت انجام شد!'))