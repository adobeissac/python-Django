import math
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .woocommerce import wc_api
from .models import Order
import json


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_cart(request):
    return request.session.get('cart', {})

def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True

def cart_total_items(cart):
    return sum(item['quantity'] for item in cart.values())


# ── Shop ──────────────────────────────────────────────────────────────────────

def product_list(request):
    page = int(request.GET.get('page', 1))
    per_page = 12
    category_id = request.GET.get('category', '')
    search = request.GET.get('q', '')
    sort = request.GET.get('sort', 'date')

    products = wc_api.get_products(
        page=page, per_page=per_page,
        category=category_id or None,
        search=search or None,
        order_by=sort
    )
    categories = wc_api.get_categories()
    total = wc_api.get_products_count(category=category_id or None, search=search or None)
    total_pages = math.ceil(total / per_page) if total else 1

    # Find selected category name
    selected_category = None
    if category_id:
        selected_category = next((c for c in categories if str(c['id']) == str(category_id)), None)

    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'category_id': category_id,
        'search': search,
        'sort': sort,
        'page': page,
        'total_pages': total_pages,
        'total': total,
    })


def product_detail(request, product_id):
    product = wc_api.get_product(product_id)
    if not product:
        messages.error(request, "Product not found.")
        return redirect('product_list')

    variations = []
    if product.get('type') == 'variable':
        variations = wc_api.get_product_variations(product_id)

    related_ids = [p['id'] for p in product.get('related_ids', [])[:4]]
    related = []
    for rid in related_ids:
        p = wc_api.get_product(rid)
        if p:
            related.append(p)

    return render(request, 'store/product_detail.html', {
        'product': product,
        'variations': variations,
        'related': related,
    })


# ── Cart ──────────────────────────────────────────────────────────────────────

def cart_view(request):
    cart = get_cart(request)
    cart_items = []
    subtotal = 0

    for pid, item in cart.items():
        price = float(item.get('price', 0))
        qty = item.get('quantity', 1)
        line_total = price * qty
        subtotal += line_total
        cart_items.append({**item, 'product_id': pid, 'line_total': line_total})

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
    })


@require_POST
def add_to_cart(request, product_id):
    cart = get_cart(request)
    data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
    quantity = int(data.get('quantity', 1))
    variation_id = data.get('variation_id', '')

    pid = str(product_id)
    cart_key = f"{pid}_{variation_id}" if variation_id else pid

    if cart_key in cart:
        cart[cart_key]['quantity'] += quantity
    else:
        product = wc_api.get_product(product_id)
        if not product:
            return JsonResponse({'success': False, 'error': 'Product not found'})

        name = product['name']
        price = product.get('sale_price') or product.get('price', '0')
        image = product['images'][0]['src'] if product.get('images') else ''

        if variation_id:
            for v in wc_api.get_product_variations(product_id):
                if str(v['id']) == str(variation_id):
                    price = v.get('sale_price') or v.get('price', price)
                    if v.get('image'):
                        image = v['image']['src']
                    attrs = ', '.join(f"{a['name']}: {a['option']}" for a in v.get('attributes', []))
                    name = f"{name} ({attrs})"
                    break

        cart[cart_key] = {
            'product_id': pid,
            'variation_id': variation_id,
            'name': name,
            'price': float(price),
            'quantity': quantity,
            'image': image,
        }

    save_cart(request, cart)
    return JsonResponse({'success': True, 'cart_count': cart_total_items(cart)})


@require_POST
def update_cart(request, cart_key):
    cart = get_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    if quantity <= 0:
        cart.pop(cart_key, None)
    elif cart_key in cart:
        cart[cart_key]['quantity'] = quantity
    save_cart(request, cart)
    return redirect('cart')


@require_POST
def remove_from_cart(request, cart_key):
    cart = get_cart(request)
    cart.pop(cart_key, None)
    save_cart(request, cart)
    return redirect('cart')


# ── Checkout ──────────────────────────────────────────────────────────────────

def checkout(request):
    cart = get_cart(request)
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    if request.method == 'POST':
        # Build WooCommerce order payload
        line_items = []
        for key, item in cart.items():
            li = {
                'product_id': int(item['product_id']),
                'quantity': item['quantity'],
            }
            if item.get('variation_id'):
                li['variation_id'] = int(item['variation_id'])
            line_items.append(li)

        order_data = {
            'payment_method': 'bacs',
            'payment_method_title': 'Direct Bank Transfer',
            'set_paid': False,
            'billing': {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'address_1': request.POST.get('address_1'),
                'city': request.POST.get('city'),
                'state': request.POST.get('state'),
                'postcode': request.POST.get('postcode'),
                'country': request.POST.get('country', 'US'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone', ''),
            },
            'shipping': {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'address_1': request.POST.get('address_1'),
                'city': request.POST.get('city'),
                'state': request.POST.get('state'),
                'postcode': request.POST.get('postcode'),
                'country': request.POST.get('country', 'US'),
            },
            'line_items': line_items,
        }

        if request.user.is_authenticated:
            order_data['customer_id'] = 0  # Guest; set actual WC customer ID if syncing

        result = wc_api.create_order(order_data)
        if result and result.get('id'):
            # Save locally
            Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                wc_order_id=result['id'],
                order_key=result.get('order_key', ''),
                status=result.get('status', 'pending'),
                total=result.get('total', 0),
                currency=result.get('currency', 'USD'),
                billing_first_name=result['billing']['first_name'],
                billing_last_name=result['billing']['last_name'],
                billing_email=result['billing']['email'],
                billing_address_1=result['billing']['address_1'],
                billing_city=result['billing']['city'],
                billing_state=result['billing']['state'],
                billing_postcode=result['billing']['postcode'],
                billing_country=result['billing']['country'],
            )
            save_cart(request, {})  # Clear cart
            messages.success(request, f"Order #{result['id']} placed successfully!")
            return redirect('order_confirmation', order_id=result['id'])
        else:
            messages.error(request, "Failed to place order. Please try again.")

    # Pre-fill email if logged in
    user_email = request.user.email if request.user.is_authenticated else ''
    cart_items = []
    subtotal = 0
    for key, item in cart.items():
        price = float(item.get('price', 0))
        qty = item.get('quantity', 1)
        line_total = price * qty
        subtotal += line_total
        cart_items.append({**item, 'cart_key': key, 'line_total': line_total})

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'user_email': user_email,
    })


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, wc_order_id=order_id)
    wc_order = wc_api.get_order(order_id)
    return render(request, 'store/order_confirmation.html', {
        'order': order,
        'wc_order': wc_order,
    })


# ── Account ───────────────────────────────────────────────────────────────────

@login_required
def account(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/account.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, wc_order_id=order_id, user=request.user)
    wc_order = wc_api.get_order(order_id)
    return render(request, 'store/order_detail.html', {
        'order': order,
        'wc_order': wc_order,
    })


# ── Auth ──────────────────────────────────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect('product_list')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Welcome.")
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
