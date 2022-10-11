from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from store.views import *


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Home, name='home'),
    path('category/<slug:category_slug>', Home, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>', ProductDetails, name='product_detail'),
    path('cart/add/<int:product_id>', add_cart, name='add_cart'),
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/remove/<int:product_id>', remove_cart, name='remove_cart'),
    path('cart/delete/<int:product_id>', del_cart, name='delete_cart'),
    path('thankyou/<int:order_id>', thanks_page, name='thanks_page'),
    path('account/create/', signupView, name='signup'),
    path('account/signin/', signinView, name='signin'),
    path('account/signout/', signoutView, name='signout'),
    # path('account/signout/', signoutView, name='signout'),
    path('order-history/', orderHistory, name='order_history'),
    path('order/<int:order_id>', orderView, name='order_detail'),
    path('search/', search, name='search'),
    path('contact/', contact, name='contact'),
    path('product/', add_product, name='product_upload'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
