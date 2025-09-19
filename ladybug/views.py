from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import *
from .forms import *
import math, random
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import logout, login
from django.utils.timezone import now, timedelta
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from collections import defaultdict
import uuid
from django.db.models import Avg, Q, Count
from django.db.models import F
from decimal import Decimal
import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from .forms import AdminOrderCustomerForm, AdminOrderItemFormSet
from django.views.decorators.http import require_POST

def calculate_final_price(base_price, original_price=None, flat_discount=None):
    """
    Calculates the final price after applying flat discount (if better).
    
    Args:
        base_price (Decimal): The already discounted price of the item.
        original_price (Decimal or None): The original price (before any product discount).
        flat_discount (FlatDiscount instance or None): The flat discount object.

    Returns:
        dict: {
            'final_price': Decimal,
            'discount_applied': bool,
            'discount_amount': Decimal,
            'base_price': Decimal,
            'original_price': Decimal
        }
    """
    original_price = original_price or base_price
    final_price = base_price
    discount_applied = False
    discount_amount = Decimal('0.00')

    if flat_discount and flat_discount.is_valid():
        temp_discount = flat_discount.get_discount(original_price)
        discounted_price = original_price - temp_discount

        if discounted_price < base_price:
            final_price = discounted_price
            discount_applied = True
            discount_amount = temp_discount

    return {
        'final_price': final_price,
        'discount_applied': discount_applied,
        'discount_amount': discount_amount,
        'base_price': base_price,
        'original_price': original_price
    }


# def home(request):
#     images = CarouselImage.objects.all()
#     categories = Category.objects.all()
#     create_style_card = cardImages.objects.get(name = 'create_style_card')

#     products = Product.objects.annotate(
#         average_rating=Avg('productreview__rating', filter=Q(productreview__is_submitted=True)),
#         total_reviews=Count('productreview', filter=Q(productreview__is_submitted=True))).all()

#     products_by_view = products.order_by('-views')[0:3]
#     products_by_date = products.order_by('-created_at').exclude(id__in=products_by_view.values_list('id', flat=True))

#     flat_discount = FlatDiscount.objects.filter(is_active=True).first()

#     for product in products_by_view:
#         pricing = calculate_final_price(
#             base_price=product.price,
#             original_price=product.original_price,
#             flat_discount=flat_discount
#         )
#         product.final_price = pricing['final_price']
#         product.original_price = pricing['original_price']

#     for product in products_by_date:
#         pricing = calculate_final_price(
#             base_price=product.price,
#             original_price=product.original_price,
#             flat_discount=flat_discount
#         )
#         product.final_price = pricing['final_price']
#         product.original_price = pricing['original_price']
    

#     return render(request, 'home.html', {'carousel_images': images,
#                                          'categories': categories,
#                                          'create_style_card': create_style_card,
#                                          'products_by_view': products_by_view,
#                                          'products_by_date': products_by_date})

def home(request):

    return render(request, 'links.html', {})


# REGISTER
def generateOTP():
    digits = '11234567899'
    OTP = ''
    for i in range(6):
        rand_n = digits[math.floor(random.random() * 10) ]
        OTP = ''.join([OTP, rand_n])
    return OTP

def emailOTP(email, otp):
    
    subject = 'LADYBUG - OTP'
    message = f'OTP for Signing-In at LADYBUG is {otp}'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

def register(request):
    if request.method == "POST":
        # Retrieve POST data
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        
        # Address
        building = request.POST.get('building', '')
        house = request.POST.get('house', '')
        street = request.POST.get('street', '')
        area = request.POST.get('area', '')
        city = request.POST.get('city', '')
        pincode = request.POST.get('pincode', '')
        full_address = ", ".join(filter(None, [house, building, street, area, city, pincode]))

        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
        
        if not mobile or len(mobile) != 10 or not mobile.isdigit():
            messages.error(request, "Please enter a valid 10-digit mobile number.")
            
            # return redirect('register')

        # Check if email is already registered
        try:
            existing_profile = Profile.objects.get(mobile=mobile) 
            if not existing_profile.mobileAuthenticated: 
                # Delete incomplete registrations 
                existing_user = existing_profile.user
                existing_profile.delete()
                existing_user.delete()

                user = User.objects.filter(username=mobile)
                user.delete()
            else:
                messages.error(request, "Mobile No. already registered. Please try login.")
                # return redirect('register')
        except Profile.DoesNotExist:
            try: 
                existing_user = User.objects.get(username = mobile, email=email)
                existing_user.delete()
            except:
                pass

            pass
        
        # try:
        # Create User object
        #user_data = User.objects.create_user(username=email, email=email)

        
        user_data = User.objects.create_user(username = mobile, email=email)

        group_type='customer'
        group = Group.objects.get(name = group_type) # Create group if not exists
        user_data.groups.add(group)  # Assign user to the group
        user_data.save()
        
        # Generate OTP
        otp = generateOTP()
        emailOTP(email, otp)  # Send OTP to the user's email
        
        # Create Profile object
        profile_data = Profile(
            email=email,
            mobile = mobile,
            user=user_data,
            name=name,
            building = request.POST.get('building', ''),
            house = request.POST.get('house', ''),
            street = request.POST.get('street', ''),
            area = request.POST.get('area', ''),
            city = request.POST.get('city', ''),
            state = request.POST.get('state', ''),
            zip_code = request.POST.get('pincode', ''),
            userGroup=Group.objects.get(name=group_type),
            mobileAuthenticated=False,
            otp=otp,
        )
        profile_data.save()

        request.session['auth_mobile'] = mobile
        return redirect(f'verify_otp')

    return render(request, template_name="register.html", context={})


