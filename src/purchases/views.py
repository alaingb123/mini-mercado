import random
import stripe

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from products.models import Product
from .models import Purchase

from cfehome.env import config

# Obtener la clave secreta de Stripe desde la configuración del entorno
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default=None)

# Establecer la clave secreta de Stripe
stripe.api_key = STRIPE_SECRET_KEY
BASE_ENDPOINT = "http://127.0.0.1:8000"

# Create your views here.

def purchase_start_view(request):
    if not request.method == 'POST':
        print("algo malo paso y no se")
        return HttpResponseBadRequest()
    if not request.user.is_authenticated:
        print("no esta au")
        return HttpResponseBadRequest()
    handle = request.POST.get('handle')
    obj = Product.objects.get(handle=handle)
    stripe_price_id = obj.stripe_price_id
    if stripe_price_id is None:
        return HttpResponseBadRequest()
    purchase = Purchase.objects.create(user=request.user, product=obj)
    request.session['purchase_id'] = purchase.id
    
    success_path = reverse("purchases:success")
    if not success_path.startswith("/"):
        success_path = f"/{success_path}"
    cancel_path = reverse("purchases:stopped")
    
    success_url = f"{BASE_ENDPOINT}{success_path}"
    cancel_url = f"{BASE_ENDPOINT}{cancel_path}"
    print(success_url, cancel_url)
    # Crear una sesión de pago de Stripe utilizando el ID del precio y otras opciones
    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                "price": stripe_price_id,
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url
    )
            
    purchase.stripe_checkout_session_id = checkout_session.id
    purchase.save()
    return HttpResponseRedirect(checkout_session.url)
    

def purchase_success_view(request):
    purchase_id = request.session.get('purchase_id')
    if purchase_id:
        purchase = Purchase.objects.get(id=purchase_id)
        purchase.completed = True
        purchase.save()
    return HttpResponse(f"Finished {purchase_id}")
    
def purchase_stopped_view(request):
    return HttpResponse("Stopped")
