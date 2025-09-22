# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CustomersCustomer(models.Model):
    id = models.BigAutoField(primary_key=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.OneToOneField(AuthUser, models.DO_NOTHING)
    level = models.ForeignKey('CustomersCustomerlevel', models.DO_NOTHING, blank=True, null=True)
    avatar = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customers_customer'


class CustomersCustomeraddress(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    customer = models.ForeignKey(CustomersCustomer, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'customers_customeraddress'


class CustomersCustomerguarantee(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    customer = models.ForeignKey(CustomersCustomer, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'customers_customerguarantee'


class CustomersCustomerlevel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    max_credit = models.DecimalField(max_digits=12, decimal_places=2)
    benefit_percent = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'customers_customerlevel'


class CustomersCustomerstate(models.Model):
    id = models.BigAutoField(primary_key=True)
    updated_at = models.DateTimeField()
    customer = models.OneToOneField(CustomersCustomer, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'customers_customerstate'


class CustomersCustomerstateStatuses(models.Model):
    id = models.BigAutoField(primary_key=True)
    customerstate = models.ForeignKey(CustomersCustomerstate, models.DO_NOTHING)
    status = models.ForeignKey('CustomersStatus', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'customers_customerstate_statuses'
        unique_together = (('customerstate', 'status'),)


class CustomersOtp(models.Model):
    id = models.BigAutoField(primary_key=True)
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField()
    session_id = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = 'customers_otp'


class CustomersStatus(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=30)
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customers_status'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class InventoryInventorymovement(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=20)
    quantity = models.IntegerField()
    created_at = models.DateTimeField()
    product_variant = models.ForeignKey('ProductsProductvariant', models.DO_NOTHING)
    related_order = models.ForeignKey('OrdersOrder', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'inventory_inventorymovement'


class OrdersCart(models.Model):
    id = models.BigAutoField(primary_key=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders_cart'


class OrdersCartitem(models.Model):
    id = models.BigAutoField(primary_key=True)
    quantity = models.PositiveIntegerField()
    added_at = models.DateTimeField()
    cart = models.ForeignKey(OrdersCart, models.DO_NOTHING)
    variant = models.ForeignKey('ProductsProductvariant', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'orders_cartitem'


class OrdersOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    status = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'orders_order'


class OrdersOrderitem(models.Model):
    id = models.BigAutoField(primary_key=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    order = models.ForeignKey(OrdersOrder, models.DO_NOTHING)
    variant = models.ForeignKey('ProductsProductvariant', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'orders_orderitem'


class OrdersSalessummary(models.Model):
    id = models.BigAutoField(primary_key=True)
    period_start = models.DateField()
    period_end = models.DateField()
    total_quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    product = models.ForeignKey('ProductsProduct', models.DO_NOTHING)
    variant = models.ForeignKey('ProductsProductvariant', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders_salessummary'
        unique_together = (('product', 'variant', 'period_start', 'period_end'),)


class PaymentsInstallmentpayment(models.Model):
    id = models.BigAutoField(primary_key=True)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.IntegerField()
    paid_at = models.DateTimeField(blank=True, null=True)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2)
    plan = models.ForeignKey('PaymentsInstallmentplan', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'payments_installmentpayment'


class PaymentsInstallmentplan(models.Model):
    id = models.BigAutoField(primary_key=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    months = models.PositiveIntegerField()
    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    created_at = models.DateTimeField()
    order = models.OneToOneField(OrdersOrder, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'payments_installmentplan'


class PaymentsPayment(models.Model):
    id = models.BigAutoField(primary_key=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=30)
    tracking_code = models.CharField(max_length=100, blank=True, null=True)
    proof_image = models.CharField(max_length=100, blank=True, null=True)
    is_successful = models.IntegerField()
    paid_at = models.DateTimeField()
    order = models.ForeignKey(OrdersOrder, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'payments_payment'


class ProductsAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'products_attribute'


class ProductsAttributevalue(models.Model):
    id = models.BigAutoField(primary_key=True)
    value = models.CharField(max_length=50)
    attribute = models.ForeignKey(ProductsAttribute, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products_attributevalue'


class ProductsCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.CharField(unique=True, max_length=50)
    image = models.CharField(max_length=100, blank=True, null=True)
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products_category'


class ProductsProduct(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    slug = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    category = models.ForeignKey(ProductsCategory, models.DO_NOTHING, blank=True, null=True)
    quantity = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'products_product'


class ProductsProductTags(models.Model):
    id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(ProductsProduct, models.DO_NOTHING)
    tag = models.ForeignKey('ProductsTag', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products_product_tags'
        unique_together = (('product', 'tag'),)


class ProductsProductimage(models.Model):
    id = models.BigAutoField(primary_key=True)
    image = models.CharField(max_length=100, blank=True, null=True)
    source_url = models.CharField(unique=True, max_length=200, blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_main = models.IntegerField()
    created_at = models.DateTimeField()
    product = models.ForeignKey(ProductsProduct, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products_productimage'


class ProductsProductspecification(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=655)
    product = models.ForeignKey(ProductsProduct, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products_productspecification'


class ProductsProductvariant(models.Model):
    id = models.BigAutoField(primary_key=True)
    sku = models.CharField(unique=True, max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    stock = models.PositiveIntegerField()
    low_stock_threshold = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    product = models.ForeignKey(ProductsProduct, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products_productvariant'


class ProductsProductvariantAttributes(models.Model):
    id = models.BigAutoField(primary_key=True)
    productvariant = models.ForeignKey(ProductsProductvariant, models.DO_NOTHING)
    attributevalue = models.ForeignKey(ProductsAttributevalue, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products_productvariant_attributes'
        unique_together = (('productvariant', 'attributevalue'),)


class ProductsProductvideo(models.Model):
    id = models.BigAutoField(primary_key=True)
    video = models.CharField(max_length=100)
    caption = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    product = models.ForeignKey(ProductsProduct, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products_productvideo'


class ProductsSpecialproduct(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.IntegerField()
    product = models.OneToOneField(ProductsProduct, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products_specialproduct'


class ProductsTag(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    slug = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'products_tag'


class PromotionsBanner(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    image = models.CharField(max_length=100)
    link = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'promotions_banner'


class ScrapAbdisitePricehistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    price = models.BigIntegerField()
    checked_at = models.DateTimeField()
    watched_url = models.ForeignKey('ScrapAbdisiteWatchedurl', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'scrap_abdisite_pricehistory'


class ScrapAbdisiteWatchedurl(models.Model):
    id = models.BigAutoField(primary_key=True)
    url = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    created_at = models.DateTimeField()
    last_checked = models.DateTimeField()
    product = models.ForeignKey(ProductsProduct, models.DO_NOTHING, blank=True, null=True)
    supplier = models.ForeignKey('SuppliersSupplier', models.DO_NOTHING)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'scrap_abdisite_watchedurl'


class SuppliersSupplier(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    website = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'suppliers_supplier'