def verify_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')  # OTP entered by user
        mobile = request.POST.get('mobile')
        try:
            profile = Profile.objects.get(mobile=mobile)
            if profile.otp == int(otp_entered):
                profile.mobileAuthenticated = True
                profile.save()

                user = User.objects.get(username=mobile) # Get the user by email
                login(request, user)
                
                if request.user.is_authenticated:  # Check if the user is authenticated
                    next_url = request.session.pop('next_url', None)
                    if next_url:
                        next_url = next_url
                        if next_url == reverse('cart'):
                            save_session_data(request)
                    else:
                        next_url = reverse('home')
                    
                    return JsonResponse({'success': 'OTP verified', 'redirect_url': next_url})
                else:
                    return JsonResponse({'error': 'Otp verified but unable to Login'}, status=400)
            else:
                return JsonResponse({'error': 'Invalid OTP. Please try again.'}, status=400)

        except Profile.DoesNotExist:
            return JsonResponse({'error': 'Profile not found.'}, status=404)
    else:
        mobile = request.session.get('auth_mobile')
    return render(request, 'mobile-authentication.html', {'mobile': mobile})


def resend_otp(request):
    if request.method == "POST":
        
        try:
            mobile = request.POST.get('mobile')
            # Fetch the user's profile by email
            profile = Profile.objects.get(mobile=mobile)

            # Check if the user can request another OTP
            if profile.n_otps_sent_day and profile.n_otps_sent_day > 2:
                return JsonResponse({
                    'error': f"You have exceeded your daily OTP request limit"
                }, status=429)
            
            elif profile.last_otp_resend and now() - profile.last_otp_resend < timedelta(minutes=1):
                time_remaining = 60 - (now() - profile.last_otp_resend).seconds
                return JsonResponse({
                    'error': f"Please wait {time_remaining} seconds before requesting another OTP."
                }, status=429)

            # Generate a new OTP
            new_otp = generateOTP()
            # Send the OTP via email
            email = profile.email
            emailOTP(email, new_otp)

            profile.otp = new_otp
            
            if profile.last_otp_resend and profile.last_otp_resend.date() == now().date():
                profile.n_otps_sent_day = profile.n_otps_sent_day + 1
            else:
                profile.n_otps_sent_day = 1

            profile.last_otp_resend = now()

            profile.save()

                # Return success response
            return JsonResponse({'success': 'OTP has been resent to your mobile.'})
        except Profile.DoesNotExist:
            return JsonResponse({'error': 'Profile not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

WHATSAPP_BOT_URL = "https://whatsapp-bot-sr9j.onrender.com"

def login_otp(request):
    if request.method == 'POST':
        mobile = request.POST.get('mobile')

        if Profile.objects.filter(mobile=mobile).exists():
            profile = Profile.objects.get(mobile=mobile)
            if profile.mobileAuthenticated:
                # Generate and send OTP
                otp = generateOTP()
                email = profile.email
                emailOTP(email, otp)
                
                # Send OTP to WhatsApp
                payload = {
                    "number": f"91{mobile}",  # make sure it’s full country code format
                    "message": f"Your OTP is {otp}",
                }
                # try:
                res = requests.post(f"{WHATSAPP_BOT_URL}/send-message", json=payload)
                print("Status:", res.status_code)
                print("Response:", res.text)
                #     if res.status_code != 200:
                #         messages.warning(request, "OTP sent to email, but WhatsApp failed")
                # except Exception as e:
                #     messages.warning(request, f"OTP sent to email, but WhatsApp error: {e}")

                # Store OTP and timestamp in the user's profile
                profile.otp = otp
                profile.save()
                #messages.success(request, 'OTP has been sent to your email')
                return render(request, 'mobile-authentication.html', {'mobile': mobile})
            else:
                messages.error(request, "Mobile No. is not authenticated, please register")
                return redirect('login')
        else:
            messages.error(request, "User ID doesn't exist, please register")
            return redirect('login')
        # messages.success(request, 'OTP has been sent to your email')
        
    return render(request, 'login.html')  # Render the login page template

def user_logout(request):
    logout(request)
    return render(request, 'logout.html')  # Replace 'login' with the URL name of your login page


def select_fabric_option(request):
    fabric_option = request.session.get('own_fabric')
    if fabric_option is None:
        selected_fabric_option = None
    else:
        if fabric_option == True:
            selected_fabric_option = 'own_fabric'
        else:
            selected_fabric_option = 'purchase_fabric'


    if request.method == 'POST':
        option = request.POST.get('category_id')
        
        if option == 'own_fabric':
            request.session['own_fabric'] = True
            request.session['fabric_id'] = None
            return redirect('select-pickup-option')
        else:
            request.session['own_fabric'] = False
            return redirect('select-fabric')

    return render(request, 'select-fabric-option.html', {'selected_fabric_option': selected_fabric_option,
                                                          'own_thumbnails': cardImages.objects.get(name = 'own_fabric'),
                                                         'purchase_thumbnails': cardImages.objects.get(name = 'purchase_fabric')})

def select_pickup_option(request):

    pickup_option = request.session.get('pickup')
    if pickup_option is None:
        selected_pickup_option = None
    else:
        if pickup_option == True:
            selected_pickup_option = 'pickup'
        else:
            selected_pickup_option = 'drop'

    if request.method == 'POST':
        option = request.POST.get('category_id')
        if option == 'pickup':
            request.session['pickup'] = True
        else:
            request.session['pickup'] = False

        return redirect('select-style')

    return render(request, 'select-pickup-option.html', {'selected_pickup_option': selected_pickup_option,
                                                         'pickup_thumbnails': cardImages.objects.get(name = 'pickup'),
                                                         'drop_thumbnails': cardImages.objects.get(name = 'drop')})

def select_category(request):
    categories = Category.objects.annotate(pattern_count=Count('pattern')).filter(pattern_count__gt=0)
    selected_category_id = request.session.get('category_id')
    
    if request.method == 'POST':
        request.session['category_id'] = request.POST.get('category_id')

        return redirect('select-fabric-option')

    return render(request, 'select-category.html', {'categories': categories, 
                                                  'selected_category_id': int(selected_category_id) if selected_category_id else None,
                                                  })


def select_fabric(request):
    # fabrics = Fabric.objects.prefetch_related('images').all()
    # Try to get previously selected fabric - in case going back - it should exists
    
    fabrics = Fabric.objects.prefetch_related('images').annotate(
        average_rating=Avg('productreview__rating', filter=Q(productreview__is_submitted=True)),
        total_reviews=Count('productreview', filter=Q(productreview__is_submitted=True))
        )
    
    selected_fabric_id = request.session.get('fabric_id')
    
    if request.method == 'POST':
        request.session['fabric_id'] = request.POST.get('fabric_id')
        # Safely delete session keys if they exist
        for key in ['pickup', 'own_fabric']:
            if key in request.session:
                del request.session[key]

        return redirect('select-style')

    return render(request, 'select-fabric.html', {'fabrics': fabrics, 
                                                  'selected_fabric_id': int(selected_fabric_id) if selected_fabric_id else None,
                                                  })


def get_similar_products(request):
    fabric_id = request.GET.get('fabric_id')
    products_data = []
    
    if fabric_id:
        fabric = Fabric.objects.get(id=fabric_id)
        products = Product.objects.filter(fabric=fabric)
        for p in products:
            images = [img.image.url for img in p.images.all()]
            products_data.append({
                'id': p.id,
                'name': p.name,
                'images': images,
            })

    return JsonResponse({'products': products_data})


def get_similar_products_pattern(request):
    pattern_id = request.GET.get('pattern_id')
    products_data = []

    if pattern_id:
        pattern = Pattern.objects.get(id=pattern_id)
        products = Product.objects.filter(pattern=pattern)
        for p in products:
            images = [img.image.url for img in p.images.all()]
            products_data.append({
                'id': p.id,
                'name': p.name,
                'images': images,
            })

    return JsonResponse({'products': products_data})


# @login_required
def select_style(request):
    
    if request.method == 'POST':
        request.session['pattern_id'] = request.POST.get('pattern_id')
        
        return redirect('measurements')

    if (not request.session.get('fabric_id')) and (not request.session.get('pickup')) and (not request.session.get('own_fabric')):
        
        return redirect('select-fabric-option')
    elif 'category_id' not in request.session:
        return redirect('select-category')
    else:
        patterns = Pattern.objects.prefetch_related('images').annotate(
            average_rating=Avg('productreview__rating', filter=Q(productreview__is_submitted=True)),
            total_reviews=Count('productreview', filter=Q(productreview__is_submitted=True))
            ).filter(Category = request.session['category_id'])
        
        # patterns = Pattern.objects.filter(Category = request.session['category_id'])

        if request.session.get('pickup') or request.session.get('own_fabric'):
            selected_fabric = None
        else:
            selected_fabric = Fabric.objects.get(id = request.session['fabric_id'])
        
        # Try to get previously selected pattern - in case going back - it should exists
        selected_pattern_id = request.session.get('pattern_id')
        
        return render(request, 'select-style.html', {'patterns': patterns,
                                                        'selected_fabric': selected_fabric,
                                                        'selected_pattern_id': int(selected_pattern_id) if selected_pattern_id else None,
                                                        })

def get_standard_measurements(request, chart):

    raw_values = SizeValue.objects.filter(chart=chart).select_related('size', 'parameter')
    
    structured_data = defaultdict(list)
    for val in raw_values:
        structured_data[val.size.label].append({
            "name": val.parameter.name,
            "value": val.value
        })

    size_data = [
        {
            "label": label,
            "parameters": params
        } for label, params in structured_data.items()
    ]

    return size_data

def measurements(request):
    try:
        if request.session.get('pickup') or request.session.get('own_fabric'):
            selected_fabric = None
        else:
            selected_fabric = Fabric.objects.get(id=request.session['fabric_id'])
        pattern = Pattern.objects.get(id=request.session['pattern_id'])
    except (KeyError, Fabric.DoesNotExist, Pattern.DoesNotExist):
        messages.error(request, "Fabric or style not selected.")
        return redirect('select-style')

    fields = pattern.required_measurements.all()
    chart = pattern.size_chart
    size_chart_data = get_standard_measurements(request, chart)
    form = None
    previous_measurements = None
    
    if request.method == 'POST':
        size_type = request.POST.get('size_type')  # 'custom' or 'standard'

        if size_type == 'custom':
            form = DynamicMeasurementForm(request.POST, fields=fields)
            if form.is_valid():
                request.session['temp_measurements'] = form.cleaned_data
                return redirect('options')

            else:
                # Optionally: Save to session and redirect
                messages.error(request, "Measurement data is not valid")
                return redirect('measurements')
        elif size_type == 'standard':
            standard_size = request.POST.get('active_standard_size')

            selected_data = next(
                (entry for entry in size_chart_data if entry['label'] == standard_size),
                    None
                        )

            measurement_dict = {
                'Size': standard_size,
                **{param['name']: param['value'] for param in selected_data['parameters']}
                    }
            
            try:
                request.session['temp_measurements'] = measurement_dict
                return redirect('options')
            except:
                messages.error(request, "Body Parameter is not valid")
                return redirect('measurements')
        
    else:
        initial_data = request.session.get('temp_measurements', None)
        if initial_data:
            if 'Size' in initial_data:
                size_type = 'standard'
                selected_standard_size = initial_data['Size']
                form = DynamicMeasurementForm(fields=fields)
                
            else:
                size_type = 'custom'
                form = DynamicMeasurementForm(fields=fields, initial=initial_data)
                selected_standard_size=""
        else:
            user = request.user
            if user.is_authenticated:
                order = Order.objects.filter(user = user.profile).order_by('-order_date').first()
                if order:
                    order_item = order.items.first()
                    if order_item:
                        previous_measurements = order_item.measurements or {}
                    if not 'Size' in previous_measurements:
                        form = DynamicMeasurementForm(fields=fields, initial = previous_measurements)
                        size_type = 'custom'
                        selected_standard_size = ""
        
        if not form:
            form = DynamicMeasurementForm(fields=fields)
            size_type = 'custom'
            selected_standard_size = ""


        # To show id measurement eixts
        user = request.user
        if user.is_authenticated:
            order = Order.objects.filter(user = user.profile).order_by('-order_date').first()
            if order:
                order_item = order.items.first()
                if order_item:
                    previous_measurements = order_item.measurements
                else:
                    previous_measurements = None

        return render(request, 'measurements.html', {
            'form': form,
            'measurement_guides': fields,
            'pattern': pattern,
            'selected_fabric': selected_fabric,
            'selected_style': pattern,
            'size_chart_data': size_chart_data,
            'selected_tab': size_type,
            'selected_standard_size': selected_standard_size,
            'previous_measurements': previous_measurements
                })

def save_session_data(request):
    user = request.user
    
    pattern_id = request.session.get('pattern_id')
    option_data = request.session.get('temp_options')
    measurement_data = request.session.get('temp_measurements')

    if request.session.get('fabric_id'):
        fabric_id = request.session.get('fabric_id')
        fabric = Fabric.objects.get(id=fabric_id)
        fabric_price = fabric.price
        fabric_original_price = fabric.original_price
        own_fabric = False
        arrange_pickup = False

    else:
        fabric = None
        fabric_price = 0
        fabric_original_price = 0
        try:
            own_fabric = request.session.get('own_fabric')
            arrange_pickup = request.session.get('pickup')
        except:
            messages.error(request, "Error")

    pattern = Pattern.objects.get(id=pattern_id)

    if not pattern_id or not option_data or not measurement_data:
        messages.error(request, "Missing fabric or pattern selection.")
        return redirect('fabric_selection')
    else:

        for key, value in measurement_data.items():

            Cart.objects.update_or_create(
            user=user,
            fabric=fabric,
            own_fabric = own_fabric,
            arrange_pickup = arrange_pickup,
            pattern=pattern,
            options=option_data,
            price = fabric_price + pattern.price ,
            original_price = fabric_original_price + pattern.original_price ,
            measurements = measurement_data
        )
            
        # messages.success(request, "Your selection has been saved to cart.")

def options(request):
    pattern_id = request.session.get('pattern_id')
    if not request.session.get('own_fabric'):
        selected_fabric = Fabric.objects.get(id=request.session['fabric_id'])
    else:
        selected_fabric = None
    selected_style = Pattern.objects.get(id=request.session['pattern_id'])
    measurements = request.session.get('temp_measurements')
    
    if not pattern_id:
        return redirect('select-style')

    pattern = Pattern.objects.get(id=pattern_id)
    fields = pattern.required_options.all()

    if request.method == 'POST':
        form = DynamicOptionForm(request.POST, fields=fields)
        if form.is_valid():
            request.session['temp_options'] = form.cleaned_data

            if request.user.is_authenticated:
                save_session_data(request)
                return redirect('cart')
            else:
                request.session['next_url'] = reverse('cart')
                print(request.session['next_url'])
                return redirect('login')
            
    else:
        option_data = request.session.get('temp_options', None)
        if option_data:
            form = DynamicOptionForm(option_data, fields=fields)
        else:
            form = DynamicOptionForm(fields=fields)
    
    return render(request, 'options.html', {
            'form': form,
            'measurement_guides': fields,
            'pattern': pattern,
            'selected_fabric': selected_fabric,
            'selected_style': selected_style,
            'measurements': measurements
        })

@login_required
def user_cart(request):

    user = request.user
    carts = Cart.objects.filter(user=user).select_related('fabric', 'pattern', 'product').order_by('-created_at')
    wallet = Wallet.objects.filter(user=user).first()
    if wallet:
        amount_in_wallet = wallet.balance
    else:
        amount_in_wallet = None

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        

        if action == 'order':
            request.session['item_id'] = item_id
            return redirect('order-review')
            
        elif action == 'remove':
            cart_item = get_object_or_404(Cart, id=item_id, user=user)
            cart_item.delete()
            messages.success(request, "Item removed from cart.")
            return redirect('cart')

    cart_data = []
    for cart in carts:

        # if cart.fabric:
        #     fabric_name = cart.fabric.name
        #     fabric_img = cart.fabric.images.first().image.url
        #     own_fabric = None
        #     arrange_pickup = None
        #     fabric_inStock = cart.fabric.units_inStock

        # else:
        #     own_fabric = cart.fabric
        #     arrange_pickup = cart.arrange_pickup
        #     fabric_name = None
        #     fabric_img = None

        if cart.product:
            fabric_inStock = cart.product.fabric.units_inStock
            own_fabric = None
            fabric_name = None
            fabric_img = None
            arrange_pickup = None

        elif cart.own_fabric:
            own_fabric = cart.own_fabric
            arrange_pickup = cart.arrange_pickup
            fabric_name = None
            fabric_img = None
        else:
            fabric_name = cart.fabric.name
            fabric_img = cart.fabric.images.first().image.url
            own_fabric = None
            arrange_pickup = None
            fabric_inStock = cart.fabric.units_inStock

        flat_discount = FlatDiscount.objects.filter(is_active=True).first()
        pricing = calculate_final_price(
            base_price=cart.price,
            original_price=cart.original_price,
            flat_discount=flat_discount
                )
        cart.final_price = pricing['final_price']
        cart.discount = pricing['discount_amount']

        out_of_stock = False
        if not own_fabric:
            if fabric_inStock <= 0:
                out_of_stock = True
       

        cart_data.append({
            'id': cart.id,
            'product': cart.product,
            'fabric_name': fabric_name,
            'fabric_img': fabric_img,
            'own_fabric': own_fabric,
            'arrange_pickup': arrange_pickup,
            'pattern_name': cart.pattern.name,
            'pattern_img': cart.pattern.images.first().image.url,
            'options': cart.options or {},
            'measurements': cart.measurements or {},
            'created_at': cart.created_at,
            'final_price': pricing['final_price'],
            'discount_amount': pricing['discount_amount'],
            'original_price': cart.original_price,
            'out_of_stock': out_of_stock,
                })
        
    return render(request, 'cart.html', {'cart_data': cart_data,
                                         'amount_in_wallet': amount_in_wallet})

@login_required
def orders(request):
    user_profile = request.user.profile
    orders = Order.objects.filter(user=user_profile).prefetch_related('items__product', 'items__fabric', 'items__pattern').order_by('-order_date')
    print("ORDERS")
    for order in orders:
        order.expected_delivery = order.order_date + timedelta(days=7)

    return render(request, 'orders.html', {'orders': orders})


@login_required
def address(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = OrderAddressForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            return redirect('order-review')  # or to payment page
    else:
        form = OrderAddressForm(instance=profile)
    return render(request, 'address.html', {
        'form': form,
        'profile': profile,
    })

@login_required
def order_review(request):
    item_id = request.session['item_id']
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    profile = request.user.profile
    fabric = cart_item.fabric
    pattern = cart_item.pattern
    # total_price = cart_item.total_amount
    product = cart_item.product

    flat_discount = FlatDiscount.objects.filter(is_active=True).first()
    pricing = calculate_final_price(
        base_price=cart_item.price,
        original_price=cart_item.original_price,
        flat_discount=flat_discount
            )
    cart_item.final_price = pricing['final_price']
    cart_item.discount_amount = pricing['discount_amount']
    wallet = Wallet.objects.filter(user=request.user).first()
    if wallet:
        amount_in_wallet = wallet.balance
    else:
        amount_in_wallet = 0

    cart_item.wallet_balance = amount_in_wallet
    if cart_item.wallet_balance >= pricing['final_price']:
        cart_item.final_price_deducted_wallet = 0
        if wallet:
            wallet.balance = amount_in_wallet - pricing['final_price']
    else:
        cart_item.final_price_deducted_wallet = pricing['final_price'] - cart_item.wallet_balance
        if wallet:
            wallet.balance = 0

    if request.method == 'POST':

        if product:
            fabric = product.fabric # Stock of fabric is governed by Product
            if fabric.units_inStock >= 1:
                fabric.units_inStock -= 1
                fabric.units_sold += 1
                product.units_sold += 1
                product.save()
                fabric.save()
            else:
                messages.error(request, f"Not enough stock for {product.name}")
                return redirect('cart')
        else:
            if fabric:
                if fabric.units_inStock >= 1:
                    fabric.units_inStock -= 1
                    fabric.units_sold += 1
                    fabric.save()

                    pattern.units_sold +=1
                    pattern.save()

                else:
                    messages.error(request, f"Not enough stock for {fabric.name}")
                    return redirect('cart')

        order = Order.objects.create(user=request.user.profile, 
                                     total_amount=cart_item.final_price_deducted_wallet,
                                     building = profile.building,
                                     house = profile.house,
                                     street = profile.street,
                                     area = profile.area,
                                     city = profile.city,
                                     state = profile.state,
                                     zip_code = profile.zip_code,
                                     mobile = profile.mobile,
                                     )
        
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            fabric=cart_item.fabric,
            pattern=cart_item.pattern,
            options=cart_item.options,
            measurements=cart_item.measurements,
            quantity=cart_item.quantity,
                )
        
        cart_item.delete()  # Clear from cart
        if wallet:
            wallet.save() # save the wallet amount
        return redirect('orders')
        
    return render(request, 'order-review.html', {
        'profile': profile,
        'cart_item': cart_item,
        # 'total_price': total_price
    })

@login_required
def order_success(request):
    item_id = request.session['item_id']
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    profile = request.user.profile
    fabric = cart_item.fabric
    pattern = cart_item.pattern
    total_price = cart_item.total_amount
    product = cart_item.product

    if request.method == 'POST':

        if product:
            if product.units_inStock >= 1:
                product.units_inStock -= 1
                product.units_sold += 1
                product.save()
            else:
                messages.error(request, f"Not enough stock for {product.name}")
                return redirect('cart')
        else:
            if fabric.units_inStock >= 1:
                fabric.units_inStock -= 1
                fabric.units_sold += 1
                fabric.save()

                pattern.units_sold +=1
                pattern.save()

            else:
                messages.error(request, f"Not enough stock for {fabric.name}")
                return redirect('cart')

        order = Order.objects.create(user=request.user.profile, 
                                     total_amount=total_price,
                                     building = profile.building,
                                     house = profile.house,
                                     street = profile.street,
                                     area = profile.area,
                                     city = profile.city,
                                     state = profile.state,
                                     zip_code = profile.zip_code,
                                     mobile = profile.mobile,
                                     )
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            fabric=cart_item.fabric,
            pattern=cart_item.pattern,
            options=cart_item.options,
            measurements=cart_item.measurements,
            quantity=cart_item.quantity,
                )
        
        cart_item.delete()  # Clear from cart
        return redirect('orders')
        
    return render(request, 'order-review.html', {
        'profile': profile,
        'cart_item': cart_item,
        'total_price': total_price
    })


def products(request):

    # products = Product.objects.prefetch_related('images').all()
    
    products = Product.objects.prefetch_related('images').annotate(
            average_rating=Avg('productreview__rating', filter=Q(productreview__is_submitted=True))
            )

    if request.method == 'POST':

        return redirect('cart')

    return render(request, 
                  'products.html', 
                  {'products': products, 
                            })

@login_required
def save_product_to_cart(request, product_id):
    user = request.user
    
    product = Product.objects.get(id=product_id)
    measurement_data = request.session.get('temp_measurements')

    if not product_id or not measurement_data:
        messages.error(request, "Missing product selection.")
        return redirect('products')
    else:
        
        for key, value in measurement_data.items():

            Cart.objects.update_or_create(
            user=user,
            product = product,
            fabric=product.fabric,
            pattern=product.pattern,
            price = product.price,
            original_price = product.original_price,
            measurements = measurement_data
                )
            
def product_detail(request, product_id):
    
    product = Product.objects.select_related('fabric__category', 'pattern').prefetch_related('images', 'tag').annotate(
        average_rating=Avg('productreview__rating', filter=Q(productreview__is_submitted=True)),
        total_reviews=Count('productreview', filter=Q(productreview__is_submitted=True))
    ).get(id=product_id)

    product.views = models.F('views') + 1  # Avoids race conditions
    product.save(update_fields=['views'])

    
    reviews = ProductReview.objects.select_related('reviewer__user').filter(
        product=product, is_submitted=True
            ).order_by('-created_at')
    
    if request.method == 'POST':

        return redirect('cart')

    flat_discount = FlatDiscount.objects.filter(is_active=True).first()
    pricing = calculate_final_price(
            base_price=product.price,
            original_price=product.original_price,
            flat_discount=flat_discount
                )
    product.final_price = pricing['final_price']
    product.original_price = pricing['original_price']

    # 1. Color options: same pattern, same fabric category
    shown_product_ids = {product.id}
    color_options = Product.objects.filter(
        pattern=product.pattern,
        fabric__category=product.fabric.category
        ).exclude(id__in=shown_product_ids)
    
    shown_product_ids.update(color_options.values_list('id', flat=True))

    # 2. Similar fabric products
    similar_fabric_products = Product.objects.filter(
        fabric__category=product.fabric.category
        ).exclude(id__in=shown_product_ids)
    
    shown_product_ids.update(similar_fabric_products.values_list('id', flat=True))

    # 3. Similar pattern products
    similar_pattern_products = Product.objects.filter(
        pattern=product.pattern
        ).exclude(id__in=shown_product_ids)

    shown_product_ids.update(similar_pattern_products.values_list('id', flat=True))

    # 4. Explore more — products with similar tags
    tag_ids = product.tag.values_list('id', flat=True)
    explore_more = Product.objects.filter(
        tag__in=tag_ids
        ).exclude(id__in=shown_product_ids).annotate(
        shared_tags=Count('id', filter=Q(tag__in=tag_ids))
            ).order_by('-shared_tags', '-id').distinct()[:6]

    return render(request, 'product-detail.html', {
        'product': product,
        'reviews': reviews,
        'color_options': color_options,
        'similar_fabric_products': similar_fabric_products,
        'similar_pattern_products': similar_pattern_products,
        'explore_more': explore_more
    })


def product_measurements(request, product_id):
    try:
        product = Product.objects.get(id=product_id)

    except (KeyError, Product.DoesNotExist):
        messages.error(request, "Product not selected.")
        return redirect('products')

    fields = product.required_measurements.all()
    chart = product.size_chart

    size_chart_data = get_standard_measurements(request, chart)
    form = None
    previous_measurements = None

    if request.method == 'POST':
        size_type = request.POST.get('size_type')  # 'custom' or 'standard'

        if size_type == 'custom':
            form = DynamicMeasurementForm(request.POST, fields=fields)
            if form.is_valid():
                request.session['temp_measurements'] = form.cleaned_data
                save_product_to_cart(request, product_id)
                return redirect('cart')

            else:
                # Optionally: Save to session and redirect
                messages.error(request, "Measurement data is not valid")
                return redirect('product-measurements', product_id=product.id)
        elif size_type == 'standard':
            standard_size = request.POST.get('active_standard_size')

            selected_data = next(
                (entry for entry in size_chart_data if entry['label'] == standard_size),
                    None
                        )

            measurement_dict = {
                'Size': standard_size,
                **{param['name']: param['value'] for param in selected_data['parameters']}
                    }

            try:
                request.session['temp_measurements'] = measurement_dict
                save_product_to_cart(request, product_id)

                return redirect('cart')
            except:
                messages.error(request, "Body Parameter is not valid")
                return redirect('measurements')
    else:
        initial_data = request.session.get('temp_measurements', None)
        if initial_data:
            if 'Size' in initial_data:
                size_type = 'standard'
                selected_standard_size = initial_data['Size']
                form = DynamicMeasurementForm(fields=fields)
                
            else:
                size_type = 'custom'
                form = DynamicMeasurementForm(fields=fields, initial=initial_data)
                selected_standard_size=""
        else:
            user = request.user
            if user.is_authenticated:
                order = Order.objects.filter(user = user.profile).order_by('-order_date').first()
                if order:
                    order_item = order.items.first()
                    if order_item:
                        
                        previous_measurements = order_item.measurements or {}
                    if not 'Size' in previous_measurements:
                        form = DynamicMeasurementForm(fields=fields, initial = previous_measurements)
                        size_type = 'custom'
                        selected_standard_size = ""
        
        if not form:
            form = DynamicMeasurementForm(fields=fields)
            size_type = 'custom'
            selected_standard_size = ""


    # To show id measurement eixts
    user = request.user
    if user.is_authenticated:
        order = Order.objects.filter(user = user.profile).order_by('-order_date').first()
        if order:
            order_item = order.items.first()
            if order_item:
                previous_measurements = order_item.measurements

            else:
                previous_measurements = None
    

    form = DynamicMeasurementForm(fields=fields)
    return render(request, 'product-measurements.html', {
        'form': form,
        'measurement_guides': fields,
        'product': product,
        'size_chart_data': size_chart_data,
        'selected_tab': size_type,
        'previous_measurements': previous_measurements
            })

def send_review_email(order, resend=False):
    for item in order.items.all():  # uses related_name='items'
        product = item.product
        fabric = item.fabric
        pattern = item.pattern
        
        if product is None and fabric is None and pattern is None:
            continue  # skip if all items are missing
 
        if fabric is None and pattern is None and product is not None:
            fabric = product.fabric
            pattern = product.pattern

        review, created = ProductReview.objects.get_or_create(
            product=product,
            fabric = fabric,
            pattern = pattern,
            order=order,
            reviewer=order.user,
            defaults={
                'review_token': str(uuid.uuid4()),
            }
        )

        if resend and not created:
            # regenerate token if it's a resend and review already exists
            review.review_token = str(uuid.uuid4())
            review.save()


        review_url = f"http://192.168.1.9:8000/submit_review/{review.review_token}/"

        send_mail(
            subject="We value your feedback!",
            message=f"Please review your recent purchase: \nReview link: {review_url}",
            from_email="noreply@yourdomain.com",
            recipient_list=[order.user.user.email],  # assuming Profile.user is Django User
        )


def add_discount_onfeedback(user, amount, description, order, type):
    wallet, created = Wallet.objects.get_or_create(user=user)
    amount = amount

    if type == 'credit':
        wallet.balance += amount
    elif type == 'debit':
        amount_to_deduct = min(amount, wallet.balance)
        wallet.balance -= amount_to_deduct
        amount = Decimal(amount_to_deduct)  # record actual debited amount in transaction
    else:
        raise ValueError("Invalid type: must be 'credit' or 'debit'")

    wallet.save()
    if amount > 0:
        WalletTransaction.objects.create(
            user=user,
            amount=amount,
            type=type,
            description=description,
            order=order,
        )


def submit_review(request, review_token):
    try:
        review = get_object_or_404(ProductReview, review_token=review_token)
        if review.is_submitted:
            return render(request, 'review_exists.html')
    except:
        return render(request, 'error_page.html')

    review = ProductReview.objects.select_related('order__user').prefetch_related(
        'order__items__product', 'order__items__fabric', 'order__items__pattern'
        ).get(review_token=review_token)
    order = review.order
    user = order.user.user

    if request.method == 'POST':
        form = ProductReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review.rating = form.cleaned_data['rating']
            review.comment = form.cleaned_data['comment']
            if form.cleaned_data.get('image'):
                review.image = form.cleaned_data['image']
                add_discount_onfeedback(user=user, amount = 50, description='Feedback Reward', order=order, type='credit')

            review.is_submitted = True
            review.save()
            return render(request, 'thankyou.html')
    else:
        form = ProductReviewForm()

    return render(request, 'submit_review.html', {
        'form': form,
        'product': review.product,
        'order': order
    })

def thankyou(request):

    return render(request,
           'thankyou.html',
           {})

def review_exists(request):

    return render(request,
           'review_exists.html',
           {})

def error_page(request):

    return render(request,
           'error_page.html',
           {})




def send_order_confirmation(order):
    """
    Sends a simple email confirmation immediately after order creation.
    """
    items = order.items.select_related('product', 'fabric', 'pattern')
    lines = []
    for it in items:
        if it.product:
            label = f"Product: {it.product.name}"
        elif it.pattern:
            label = f"Pattern: {it.pattern.name}"
        elif getattr(it, "custom_pattern", False):
            label = f"Custom: {getattr(it, 'custom_pattern_name', 'Custom stitching')}"
        else:
            label = "Item"
        lines.append(f"- {label} | Qty: {it.quantity}")

    subject = f"Order #{order.id} confirmed"
    message = (
        f"Hi {order.user.name or 'Customer'},\n\n"
        f"Thanks for your purchase on {order.order_date.strftime('%d %b %Y, %H:%M')}.\n"
        f"Order #{order.id} — Total: ₹{order.total_amount}\n\n"
        f"Items:\n" + "\n".join(lines) + "\n\n"
        f"We’ll update you when it’s shipped.\n\n"
        f"Regards,\nLADYBUG"
    )

    recipient = [order.user.user.email] if order.user and order.user.user.email else []
    if recipient:
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient)



