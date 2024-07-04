from django.http import JsonResponse
from rest_framework.decorators import api_view
from .models import Restaurant, Reservation, Admin
from .serializers import RestaurantSerializer, ReservationSerializer
from django.contrib.auth.hashers import make_password, check_password

@api_view(['POST'])
def admin_register(request):
    data = request.data
    admin = Admin(employee_id=data['employee_id'], password=make_password(data['password']))
    admin.save()
    return JsonResponse({'message': 'Admin registered successfully'})

@api_view(['POST'])
def admin_login(request):
    data = request.data
    try:
        admin = Admin.objects.get(employee_id=data['employee_id'])
        if check_password(data['password'], admin.password):
            return JsonResponse({'message': 'Login successful'})
        else:
            return JsonResponse({'message': 'Invalid credentials'}, status=401)
    except Admin.DoesNotExist:
        return JsonResponse({'message': 'Admin not found'}, status=404)

@api_view(['POST'])
def add_restaurant(request):
    serializer = RestaurantSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data, status=201)
    return JsonResponse(serializer.errors, status=400)

@api_view(['PUT'])
def update_restaurant(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(restaurant_id=restaurant_id)
        serializer = RestaurantSerializer(restaurant, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)
    except Restaurant.DoesNotExist:
        return JsonResponse({'message': 'Restaurant not found'}, status=404)

@api_view(['DELETE'])
def delete_restaurant(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(restaurant_id=restaurant_id)
        restaurant.delete()
        return JsonResponse({'message': 'Restaurant deleted successfully'})
    except Restaurant.DoesNotExist:
        return JsonResponse({'message': 'Restaurant not found'}, status=404)

@api_view(['POST'])
def book_reservation(request):
    data = request.data
    try:
        restaurant = Restaurant.objects.get(restaurant_id=data['restaurant_id'])
        if restaurant.capacity >= data['num_people']:
            reservation = Reservation(
                restaurant=restaurant,
                customer_mobile=data['customer_mobile'],
                num_people=data['num_people'],
                reservation_time=data['reservation_time'],
                status=True
            )
            reservation.save()
            restaurant.capacity -= data['num_people']
            restaurant.save()
            return JsonResponse({'message': 'Reservation successful'})
        else:
            return JsonResponse({'message': 'Not enough seats available'}, status=400)
    except Restaurant.DoesNotExist:
        return JsonResponse({'message': 'Restaurant not found'}, status=404)
