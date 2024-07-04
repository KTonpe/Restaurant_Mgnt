from django.http import JsonResponse
from rest_framework.decorators import api_view
from .models import Restaurant, Reservation, Admin
from .serializers import RestaurantSerializer
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from django.utils.timezone import make_aware


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
        reservation_time = datetime.strptime(data['reservation_time'], '%Y-%m-%dT%H:%M:%SZ')
        reservation_time = make_aware(reservation_time)

        # Check for overlapping reservations
        overlapping_reservations = Reservation.objects.filter(
            restaurant=restaurant,
            reservation_time=reservation_time
        )

        if overlapping_reservations.exists():
            return JsonResponse({'message': 'The slot is already booked'}, status=400)

        # Calculate available seats
        reservations = Reservation.objects.filter(
            restaurant=restaurant,
            reservation_time__date=reservation_time.date(),
            reservation_time__time=reservation_time.time()
        )
        total_reserved = sum([r.num_people for r in reservations])
        available_seats = restaurant.capacity - total_reserved

        if available_seats >= data['num_people']:
            reservation = Reservation(
                restaurant=restaurant,
                customer_mobile=data['customer_mobile'],
                num_people=data['num_people'],
                reservation_time=reservation_time,
                status=True
            )
            reservation.save()
            return JsonResponse({'message': 'Reservation successful'})
        else:
            return JsonResponse({'message': 'Not enough seats available'}, status=400)
    except Restaurant.DoesNotExist:
        return JsonResponse({'message': 'Restaurant not found'}, status=404)
    
@api_view(['DELETE'])
def delete_reservation(request):
    data = request.data
    try:
        restaurant = Restaurant.objects.get(restaurant_id=data['restaurant_id'])
        reservation_time = datetime.strptime(data['reservation_time'], '%Y-%m-%dT%H:%M:%SZ')
        reservation_time = make_aware(reservation_time)

        # Find the reservation
        reservation = Reservation.objects.filter(
            restaurant=restaurant,
            reservation_time=reservation_time,
            customer_mobile=data['customer_mobile']
        ).first()

        if reservation:
            num_people = reservation.num_people
            reservation.delete()

            # Update available seats
            reservations = Reservation.objects.filter(
                restaurant=restaurant,
                reservation_time__date=reservation_time.date(),
                reservation_time__time=reservation_time.time()
            )
            total_reserved = sum([r.num_people for r in reservations])
            available_seats = restaurant.capacity - total_reserved

            return JsonResponse({
                'message': 'Reservation deleted successfully',
                'available_seats': available_seats
            })
        else:
            return JsonResponse({'message': 'Reservation not found'}, status=404)
    except Restaurant.DoesNotExist:
        return JsonResponse({'message': 'Restaurant not found'}, status=404)

@api_view(['GET'])   
def get_reservations_by_restaurant(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(restaurant_id=restaurant_id)
        reservations = Reservation.objects.filter(restaurant=restaurant)

        if reservations.exists():
            reservations_list = []
            for reservation in reservations:
                reservations_list.append({
                    'reservation_id': reservation.id,
                    'customer_mobile': reservation.customer_mobile,
                    'num_people': reservation.num_people,
                    'reservation_time': reservation.reservation_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': reservation.status
                })

            return JsonResponse(reservations_list, safe=False)
        else:
            return JsonResponse({'message': 'No reservations for this restaurant'}, status=200)
        
    except Restaurant.DoesNotExist:
        return JsonResponse({'message': 'Restaurant not found'}, status=404)
