from django.contrib import admin
from .models import (Fabric, FabricImage, Pattern, PatternImage, Product, 
                     ProductImage, Order, Measurement, MeasurementField, 
                     Pattern, Profile, PatternOption, SizeChart, SizeParameter,
                     SizeLabel, SizeValue, Pattern, Category, Cart, CommonInformation,
                     ProductReview, CarouselImage, Tag, cardImages, SiteHit, FlatDiscount,
                     Wallet, WalletTransaction, FabricCategory, OrderItem)

from .views import send_review_email  # or wherever your function is defined
from django.contrib import messages

# Inline for fabric images
class FabricImageInline(admin.TabularInline):
    model = FabricImage
    extra = 1

@admin.register(Fabric)
class FabricAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    inlines = [FabricImageInline]

# Inline for pattern images
class PatternImageInline(admin.TabularInline):
    model = PatternImage
    extra = 1


# Inline for product images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'fabric', 'pattern', 'price', 'created_at', 'views')
    inlines = [ProductImageInline]


@admin.action(description="Resend review email to selected users")
def resend_review_email(modeladmin, request, queryset):
    count = 0
    for order in queryset:
        if order.delivered:
            send_review_email(order, resend=True)
            count += 1
    messages.success(request, f"Sent review email for {count} delivered orders.")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'order_date', 'delivered', 'review_sent')
    list_filter = ('status', 'order_date', 'delivered', 'review_sent')
    search_fields = ('user', 'order_date')
    actions = [resend_review_email]



@admin.register(MeasurementField)
class MeasurementFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(PatternOption)
class PatternOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# Inline for pattern images
class ProductImageInline(admin.TabularInline):
    model = PatternImage
    extra = 1

@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('required_measurements',)  # For many-to-many field
    inlines = [PatternImageInline]

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('user', 'field', 'value', 'updated_on')
    list_filter = ('field', 'updated_on')
    search_fields = ('user__username', 'field__name')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'mobile', 'created_at')

admin.site.register(SizeChart)
admin.site.register(SizeParameter)
admin.site.register(SizeLabel)
admin.site.register(SizeValue)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CommonInformation)
admin.site.register(ProductImage)
admin.site.register(FabricImage)

@admin.register(cardImages)
class cardImagesAdmin(admin.ModelAdmin):
    list_display = ('name', 'image')

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'is_submitted')

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('alt_text', 'image', 'order')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'additional_perc_discount', 'max_discount')

@admin.register(SiteHit)
class TagAdmin(admin.ModelAdmin):
    list_display = ('date', 'count')


@admin.register(FlatDiscount)
class FlatDiscountAdmin(admin.ModelAdmin):
    list_display = ('amount', 'percent', 'start_date', 'end_date', 'is_active')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'timestamp')

admin.site.register(FabricCategory)

admin.site.register(OrderItem)