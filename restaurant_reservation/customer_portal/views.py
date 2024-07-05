from django.http import JsonResponse
from rest_framework.decorators import api_view
from .models import Customer
from .serializers import CustomerSerializer
from admin_portal.models import Restaurant, Reservation
from admin_portal.serializers import RestaurantSerializer, ReservationSerializer
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timedelta
from django.utils.timezone import make_aware



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

    if not (location and date and time):
        return JsonResponse({'error': 'Location, date, and time parameters are required.'}, status=400)

    date_time_str = f"{date} {time}"
    date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')

    available_restaurants = []
    restaurants = Restaurant.objects.filter(location=location)

    for restaurant in restaurants:
        reservations = Reservation.objects.filter(restaurant=restaurant, reservation_time=date_time)
        reserved_seats = sum(reservation.num_people for reservation in reservations)
        available_seats = restaurant.capacity - reserved_seats

        available_restaurants.append({
            'id': restaurant.pk,
            'name': restaurant.name,
            'capacity': restaurant.capacity,
            'available_seats': available_seats,
            'location': restaurant.location
        })

    return JsonResponse(available_restaurants, safe=False)    

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

@api_view(['POST'])
def book_reservation(request):
    data = request.data
    try:
        restaurant = Restaurant.objects.get(restaurant_id=data['restaurant_id'])
        reservation_time = datetime.strptime(data['reservation_time'], '%Y-%m-%dT%H:%M:%SZ')

        # Calculate available seats
        reservations = Reservation.objects.filter(
            restaurant=restaurant,
            reservation_time__gte=reservation_time - timedelta(minutes=45),
            reservation_time__lt=reservation_time + timedelta(minutes=45),
            status=True
        )

        # Check for table availability
        tables_of_6 = [i for i in range(1, restaurant.tables_of_6 + 1)]
        tables_of_4 = [i for i in range(1, restaurant.tables_of_4 + 1)]
        tables_of_2 = [i for i in range(1, restaurant.tables_of_2 + 1)]

        for reservation in reservations:
            if reservation.table_type == 6:
                if reservation.table_number in tables_of_6:
                    tables_of_6.remove(reservation.table_number)
            elif reservation.table_type == 4:
                if reservation.table_number in tables_of_4:
                    tables_of_4.remove(reservation.table_number)
            elif reservation.table_type == 2:
                if reservation.table_number in tables_of_2:
                    tables_of_2.remove(reservation.table_number)

        # Allocate table
        allocated_table = None
        if data['num_people'] <= 2 and tables_of_2:
            allocated_table = (2, tables_of_2[0])
        elif data['num_people'] <= 4 and tables_of_4:
            allocated_table = (4, tables_of_4[0])
        elif data['num_people'] <= 6 and tables_of_6:
            allocated_table = (6, tables_of_6[0])

        if allocated_table:
            table_type, table_number = allocated_table
            reservation = Reservation(
                restaurant=restaurant,
                customer_mobile=data['customer_mobile'],
                num_people=data['num_people'],
                reservation_time=reservation_time,
                table_type=table_type,
                table_number=table_number,
                status=True
            )
            reservation.save()
            return JsonResponse({'message': 'Reservation successful', 'table_type': table_type, 'table_number': table_number})
        else:
            return JsonResponse({'message': 'No available seats at this time'}, status=400)
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