def _upsert_profile(name, mobile, email):
    # basic quick-create; no OTP here
    user, _ = User.objects.get_or_create(username=mobile or email or f"walkin_{uuid.uuid4()}",
                                         defaults={"email": email or ""})
    profile, created = Profile.objects.get_or_create(user=user, defaults={
        "name": name or "",
        "mobile": mobile or "",
        "email": email or ""
    })
    # Fill missing basics if provided
    changed = False
    for f, v in [("name", name), ("mobile", mobile), ("email", email)]:
        if v and getattr(profile, f) != v:
            setattr(profile, f, v); changed = True
    if changed: profile.save()
    return profile

def _line_total(item: OrderItem):
    # Decide the price for each path
    if item.product:
        return (item.product.price or 0) * item.quantity
    if item.custom_pattern:
        return (item.custom_price or 0) * item.quantity
    # stitching with existing pattern/fabric
    base = (item.pattern.price if item.pattern else 0)
    fabric_price = (0 if item.own_fabric else (item.fabric.price if item.fabric else 0))
    return (base + fabric_price) * item.quantity



@staff_member_required
@transaction.atomic
def admin_create_order(request):
    message_level = None
    if request.method == "POST":
        cust_form = AdminOrderCustomerForm(request.POST)
        order_stub = Order()  # dummy for formset binding
        formset = AdminOrderItemFormSet(request.POST, instance=order_stub)

        try:
            if cust_form.is_valid() and formset.is_valid():
                # --- resolve/create profile by mobile ---
                mobile = (cust_form.cleaned_data.get("mobile") or "").strip()
                name   = (cust_form.cleaned_data.get("name") or "").strip()
                email  = (cust_form.cleaned_data.get("email") or "").strip()

                try:
                    prof = Profile.objects.get(mobile=mobile)
                except Profile.DoesNotExist:
                    prof = _upsert_profile(name=name, mobile=mobile, email=email)

                # --- create order ---
                order = Order.objects.create(
                    user=prof,
                    total_amount=0,
                    payment_status="paid",
                    building=cust_form.cleaned_data.get("building") or prof.building,
                    house=cust_form.cleaned_data.get("house") or prof.house,
                    street=cust_form.cleaned_data.get("street") or prof.street,
                    area=cust_form.cleaned_data.get("area") or prof.area,
                    city=cust_form.cleaned_data.get("city") or prof.city,
                    state=cust_form.cleaned_data.get("state") or prof.state,
                    zip_code=cust_form.cleaned_data.get("zip_code") or prof.zip_code,
                    mobile=cust_form.cleaned_data.get("mobile_override") or prof.mobile,
                )

                # --- parse measurements/options ---
                measurements_data = {}
                for mf in MeasurementField.objects.all():
                    val = request.POST.get(f"measurement_{mf.id}")
                    if val not in (None, ""):
                        measurements_data[mf.name] = val

                options_data = {}
                for opt in PatternOption.objects.all():
                    key = f"option_{opt.id}"
                    if opt.field_type == "bool":
                        options_data[opt.name] = bool(request.POST.get(key))
                    else:
                        val = request.POST.get(key)
                        if val not in (None, ""):
                            options_data[opt.name] = val

                # --- save items ---
                formset.instance = order
                items = formset.save(commit=False)
                grand_total = 0

                for it in items:
                    it.measurements = measurements_data or None
                    it.options = options_data or None

                    if it.product:
                        fabric = it.product.fabric
                        if fabric and fabric.units_inStock >= it.quantity:
                            fabric.units_inStock -= it.quantity
                            fabric.units_sold += it.quantity
                            it.product.units_sold = (it.product.units_sold or 0) + it.quantity
                            fabric.save(); it.product.save()
                        else:
                            raise ValidationError(f"Not enough stock for {it.product.name}")
                        it.fabric = fabric
                        it.pattern = it.product.pattern

                    elif it.pattern and not it.own_fabric:
                        if it.fabric:
                            if it.fabric.units_inStock >= it.quantity:
                                it.fabric.units_inStock -= it.quantity
                                it.fabric.units_sold += it.quantity
                                it.fabric.save()
                            else:
                                raise ValidationError(f"Not enough stock for {it.fabric.name}")
                        if it.pattern:
                            it.pattern.units_sold = (it.pattern.units_sold or 0) + it.quantity
                            it.pattern.save()

                    elif getattr(it, "custom_pattern", False) and it.fabric and not it.own_fabric:
                        if it.fabric.units_inStock >= it.quantity:
                            it.fabric.units_inStock -= it.quantity
                            it.fabric.units_sold += it.quantity
                            it.fabric.save()
                        else:
                            raise ValidationError(f"Not enough stock for {it.fabric.name}")

                    line_total = _line_total(it)
                    grand_total += line_total
                    it.save()

                order.total_amount = grand_total
                order.save()
                
                send_order_confirmation(order)
                messages.success(request, f"Order #{order.id} created successfully ✅")
                return redirect("admin_order_invoice", order_id=order.id)
            else:
                messages.error(request, "Please correct the errors in the form.")
        except Exception as e:
            messages.error(request, f"Couldn't create order: {e}")

    else:
        cust_form = AdminOrderCustomerForm()
        order_stub = Order()
        formset = AdminOrderItemFormSet(instance=order_stub)

    measurement_fields = MeasurementField.objects.all()
    pattern_options = list(PatternOption.objects.all())
    for opt in pattern_options:
        raw = opt.choices or ""
        opt.choice_list = [c.strip() for c in raw.split(",") if c.strip()]

    return render(request, "admin_create_order.html", {
        "cust_form": cust_form,
        "formset": formset,
        "measurement_fields": measurement_fields,
        "pattern_options": pattern_options,
    })

