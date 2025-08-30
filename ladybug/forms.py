from django import forms
from .models import Measurement, MeasurementField, PatternOption, Profile, OrderItem, Order, Product, Fabric, Pattern
from django.forms import inlineformset_factory, BaseInlineFormSet


class MeasurementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in MeasurementField.objects.all():
            self.fields[field.name] = forms.DecimalField(
                label=field.name.capitalize(),
                required=True,
                min_value=0,
                widget=forms.NumberInput(attrs={
                    'class': 'w-full p-2 border border-gray-300 rounded-md',
                    'placeholder': f'Enter your {field.name.lower()} measurement',
                    'step': '0.1'
                })
            )


class DynamicMeasurementForm(forms.Form):
    def __init__(self, *args, fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        if fields:
            for field in fields:
                self.fields[field.name] = forms.FloatField(
                    label=field.name.capitalize(),
                    required=True,
                    widget=forms.NumberInput(attrs={
                        'class': 'w-full border border-gray-300 rounded-md p-2',
                        'placeholder': f"Enter {field.name}",
                        'step': '0.1'
                    }),
                min_value=field.min_value,
                max_value=field.max_value,
                error_messages={
                    'required': 'Measurement is required.',
                    'min_value': f'Minimum allowed value is {field.min_value}',
                    'max_value': f'Maximum allowed value is {field.max_value}',
                    'invalid': 'Enter a valid number.',
                }
                )



class DynamicOptionForm(forms.Form):
    def __init__(self, *args, fields=None, **kwargs):
        super().__init__(*args, **kwargs)

        if fields:
            for field in fields:
                field_name = field.name  # unique key

                if field.field_type == 'float':
                    self.fields[field_name] = forms.FloatField(
                        label=field.name,
                        required=True,
                        initial=field.default_value,
                        widget=forms.NumberInput(attrs={
                            'class': 'w-full border border-gray-300 rounded-md p-2',
                            'placeholder': f"Enter {field.name}",
                            'step': '0.1'
                        }),
                        error_messages={
                            'required': 'This field is required.',
                            'invalid': 'Enter a valid number.',
                        }
                    )

                elif field.field_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        label=field.name,
                        required=True,
                        initial=field.default_value,
                        widget=forms.TextInput(attrs={
                            'class': 'w-full border border-gray-300 rounded-md p-2',
                            'placeholder': f"Enter {field.name}",
                        }),
                        error_messages={
                            'required': 'This field is required.',
                        }
                    )

                elif field.field_type == 'bool':
                    self.fields[field_name] = forms.BooleanField(
                        label=field.name,
                        required=False,
                        initial=(field.default_value.lower() == "true") if field.default_value else False,
                        widget=forms.CheckboxInput(attrs={
                            'class': 'mr-2 leading-tight',
                        })
                    )

                elif field.field_type == 'choice':
                    choices = [(c.strip(), c.strip()) for c in field.choices.split(',')] if field.choices else []
                    self.fields[field_name] = forms.ChoiceField(
                        label=field.name,
                        required=True,
                        initial=field.default_value,
                        choices=choices,
                        widget=forms.Select(attrs={
                            'class': 'w-full border border-gray-300 rounded-md p-2',
                        }),
                        error_messages={
                            'required': 'Please select an option.',
                        }
                    )

class OrderAddressForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'building', 'house', 'street', 'area', 'city',
            'state', 'zip_code', #'mobile'
        ]
        widgets = {
            'building': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'house': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'street': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'area': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'city': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'state': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'zip_code': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            # 'mobile': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super(OrderAddressForm, self).__init__(*args, **kwargs)

        # Set required fields
        required_fields = ['building', 'house', 'area', 'city', 'state', 'zip_code']
        for field_name in self.fields:
            self.fields[field_name].required = field_name in required_fields

class ProductReviewForm(forms.Form):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    rating = forms.IntegerField(widget=forms.HiddenInput())  # JS will set value
    comment = forms.CharField(widget=forms.Textarea, required=False)
    image = forms.ImageField(required=False)

class AdminOrderCustomerForm(forms.Form):
    existing_profile = forms.ModelChoiceField(
        queryset=Profile.objects.all().order_by('name'),
        required=False,
        label="Existing customer"
    )

    # quick-create / lookup
    name = forms.CharField(required=False)
    mobile = forms.CharField(required=False, max_length=10, help_text="10-digit mobile required")
    email = forms.EmailField(required=False)

    # order address (optional overrides)
    building = forms.CharField(required=False)
    house = forms.CharField(required=False)
    street = forms.CharField(required=False)
    area = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(required=False)
    zip_code = forms.CharField(required=False)
    mobile_override = forms.CharField(required=False, max_length=10, label="Order mobile")

    def clean_mobile(self):
        mobile = (self.cleaned_data.get("mobile") or "").strip()
        if not mobile:
            raise forms.ValidationError("Mobile number is required.")
        if not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError("Enter a valid 10-digit mobile.")
        return mobile

    def clean_mobile_override(self):
        mob = (self.cleaned_data.get("mobile_override") or "").strip()
        if mob and (not mob.isdigit() or len(mob) != 10):
            raise forms.ValidationError("Enter a valid 10-digit mobile.")
        return mob


# ----------------------------
# Item form (no JSON fields)
# ----------------------------
class AdminOrderItemForm(forms.ModelForm):
    MODE_CHOICES = [
        ('product', 'Direct product'),
        ('stitch',  'Custom stitching (existing pattern/fabric)'),
        ('custom',  'Totally custom (no pattern in DB)'),
    ]
    mode = forms.ChoiceField(choices=MODE_CHOICES)

    quantity = forms.IntegerField(min_value=1, initial=1)

    # product path
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=False)

    # stitching path
    pattern = forms.ModelChoiceField(queryset=Pattern.objects.all(), required=False)
    fabric = forms.ModelChoiceField(queryset=Fabric.objects.all(), required=False)
    own_fabric = forms.BooleanField(required=False)
    arrange_pickup = forms.BooleanField(required=False)

    # totally custom
    custom_pattern = forms.BooleanField(required=False, initial=False)
    custom_pattern_name = forms.CharField(required=False)
    custom_style_notes = forms.CharField(required=False, widget=forms.Textarea, help_text="Any special instructions")
    custom_price = forms.DecimalField(required=False, min_value=0, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = [
            'quantity',
            'product',
            'pattern', 'fabric', 'own_fabric', 'arrange_pickup',
            'custom_pattern', 'custom_pattern_name', 'custom_style_notes', 'custom_price'
        ]

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('mode')

        if mode == 'product':
            if not cleaned.get('product'):
                self.add_error('product', "Select a product for direct purchase.")
        elif mode == 'stitch':
            if not cleaned.get('pattern'):
                self.add_error('pattern', "Select a pattern for stitching.")
            if not cleaned.get('own_fabric', False) and not cleaned.get('fabric'):
                self.add_error('fabric', "Select a fabric or tick 'own fabric'.")
        elif mode == 'custom':
            cleaned['custom_pattern'] = True
            price = cleaned.get('custom_price')
            if price in (None, ''):
                self.add_error('custom_price', "Provide a custom price.")
            else:
                try:
                    # ensure > 0
                    if float(price) <= 0:
                        self.add_error('custom_price', "Price must be greater than 0.")
                except Exception:
                    self.add_error('custom_price', "Enter a valid price.")
        # else: mode missing; ChoiceField will normally catch this
        return cleaned


# ----------------------------
# Formset
# ----------------------------
class BaseItemFS(BaseInlineFormSet):
    def clean(self):
        super().clean()
        # require at least one non-deleted row
        if not any(getattr(form, 'cleaned_data', None) and not form.cleaned_data.get('DELETE', False)
                   for form in self.forms):
            raise forms.ValidationError("Add at least one item.")

AdminOrderItemFormSet = inlineformset_factory(
    Order, OrderItem, form=AdminOrderItemForm, formset=BaseItemFS, extra=1, can_delete=True
)