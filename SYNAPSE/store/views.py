from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder

def store(request):
    data = cartData(request)
    cartItems = data['cartItems']

    if request.user.is_authenticated:
        # Ensure a Customer exists for the user
        Customer.objects.get_or_create(user=request.user, defaults={'name': request.user.username, 'email': request.user.email})

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)

def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']

    if request.user.is_authenticated:
        Customer.objects.get_or_create(user=request.user, defaults={'name': request.user.username, 'email': request.user.email})

    context = {'items': data['items'], 'order': data['order'], 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    data = cartData(request)
    cartItems = data['cartItems']

    if request.user.is_authenticated:
        Customer.objects.get_or_create(user=request.user, defaults={'name': request.user.username, 'email': request.user.email})

    context = {'items': data['items'], 'order': data['order'], 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user, defaults={'name': request.user.username, 'email': request.user.email})
    else:
        return JsonResponse({'error': 'User is not authenticated'}, status=400)

    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user, defaults={'name': request.user.username, 'email': request.user.email})
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)