@staff_member_required
def admin_order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()

    # prepare invoice items with calculated line totals
    invoice_items = []
    for item in items:
        if item.product and item.product.price:
            unit_price = item.product.price
        elif item.custom_price:
            unit_price = item.custom_price
        else:
            unit_price = 0

        line_total = unit_price * item.quantity

        invoice_items.append({
            "name": (
                item.product.name if item.product
                else item.custom_pattern_name if item.custom_pattern
                else item.pattern.name if item.pattern
                else "Custom Item"
            ),
            "quantity": item.quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })

    context = {
        "order": order,
        "invoice_items": invoice_items,
    }
    return render(request, "admin_order_invoice.html", context)


# --- ADD THIS VIEW ---
@staff_member_required
@require_POST
def lookup_customer_by_mobile(request):
    mobile = (request.POST.get("mobile") or "").strip()
    if not mobile.isdigit() or len(mobile) != 10:
        return JsonResponse({"ok": False, "error": "Enter a valid 10-digit mobile."}, status=400)

    try:
        profile = Profile.objects.select_related("user").get(mobile=mobile)
    except Profile.DoesNotExist:
        # Not found -> tell UI to show blank fields (new customer flow)
        return JsonResponse({"ok": True, "exists": False})

    # Found -> count orders and fetch last measurements from most recent order item
    orders_qs = Order.objects.filter(user=profile).order_by("-order_date")
    orders_count = orders_qs.count()

    last_measurements = {}
    last_order = orders_qs.first()
    if last_order:
        last_item = last_order.items.order_by("-id").first()  # uses related_name='items'
        if last_item and last_item.measurements:
            last_measurements = last_item.measurements

    data = {
        "ok": True,
        "exists": True,
        "profile": {
            "id": profile.id,
            "name": profile.name or "",
            "email": profile.email or "",
            "mobile": profile.mobile or "",
            "building": profile.building or "",
            "house": profile.house or "",
            "street": profile.street or "",
            "area": profile.area or "",
            "city": profile.city or "",
            "state": profile.state or "",
            "zip_code": profile.zip_code or "",
        },
        "orders_count": orders_count,
        "last_measurements": last_measurements,
    }
    return JsonResponse(data)

def LinksView(request):
   
   return render(request, 'links.html', {})


def dev(request):
   
   return render(request, 'dev.html', {})

