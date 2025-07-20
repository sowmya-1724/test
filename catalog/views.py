from django.shortcuts import render,get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Order
from .models import Product,Category
from django.http import HttpResponse
import qrcode
from io import BytesIO
from django.shortcuts import render
from django.shortcuts import render
from .models import CartItem  
from reportlab.pdfgen import canvas
from datetime import datetime
from .models import Order

def home(request):
    return render(request, 'home.html')


def product_detail(request, pk):
    ob_product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': ob_product})


def product_list(request):
    category_id = request.GET.get('category')
    query = request.GET.get('q')
    products = Product.objects.all()
    if category_id:
        products = products.filter(category_id=category_id)
    if query:
        products = products.filter(name__icontains=query)
    categories = Category.objects.all()
    return render(request, 'product_list.html', {'products': products, 'categories': categories})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after signup
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def add_to_cart(request, pk):
    cart = request.session.get('cart', [])
    if pk not in cart:
        cart.append(pk)
    request.session['cart'] = cart
    return redirect('product_list')
@login_required
def view_cart(request):
    cart = request.session.get('cart', [])
    products = Product.objects.filter(pk__in=cart)
    return render(request, 'cart.html', {'products': products})

@login_required
def place_order(request):
    cart = request.session.get('cart', [])
    if cart:
        order = Order.objects.create(user=request.user)
        order.products.set(cart)
        order.save()
        request.session['cart'] = []  # clear cart
        return redirect('order_history')
    return redirect('product_list')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'order_history.html', {'orders': orders})
@login_required
def make_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Payment logic goes here
    return HttpResponse(f"Initiate payment for Order #{order.id}")
@login_required
def generate_cart_qr(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)

    upi_id = "9346363970@ybl"  
    payee_name = request.user.username

    qr_text = f"upi://pay?pa={upi_id}&pn={payee_name}&am={total}&cu=INR"
    qr = qrcode.make(qr_text)

    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    products = []
    total=0
    for item in cart_items:
        product = item.product
        original_price = product.price
        quantity = item.quantity
        amount = original_price * quantity
        total += amount
        products.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': item.quantity,
            'image': product.image, 
            'amount':amount
            
        })
    return render(request, 'cart.html', {'products': products, 'total':total})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('view_cart')


@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart_item = CartItem.objects.filter(user=request.user, product=product).first()
    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1

            cart_item.save()
        else:
            cart_item.delete()
    return redirect('view_cart')
@login_required
def download_invoice(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = 0

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 14)
    p.drawString(100, 800, f"Invoice for {request.user.username}")
    p.setFont("Helvetica", 12)

    y = 770
    p.drawString(50, y, "S.No")
    p.drawString(100, y, "Product")
    p.drawString(300, y, "Qty")
    p.drawString(350, y, "Price")
    p.drawString(420, y, "Amount")

    for idx, item in enumerate(cart_items, 1):
        y -= 20
        amount = item.product.price * item.quantity
        total += amount
        p.drawString(50, y, str(idx))
        p.drawString(100, y, item.product.name)
        p.drawString(300, y, str(item.quantity))
        p.drawString(350, y, f"{item.product.price}")
        p.drawString(420, y, f"{amount}")

    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(300, y, "Total:")
    p.drawString(420, y, f"Rs {total}")
    p.showPage()
    p.save()

    return response


