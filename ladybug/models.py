from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
from django.core.exceptions import ValidationError



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=200, blank=True, unique=True)
    mobile = models.CharField(max_length=10, blank=True, unique=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    # address = models.CharField(max_length=200, blank=True, null=True)
    building = models.CharField(max_length=255, blank=True, null=True)
    house = models.CharField(max_length=255, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    userGroup = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    mobileAuthenticated = models.BooleanField(default=False)
    otp = models.IntegerField(blank=True, null=True)
    last_otp_resend = models.DateTimeField(null=True, blank=True)
    n_otps_sent_day = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# models.py...
class MeasurementField(models.Model):
    name = models.CharField(max_length=100)  # e.g., "bust", "waist"
    description = models.TextField()
    image = models.ImageField(upload_to='measurement_guides/')
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
# Main chart entity
class SizeChart(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., "Chart A"
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Define body parameters in each chart (e.g., bust, waist)
class SizeParameter(models.Model):
    chart = models.ForeignKey(SizeChart, related_name='parameters', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # e.g., "Waist", "Bust"

    def __str__(self):
        return f"{self.chart.name} - {self.name}"

# Define size labels in each chart (e.g., XS, M, XL)
class SizeLabel(models.Model):
    chart = models.ForeignKey(SizeChart, related_name='sizes', on_delete=models.CASCADE)
    label = models.CharField(max_length=50)  # e.g., "S", "M", "XL"

    def __str__(self):
        return f"{self.chart.name} - {self.label}"

# Store the value of each parameter for each size in a chart
class SizeValue(models.Model):
    chart = models.ForeignKey(SizeChart, related_name='values', on_delete=models.CASCADE)
    size = models.ForeignKey(SizeLabel, on_delete=models.CASCADE)
    parameter = models.ForeignKey(SizeParameter, on_delete=models.CASCADE)
    value = models.FloatField()  # or DecimalField for precision

    class Meta:
        unique_together = ('chart', 'size', 'parameter')

    def __str__(self):
        return f"{self.chart.name} - {self.size.label} - {self.parameter.name}: {self.value}"

class Category(models.Model):
    category = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.category

class CommonInformation(models.Model):
    name = models.CharField(null=True, blank=True)
    return_exchange_policy = models.TextField(null=True, blank=True)
    manufacturing_info = models.TextField(null=True, blank=True)
    highlights = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class Tag(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    additional_perc_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # % discount
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Maximum Amount Rs.
    
    def __str__(self):
        return self.name

class FabricCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Model to store Fabric options
class Fabric(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    Common_iformation = models.ForeignKey(CommonInformation, on_delete=models.SET_NULL, null=True, blank=True)
    tag = models.ManyToManyField(Tag, related_name='fabrics', blank=True)
    category = models.ForeignKey(FabricCategory, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    units_inStock = models.PositiveIntegerField(default=0)
    units_sold = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name

# Model to store multiple images of fabric
class FabricImage(models.Model):
    fabric = models.ForeignKey(Fabric, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='fabrics/images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fabric.name} - {self.id}"



# models.py...
class Measurement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field = models.ForeignKey(MeasurementField, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=5, decimal_places=2)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.field.name}: {self.value}"


class PatternOption(models.Model):
    FIELD_TYPES = [
        ('bool', 'Yes/No'),
        ('choice', 'Dropdown'),
        ('text', 'Text'),
        ('float', 'Decimal Number'),
    ]

    name = models.CharField(max_length=100)  # e.g., "Cup", "Hooks"
    description = models.TextField()
    image = models.ImageField(upload_to='measurement_guides/')
    
    field_type = models.CharField(max_length=10, choices=FIELD_TYPES, default='text')
    choices = models.TextField(blank=True, null=True, help_text="Comma-separated choices for dropdowns.")
    default_value = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class Pattern(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    required_measurements = models.ManyToManyField(MeasurementField, related_name='patterns')
    required_options = models.ManyToManyField(PatternOption, related_name='patterns')
    tag = models.ManyToManyField(Tag, related_name='patterns', blank=True)
    size_chart = models.ForeignKey(SizeChart, on_delete=models.SET_NULL, null=True, blank=True)
    Category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    units_sold = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name

# Model to store Product options
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    Common_iformation = models.ForeignKey(CommonInformation, on_delete=models.SET_NULL, null=True, blank=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.SET_NULL, null=True)
    pattern = models.ForeignKey(Pattern, on_delete=models.SET_NULL, null=True)
    Category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tag = models.ManyToManyField(Tag, related_name='products', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    units_inStock = models.PositiveIntegerField(default=0)
    units_sold = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    required_measurements = models.ManyToManyField(MeasurementField, related_name='products', blank=True)
    size_chart = models.ForeignKey(SizeChart, on_delete=models.SET_NULL, null=True, blank=True)
    views = models.PositiveIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name


# Model to store multiple images of a product
class ProductImage(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ]
        
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='image')
    image = models.ImageField(upload_to='products/images/', blank=True, null=True)
    video = models.FileField(upload_to='products/images/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='products/images/', blank=True, null=True,
                                  help_text="Used for video preview.")
    
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.media_type} - {self.id}"


# Model to store multiple images of patterns
class PatternImage(models.Model):
    pattern = models.ForeignKey(Pattern, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='patterns/images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pattern.name} - {self.id}"


# Cart
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', null=True, blank=True, on_delete=models.SET_NULL)
    fabric = models.ForeignKey('Fabric', null=True, blank=True, on_delete=models.SET_NULL)
    pattern = models.ForeignKey('Pattern', null=True, blank=True, on_delete=models.SET_NULL)
    own_fabric = models.BooleanField(default=False)
    arrange_pickup = models.BooleanField(default=False)
    options = models.JSONField(blank=True, null=True)
    measurements = models.JSONField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True )
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart #{self.id} - {self.user.username}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Order Placed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ]

    PAYMENT_CHOICES = [
        ('failed', 'Failed'),
        ('paid', 'Paid'),
        ('cashondelivery', 'Cash On Delivery'),
        ]
    
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    order_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='failed')

    # Per-order address 
    building = models.CharField(max_length=255, blank=True, null=True)
    house = models.CharField(max_length=255, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=10, blank=True, null=True)

    delivered = models.BooleanField(default=False)
    review_sent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        send_email = False
        from .views import send_review_email 
        if self.pk:
            # Check if delivered status changed to True
            old = Order.objects.get(pk=self.pk)
            if not old.delivered and self.delivered and not self.review_sent:
                send_email = True

        super().save(*args, **kwargs)

        if send_email:
            send_review_email(self)
            self.review_sent = True
            super().save(update_fields=['review_sent'])


    def __str__(self):
        return f"Order #{self.id} - {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)
    fabric = models.ForeignKey('Fabric', on_delete=models.SET_NULL, null=True, blank=True)
    pattern = models.ForeignKey('Pattern', on_delete=models.SET_NULL, null=True, blank=True)
    own_fabric = models.BooleanField(default=False)
    arrange_pickup = models.BooleanField(default=False)
    options = models.JSONField(blank=True, null=True)
    measurements = models.JSONField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)

    # NEW: fields for "pattern not in DB"
    custom_pattern = models.BooleanField(default=False)
    custom_pattern_name = models.CharField(max_length=255, blank=True, null=True)
    custom_style_notes = models.TextField(blank=True, null=True)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Item #{self.id} of Order #{self.order.id}"
        

class ProductReview(models.Model):
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)
    fabric = models.ForeignKey('Fabric', on_delete=models.SET_NULL, null=True, blank=True)
    pattern = models.ForeignKey('Pattern', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    reviewer = models.ForeignKey('Profile', on_delete=models.SET_NULL, null=True)
    rating = models.PositiveIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    image = models.ImageField(upload_to='review_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    review_token = models.CharField(max_length=100, unique=True)
    is_submitted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Compress image if present
        if self.image:
            img = Image.open(self.image)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            output = BytesIO()
            img.save(output, format='JPEG', quality=70)
            output.seek(0)
            self.image = ContentFile(output.read(), self.image.name)

        super().save(*args, **kwargs)

class CarouselImage(models.Model):
    image = models.ImageField(upload_to='carousel/')
    caption = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class cardImages(models.Model):
    CHOICES = [
        ('own_fabric', 'own_fabric'),
        ('purchase_fabric', 'purchase_fabric'),
        ('pickup', 'pickup'),
        ('drop', 'drop'),
        ('create_style_card', 'create_style_card')
    ]
    name = models.CharField(max_length=50, choices=CHOICES, default='create_style_card')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='card_images/', blank=True, null=True)

class SiteHit(models.Model):
    date = models.DateField(auto_now_add=True)
    count = models.PositiveIntegerField(default=0)



class FlatDiscount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('amount', 'Flat Amount'),
        ('percent', 'Percentage'),
    ]

    is_active = models.BooleanField(default=False)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)

    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        # Ensure proper value is provided for selected type
        if self.discount_type == 'amount':
            if not self.amount:
                raise ValidationError("Amount is required for flat discount.")
            if self.percent:
                raise ValidationError("Percentage must be empty when using flat amount.")
        elif self.discount_type == 'percent':
            if not self.percent:
                raise ValidationError("Percentage is required for percent discount.")
            if self.amount:
                raise ValidationError("Flat amount must be empty when using percentage.")


    def is_valid(self):
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date


    def get_discount(self, total):
        if not self.is_valid():
            return 0
        if self.discount_type == 'amount':
            return min(self.amount or 0, total)
        elif self.discount_type == 'percent':
            return total * (self.percent or 0) / 100
        return 0


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class WalletTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(choices=[('credit', 'Credit'), ('debit', 'Debit')], max_length=10)
    description = models.CharField(max_length=255)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)


