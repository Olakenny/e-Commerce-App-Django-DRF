from django.shortcuts import redirect, render
from store.models import Order, OrderItem
from django.conf import settings
from django.contrib.auth.models import User, Group
from store.form import SignUpForm, ContactForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.template.loader import get_template
from django.core.mail import EmailMessage

    

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
    
    return render(request, 'store/signup.html', {'form': form})

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
    return render(request, 'store/signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('signin')


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
        message = get_template('/mail/email.html').render(order_information)
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
            
            return render(request, 'store/contact_success.html')

    else:
        form = ContactForm()
    return render(request, 'store/contact.html', {'form': form})

    
