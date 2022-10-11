from email.mime import image
from unicodedata import name
from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review
import stripe
from django.conf import settings
from django.contrib.auth.models import User, Group
from .form import SignUpForm, ContactForm, ProductForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.core.mail import EmailMessage



def Home(request, category_slug=None):
    category_page = None
    products = None
    if category_slug != None:
        category_page = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category_page, available=True)
    else:
        products = Product.objects.all().filter(available=True)

    return render(request, 'home.html', {'category_page': category_page, 'products': products})


def ProductDetails(request, category_slug, product_slug):
    try:
       product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Exception as e:
        raise e
    if request.method == 'POST' and request.user.is_authenticated and request.POST['content'].strip() != '':
        Review.objects.create(
            product = product,
            user = request.user,
            content = request.POST['content']
        )
    reviews = Review.objects.filter(product=product)
    return render(request, 'product.html', {'product': product, 'reviews': reviews})


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Exception:
        cart = Cart.objects.create(cart_id=_cart_id(request))
    cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity = 1,
            cart = cart
        )
    cart_item.save()

    return redirect('cart_detail')

def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            counter =+ cart_item.quantity
    except ObjectDoesNotExist:
        pass

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = int(total * 100)
    description = 'K-Store - New Order'
    data_key = settings.STRIPE_PUBLISHABLE_KEY

    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']
            email = request.POST['stripeEmail']
            billingName = request.POST['stripeBillingName']
            billingAddress1 = request.POST['stripeBillingAddressLine1']
            billingCity = request.POST['stripeBillingAddressCity']
            billingPostcode = request.POST['stripeBillingAddressZip']
            billingCountry = request.POST['stripeBillingAddressCountryCode']
            shippingName = request.POST['stripeShippingName']
            shippingAddress1 = request.POST['stripeShippingAddressLine1']
            shippingCity = request.POST['stripeShippingAddressCity']
            shippingPostcode = request.POST['stripeShippingAddressZip']
            shippingCountry = request.POST['stripeShippingAddressCountryCode']
            customer = stripe.Customer.create(
                source = token,
                email = email,
            )
            charge = stripe.Charge.create(
                amount = stripe_total,
                currency = 'usd',
                description = description,
                customer = customer.id
            )
            #creating the order
            try:
                order_details = Order.objects.create(
                    token=token,
                    total = total,
                    emailAddress=email,
                    billingName=billingName,
                    billingAddress1=billingAddress1,
                    billingCity=billingCity,
                    billingPostCode=billingPostcode,
                    billingCountry=billingCountry,
                    shippingName=shippingName,
                    shippingAddress1=shippingAddress1,
                    shippingCity=shippingCity,
                    shippingPostCode=shippingPostcode,
                    shippingCountry=shippingCountry
                )
                order_details.save()
                for order_item in cart_items:
                    item_order = OrderItem.objects.create(
                        product=order_item.product.name,
                        quantity=order_item.quantity,
                        price=order_item.product.price,
                        order=order_details
                    )
                    item_order.save()
                    # reduce stock
                    products = Product.objects.get(id=order_item.product.id)
                    products.stock = int(order_item.product.stock - order_item.quantity)
                    products.save()
                    order_item.delete()

                    # print a message when the order is created
                    print('the order has been created')
                    # try:
                    #     sendEmail(order_details.id)
                    #     print('The order email has been sent')
                    # except IOError as e:
                    #     return e
                return redirect('thanks_page', order_details.id)
            except ObjectDoesNotExist:  
                pass


        except stripe.error.CardError as e:
            return False, e


    return render(request, 'cart.html', dict(cart_items=cart_items, total=total, counter=counter, stripe_total=stripe_total, description=description, data_key=data_key))


def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(cart=cart, product=product)
    if cart_item.quantity > 1:
       cart_item.quantity -= 1
       cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart_detail')


def del_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product =get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(cart=cart, product=product)
    cart_item.delete()
    return redirect('cart_detail')

def thanks_page(request, order_id):
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thankyou.html', {'customer_order': customer_order})
    

def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)
    else:
        form = SignUpForm()
    
    return render(request, 'signup.html', {'form': form})

def signinView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('signin')



@login_required(redirect_field_name='next', login_url='order_history')
def orderHistory(request):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order_details = Order.objects.filter(emailAddress=email)
    return render(request, 'order_list.html', {'order_details': order_details})

@login_required(redirect_field_name='next', login_url='order_history')
def orderView(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
    return render(request, 'order_detail.html', {'order': order, 'order_items': order_items})


def search(request):
    products = Product.objects.filter(name__contains=request.GET['name'])
    return render(request, 'home.html', {'products': products})


def sendEmail(request, order_id):
    transaction = Order.objects.get(id=order_id)
    order_item = OrderItem.objects.filter(order=transaction)

    try:
        # if request.method == 'POST':
        #     return request.POST(
        #     "https://api.mailgun.net/v3/ecommercestore.fun/messages",
        #     auth=("api", settings.EMAIL_HOST_PASSWORD),
        #     data={"from": "K-Store <mailgun@ecommercestore.fun>",
        #         "to": ["transaction.emailAddress", "orders@ecommercestore.fun"],
        #         "subject": "K-Store - New Order #{}".format(transaction.id),
        #         "message": get_template('mail/email.html').render(order_information={
        #         'transaction': transaction,
        #         'order_item': order_item
        #     })})


        subject = 'K-Store - New Order #{}'.format(transaction.id)
        to = ['{}'.format(transaction.emailAddress)]
        from_email = 'orders@ecommercestore.fun'
        order_information = {
            'transaction': transaction,
            'order_item': order_item
        }
        message = get_template('mail/email.html').render(order_information)
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        return msg.send()

    except IOError as e:
        return e


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data.get('subject')
            name = form.cleaned_data.get('name')
            from_email = form.cleaned_data.get('from_email')
            message = form.cleaned_data.get('message')

            message_format = f'{name} has sent you a new message:\n\n{message}'
            msg = EmailMessage(subject, message_format, to=['contact@ecommerce.store.fun'], from_email=from_email)

            msg.send()
            
            return render(request, 'contact_success.html')

    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            obj = form.instance
            return render(request, 'vendor.html', {'obj': obj})
           
    else:
        form = ProductForm()
        img = Product.objects.all()
    
        return render(request, 'vendor.html', {'img': img, 'form': form})


    

    
