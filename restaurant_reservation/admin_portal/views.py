from django.http import JsonResponse
from rest_framework.decorators import api_view
from .models import Restaurant, Reservation, Admin
from .serializers import RestaurantSerializer
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime,timedelta
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime



@api_view(['POST'])
def admin_register(request):
    data = request.data
    if Admin.objects.filter(employee_id=data['employee_id']).exists():
        return JsonResponse({'message': 'Employee ID already exists'}, status=400)
    
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
        capacity = serializer.validated_data['capacity']

        # Calculate table allocations
        tables_of_6 = capacity // 10  # Reduced initial allocation for tables of 6
        remaining_capacity = capacity - (tables_of_6 * 6)

        tables_of_4 = (remaining_capacity // 4) * 2 // 3  # Allocate 2/3 of remaining to tables of 4
        remaining_capacity = remaining_capacity - (tables_of_4 * 4)

        tables_of_2 = remaining_capacity // 2  # Allocate remaining to tables of 2
        remaining_capacity = remaining_capacity % 2

        waiting_seats = remaining_capacity  # Any remaining capacity used as waiting seats

        # Ensure there are more tables of 2 and 4 than tables of 6
        while tables_of_6 >= tables_of_2 + tables_of_4:
            if tables_of_6 > 0:
                tables_of_6 -= 1
                remaining_capacity += 6

                tables_of_4 += remaining_capacity // 4
                remaining_capacity = remaining_capacity % 4

                tables_of_2 += remaining_capacity // 2
                remaining_capacity = remaining_capacity % 2

                waiting_seats = remaining_capacity

        # Save the restaurant with table allocations
        restaurant = Restaurant(
            name=serializer.validated_data['name'],
            capacity=capacity,
            location=serializer.validated_data['location'],
            tables_of_2=tables_of_2,
            tables_of_4=tables_of_4,
            tables_of_6=tables_of_6,
            waiting_seats=waiting_seats
        )
        restaurant.save()

        # Update serializer with the saved restaurant data
        serializer = RestaurantSerializer(restaurant)
        return JsonResponse(serializer.data, status=201)
    return JsonResponse(serializer.errors, status=400)
@api_view(['POST'])
def book_reservation(request):
    data = request.data
    try:
        restaurant = Restaurant.objects.get(restaurant_id=data['restaurant_id'])
        reservation_time = parse_datetime(data['reservation_time'])

        # Calculate available seats
        reservations = Reservation.objects.filter(
            restaurant=restaurant,
            reservation_time__gte=reservation_time - timedelta(minutes=45),
            reservation_time__lt=reservation_time + timedelta(minutes=45),
            status=True
        )

        # Check for table availability
        tables_of_6 = list(range(1, restaurant.tables_of_6 + 1))
        tables_of_4 = list(range(1, restaurant.tables_of_4 + 1))
        tables_of_2 = list(range(1, restaurant.tables_of_2 + 1))

        for reservation in reservations:
            if reservation.table_type == 6 and reservation.table_number in tables_of_6:
                tables_of_6.remove(reservation.table_number)
            elif reservation.table_type == 4 and reservation.table_number in tables_of_4:
                tables_of_4.remove(reservation.table_number)
            elif reservation.table_type == 2 and reservation.table_number in tables_of_2:
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
            return JsonResponse({'message': 'Reservation successful', 'table_number': table_number})
        else:
            return JsonResponse({'message': 'No available seats at this time'}, status=400)
    except Restaurant.DoesNotExist:
        return JsonResponse({'message': 'Restaurant not found'}, status=404)

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

        # Calculate available seats
        reservations = Reservation.objects.filter(
            restaurant=restaurant,
            reservation_time__date=reservation_time.date()
        )
        total_reserved = sum([r.num_people for r in reservations])
        available_seats = restaurant.capacity - total_reserved

        if available_seats >= data['num_people']:
            # Check for overlapping reservations
            overlapping_reservations = reservations.filter(
                reservation_time__gte=reservation_time - timedelta(minutes=45),
                reservation_time__lte=reservation_time + timedelta(minutes=45)
            )
            if overlapping_reservations.exists():
                available_time_slots = [
                    {
                        'available_after': (reservation.reservation_time + timedelta(minutes=45)).strftime('%Y-%m-%d %H:%M:%S'),
                        'available_before': (reservation.reservation_time - timedelta(minutes=45)).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    for reservation in overlapping_reservations
                ]
                return JsonResponse({'message': 'Time slot overlaps with existing reservations', 'available_time_slots': available_time_slots}, status=400)
            
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

@api_view(['POST'])
def check_available_tables(request):
    data = request.POST  # Assuming you are sending data as form data
    try:
        restaurant_id = int(data['restaurant_id'])
        date_time = make_aware(datetime.strptime(data['reservation_time'], '%Y-%m-%dT%H:%M:%SZ'))
        
        try:
            restaurant = Restaurant.objects.get(restaurant_id=restaurant_id)
        except Restaurant.DoesNotExist:
            return JsonResponse({'message': 'Restaurant not found'}, status=404)

        reservations = Reservation.objects.filter(
            restaurant=restaurant,
            reservation_time__gte=date_time - timedelta(minutes=45),
            reservation_time__lt=date_time + timedelta(minutes=45),
            status=True
        )

        tables_of_6 = restaurant.tables_of_6
        tables_of_4 = restaurant.tables_of_4
        tables_of_2 = restaurant.tables_of_2

        for reservation in reservations:
            if reservation.table_type == 6:
                tables_of_6 -= 1
            elif reservation.table_type == 4:
                tables_of_4 -= 1
            elif reservation.table_type == 2:
                tables_of_2 -= 1

        return JsonResponse({
            'restaurant_id': restaurant_id,
            'date_time': date_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'tables_of_6': tables_of_6,
            'tables_of_4': tables_of_4,
            'tables_of_2': tables_of_2
        })

    except KeyError:
        return JsonResponse({'message': 'Missing parameters'}, status=400)
    except ValueError:
        return JsonResponse({'message': 'Invalid restaurant ID'}, status=400)