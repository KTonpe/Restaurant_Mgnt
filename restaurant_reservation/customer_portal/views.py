from django.http import JsonResponse
from rest_framework.decorators import api_view
from .models import Customer
from .serializers import CustomerSerializer
from admin_portal.models import Restaurant, Reservation
from admin_portal.serializers import RestaurantSerializer, ReservationSerializer
from django.contrib.auth.hashers import make_password, check_password

@api_view(['POST'])
def customer_register(request):
    data = request.data
    customer = Customer(mobile_number=data['mobile_number'], password=make_password(data['password']))
    customer.save()
    return JsonResponse({'message': 'Customer registered successfully'})

@api_view(['POST'])
def customer_login(request):
    data = request.data
    try:
        customer = Customer.objects.get(mobile_number=data['mobile_number'])
        if check_password(data['password'], customer.password):
            return JsonResponse({'message': 'Login successful'})
        else:
            return JsonResponse({'message': 'Invalid credentials'}, status=401)
    except Customer.DoesNotExist:
        return JsonResponse({'message': 'Customer not found'}, status=404)

@api_view(['GET'])
def check_availability(request):
    location = request.GET.get('location')
    date = request.GET.get('date')
    time = request.GET.get('time')
    try:
        restaurants = Restaurant.objects.filter(location=location)
        available_restaurants = []
        for restaurant in restaurants:
            reservations = Reservation.objects.filter(restaurant=restaurant, reservation_time__date=date, reservation_time__time=time)
            total_reserved = sum([r.num_people for r in reservations])
            if restaurant.capacity > total_reserved:
                available_restaurants.append(restaurant)
        serializer = RestaurantSerializer(available_restaurants, many=True)
        return JsonResponse(serializer.data, safe=False)
    except Restaurant.DoesNotExist:
        return JsonResponse({'message': 'No restaurants found'}, status=404)

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

@api_view(['GET'])
def reservation_stats(request, customer_mobile):
    try:
        reservations = Reservation.objects.filter(customer_mobile=customer_mobile)
        serializer = ReservationSerializer(reservations, many=True)
        return JsonResponse(serializer.data, safe=False)
    except Reservation.DoesNotExist:
        return JsonResponse({'message': 'No reservations found'}, status=404)
