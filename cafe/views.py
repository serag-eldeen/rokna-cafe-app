from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import csrf_exempt
from .models import Table, Room, Item, TableReservation, RoomReservation, Order, OrderItem, Testimonial, ITEM_TYPES  # Import ITEM_TYPESfrom django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
import os
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login
from django.views import View
from django.contrib.auth.models import User
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)  # For debugging

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        phone_number = request.POST.get('phone_number')
        if form.is_valid() and phone_number:
            user = form.save()  # Save the User
            UserProfile.objects.create(user=user, phone_number=phone_number)  # Save phone number
            return redirect('login')
        else:
            return render(request, 'cafe/signup.html', {
                'form': form,
                'error': 'Please provide a valid username, password, and phone number.'
            })
    else:
        form = UserCreationForm()
    return render(request, 'cafe/signup.html', {'form': form})

def home(request):
    if request.method == 'POST':
        author = request.POST.get('author')
        content = request.POST.get('content')
        if author and content:
            Testimonial.objects.create(author=author, content=content)
        return redirect('cafe:home')

    menu_dir = os.path.join(settings.STATICFILES_DIRS[0], 'menu')
    image_files = [f for f in os.listdir(menu_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.gif'))]
    testimonials = Testimonial.objects.all().order_by('-created_at')
    points = 0
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            points = user_profile.points
        except UserProfile.DoesNotExist:
            points = 0  # Default if no profile exists yet

    return render(request, 'cafe/home.html', {
        'menu_images': image_files,
        'testimonials': testimonials,
        'points': points  # Add points to context
    })
# views.py
class CustomLoginView(View):
    template_name = 'cafe/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        identifier = request.POST.get('username')  # Could be phone number or username
        password = request.POST.get('password')
        
        # Authenticate using the custom backend
        user = authenticate(request, username=identifier, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('cafe:home')
        else:
            return render(request, self.template_name, {
                'error': 'Invalid phone number/username or password.'
            })
def submit_feedback(request):
    if request.method == 'POST':
        author = request.POST.get('author')
        content = request.POST.get('content')
        if author and content:
            Testimonial.objects.create(author=author, content=content)
        return redirect('cafe:home')
    return redirect('cafe:home')  # Redirect GET requests to home

# Logout View (No login required)
def logout(request):
    auth_logout(request)  # Logs out the user and deletes the session
    return redirect('cafe:home')  # Redirect to home page

# Reserve Table View
@login_required
def reserve_table(request):
    tables = Table.objects.all()
    context = {'tables': tables}

    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        duration = int(request.POST.get('duration'))

        try:
            # Parse date and time
            reservation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            start_datetime = datetime.combine(reservation_date, start_time)
            end_datetime = start_datetime + timedelta(minutes=duration)

            # Get the table
            table = Table.objects.get(number=table_number)

            # Check for overlapping reservations
            existing_reservations = TableReservation.objects.filter(
                table=table,
                date=reservation_date
            )

            for res in existing_reservations:
                res_start = datetime.combine(res.date, res.start_time)
                res_end = res_start + timedelta(minutes=res.duration)
                if (start_datetime < res_end) and (end_datetime > res_start):
                    context['error'] = f"Table {table.number} is already reserved from {res.start_time.strftime('%H:%M')} to {res_end.strftime('%H:%M')} on {res.date}."
                    return render(request, 'cafe/reserve_table.html', context)

            # If no conflict, save the reservation
            reservation = TableReservation(
                user=request.user,
                table=table,
                date=reservation_date,
                start_time=start_time,
                duration=duration
            )
            reservation.save()
            context['message'] = f"Table {table.number} reserved successfully for {duration} minutes on {reservation_date} at {start_time.strftime('%H:%M')}."

        except Table.DoesNotExist:
            context['error'] = "Selected table does not exist."
        except ValueError as e:
            context['error'] = "Invalid date or time format."

    return render(request, 'cafe/reserve_table.html', context)

# Reserve PS Room View
@login_required
def reserve_ps_room(request):
    rooms = Room.objects.all()
    context = {'rooms': rooms}

    if request.method == 'POST':
        room_number = request.POST.get('room_number')
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        duration = int(request.POST.get('duration'))

        try:
            # Parse date and time
            reservation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            start_datetime = datetime.combine(reservation_date, start_time)
            end_datetime = start_datetime + timedelta(minutes=duration)

            # Get the room
            room = Room.objects.get(number=room_number)

            # Check for overlapping reservations
            existing_reservations = RoomReservation.objects.filter(
                room=room,
                date=reservation_date
            )

            for res in existing_reservations:
                res_start = datetime.combine(res.date, res.start_time)
                res_end = res_start + timedelta(minutes=res.duration)
                if (start_datetime < res_end) and (end_datetime > res_start):
                    context['error'] = f"Room {room.number} is already reserved from {res.start_time.strftime('%H:%M')} to {res_end.strftime('%H:%M')} on {res.date}."
                    return render(request, 'cafe/reserve_ps_room.html', context)

            # If no conflict, save the reservation
            reservation = RoomReservation(
                user=request.user,
                room=room,
                date=reservation_date,
                start_time=start_time,
                duration=duration
            )
            reservation.save()
            context['message'] = f"Room {room.number} reserved successfully for {duration} minutes on {reservation_date} at {start_time.strftime('%H:%M')}."

        except Room.DoesNotExist:
            context['error'] = "Selected room does not exist."
        except ValueError as e:
            context['error'] = "Invalid date or time format."

    return render(request, 'cafe/reserve_ps_room.html', context)

@login_required
def place_order(request):
    tables = Table.objects.all()
    rooms = Room.objects.all()
    items = Item.objects.filter(is_available=True)
    item_types = ITEM_TYPES

    if request.method == 'POST':
        location = request.POST.get('location')  # Expecting "table_1" or "room_1"
        item_type = request.POST.get('item_type')
        selected_items = []

        # Debug: Print the entire POST data
        print("POST Data:", request.POST)

        if item_type:
            items = items.filter(item_type=item_type)

        for item in items:
            if f'item_{item.id}' in request.POST:
                quantity = request.POST.get(f'quantity_{item.id}', 1)
                print(f"Item {item.id} selected, raw quantity: {quantity}")
                try:
                    quantity = int(quantity)
                    if quantity < 1:
                        quantity = 1
                except (ValueError, TypeError):
                    quantity = 1
                print(f"Processed quantity for item {item.id}: {quantity}")
                selected_items.append((item, quantity))

        if not selected_items:
            return render(request, 'cafe/place_order.html', {
                'items': items,
                'tables': tables,
                'rooms': rooms,
                'item_types': item_types,
                'selected_type': item_type,
                'error': 'No items selected'
            })

        if not location:
            return render(request, 'cafe/place_order.html', {
                'items': items,
                'tables': tables,
                'rooms': rooms,
                'item_types': item_types,
                'selected_type': item_type,
                'error': 'Please select a location'
            })

        # Validate location
        try:
            location_type, location_number = location.split('_')
            location_number = int(location_number)  # Ensure it's a number
            if location_type == 'table' and not Table.objects.filter(number=location_number).exists():
                raise ValueError("Invalid table number")
            elif location_type == 'room' and not Room.objects.filter(number=location_number).exists():
                raise ValueError("Invalid room number")
            elif location_type not in ['table', 'room']:
                raise ValueError("Invalid location type")
        except (ValueError, IndexError):
            return render(request, 'cafe/place_order.html', {
                'items': items,
                'tables': tables,
                'rooms': rooms,
                'item_types': item_types,
                'selected_type': item_type,
                'error': 'Invalid location selected'
            })

        order = Order(user=request.user, location=location)
        order.save()
        for item, quantity in selected_items:
            if not item.is_available:
                order.delete()
                return render(request, 'cafe/place_order.html', {
                    'items': items,
                    'tables': tables,
                    'rooms': rooms,
                    'item_types': item_types,
                    'selected_type': item_type,
                    'error': f'{item.name} is out of stock'
                })
            order_item = OrderItem.objects.create(order=order, item=item, quantity=quantity)
            print(f"Saved OrderItem: {order_item.item.name} x{order_item.quantity}")

        # Format location for user-friendly message
        location_display = f"{location_type.capitalize()} {location_number}"
        return render(request, 'cafe/place_order.html', {
            'items': items,
            'tables': tables,
            'rooms': rooms,
            'item_types': item_types,
            'selected_type': item_type,
            'message': f'Order placed successfully for {location_display}!'
        })

    return render(request, 'cafe/place_order.html', {
        'items': items,
        'tables': tables,
        'rooms': rooms,
        'item_types': item_types,
        'selected_type': None
    })
# Staff Check
def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_page(request):
    context = {}
    return render(request, 'cafe/admin_page.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def tables_rooms_page(request):
    context = {
        'tables': Table.objects.all(),
        'rooms': Room.objects.all(),
    }
    return render(request, 'cafe/tables_rooms_page.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def items_page(request):
    context = {
        'items': Item.objects.all(),
        'item_types': ITEM_TYPES,
    }
    return render(request, 'cafe/items_page.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def orders_page(request):
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    context = {
        'orders': Order.objects.filter(created_at__date=selected_date),
        'selected_date': selected_date,
    }
    return render(request, 'cafe/orders_page.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt  # Temporarily for testing; secure with CSRF token later
def update_reservation_attendance(request, reservation_type, reservation_id):
    if request.method == 'POST':
        logger.info(f"Received POST request for {reservation_type} reservation ID {reservation_id}")
        try:
            if reservation_type == 'table':
                reservation = TableReservation.objects.get(id=reservation_id)
            elif reservation_type == 'room':
                reservation = RoomReservation.objects.get(id=reservation_id)
            else:
                logger.error(f"Invalid reservation type: {reservation_type}")
                return HttpResponse('Invalid reservation type', status=400)

            attended = request.POST.get('attended')
            logger.info(f"Attended value received: {attended}")
            if attended == 'true':
                reservation.attended = True
                # Increase user's points
                user_profile = UserProfile.objects.get(user=reservation.user)
                user_profile.points += 10  # Example: +10 points per attended reservation
                user_profile.save()
                logger.info(f"Increased points for {reservation.user.username} to {user_profile.points}")
            elif attended == 'false':
                reservation.attended = False
            else:
                logger.error(f"Invalid attended value: {attended}")
                return HttpResponse('Invalid attended value', status=400)

            reservation.save()
            logger.info(f"Updated {reservation_type} reservation {reservation_id} with attended={reservation.attended}")
            return JsonResponse({'status': 'success', 'attended': reservation.attended})
        except (TableReservation.DoesNotExist, RoomReservation.DoesNotExist):
            logger.error(f"Reservation not found: {reservation_type} {reservation_id}")
            return HttpResponse('Reservation not found', status=404)
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile not found for user: {reservation.user.username}")
            return HttpResponse('User profile not found', status=500)
        except Exception as e:
            logger.error(f"Error updating attendance: {str(e)}")
            return HttpResponse(f'Error: {str(e)}', status=500)
    logger.warning(f"Invalid method: {request.method}")
    return HttpResponse('Method not allowed', status=405)

@login_required
@user_passes_test(lambda u: u.is_staff)
def table_reservations_page(request):
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    context = {
        'table_reservations': TableReservation.objects.filter(date=selected_date),
        'selected_date': selected_date,
    }
    return render(request, 'cafe/table_reservations_page.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def room_reservations_page(request):
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    context = {
        'room_reservations': RoomReservation.objects.filter(date=selected_date),
        'selected_date': selected_date,
    }
    return render(request, 'cafe/room_reservations_page.html', context)

# Update get_room_reservations to include attended status
@login_required
@csrf_exempt
def get_room_reservations(request):
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    reservations = RoomReservation.objects.filter(date=selected_date).order_by('start_time')

    data = {
        'room_reservations': [
            {
                'id': res.id,
                'user': res.user.username,
                'room': res.room.number,
                'date': res.date.strftime('%Y-%m-%d'),
                'start_time': res.start_time.strftime('%H:%M'),
                'duration': res.duration,
                'attended': res.attended  # Include attended status
            } for res in reservations
        ]
    }
    return JsonResponse(data)

@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def get_new_room_reservations(request):
    last_reservation_id = int(request.GET.get('last_reservation_id', 0))
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    new_reservations = RoomReservation.objects.filter(
        id__gt=last_reservation_id,
        date=selected_date
    ).order_by('start_time')

    reservations_data = [
        {
            'id': res.id,
            'user': res.user.username,
            'room': res.room.number,
            'date': res.date.strftime('%Y-%m-%d'),
            'start_time': res.start_time.strftime('%H:%M')
        } for res in new_reservations
    ]
    return JsonResponse({'room_reservations': reservations_data})

@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def get_orders(request):
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    orders = Order.objects.filter(created_at__date=selected_date).order_by('created_at')

    data = {
        'orders': [
            {
                'id': order.id,
                'user': order.user.username,
                'location': order.location,  # Changed from 'table' to 'location'
                'created_at': timezone.localtime(order.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                'status': order.status,
                'items': [{'name': oi.item.name, 'quantity': oi.quantity} for oi in order.orderitem_set.all()]
            } for order in orders
        ]
    }
    return JsonResponse(data)

@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def get_new_orders(request):
    last_order_id = int(request.GET.get('last_order_id', 0))
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    new_orders = Order.objects.filter(
        id__gt=last_order_id,
        created_at__date=selected_date
    ).order_by('created_at')

    orders_data = [
        {
            'id': order.id,
            'user': order.user.username,
            'location': order.location,  # Changed from 'table' to 'location'
            'created_at': timezone.localtime(order.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'status': order.status,
            'items': [{'name': oi.item.name, 'quantity': oi.quantity} for oi in order.orderitem_set.all()]
        }
        for order in new_orders
    ]
    return JsonResponse({'orders': orders_data})

@login_required
@csrf_exempt
def get_table_reservations(request):
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    reservations = TableReservation.objects.filter(date=selected_date).order_by('start_time')

    data = {
        'table_reservations': [
            {
                'id': res.id,
                'user': res.user.username,
                'table': res.table.number,
                'date': res.date.strftime('%Y-%m-%d'),
                'start_time': res.start_time.strftime('%H:%M'),
                'duration': res.duration,
                'attended': res.attended  # Include attended status
            } for res in reservations
        ]
    }
    return JsonResponse(data)

@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def get_new_table_reservations(request):
    last_reservation_id = int(request.GET.get('last_reservation_id', 0))
    date_str = request.GET.get('date', '')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    new_reservations = TableReservation.objects.filter(
        id__gt=last_reservation_id,
        date=selected_date
    ).order_by('start_time')

    reservations_data = [
        {
            'id': res.id,
            'user': res.user.username,
            'table': res.table.number,
            'date': res.date.strftime('%Y-%m-%d'),
            'start_time': res.start_time.strftime('%H:%M')
        } for res in new_reservations
    ]
    return JsonResponse({'table_reservations': reservations_data})

@login_required
@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
def update_order_status(request, order_id):
    if request.method == 'POST':
        logger.info(f"Received POST request to update order ID {order_id}")
        try:
            order = Order.objects.get(id=order_id)
            new_status = request.POST.get('status')
            valid_statuses = ['Pending', 'Preparing', 'Ready', 'Delivered']
            
            if new_status not in valid_statuses:
                logger.error(f"Invalid status value: {new_status}")
                return HttpResponse('Invalid status', status=400)

            # Check if the status is changing to 'Delivered' and wasn’t already 'Delivered'
            if new_status == 'Delivered' and order.status != 'Delivered':
                try:
                    user_profile = UserProfile.objects.get(user=order.user)
                    user_profile.points += 10  # Award 10 points (adjust as needed)
                    user_profile.save()
                    logger.info(f"Increased points for {order.user.username} to {user_profile.points} for order {order_id}")
                except UserProfile.DoesNotExist:
                    logger.error(f"UserProfile not found for user: {order.user.username}")
                    return HttpResponse('User profile not found', status=500)

            order.status = new_status
            order.save()
            logger.info(f"Updated order {order_id} to status={order.status}")
            return HttpResponse(status=200)
        except Order.DoesNotExist:
            logger.error(f"Order not found: {order_id}")
            return HttpResponse('Order not found', status=404)
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return HttpResponse(f'Error: {str(e)}', status=500)
    logger.warning(f"Invalid method: {request.method}")
    return HttpResponse('Method not allowed', status=405)
 
@csrf_exempt
@login_required
@user_passes_test(is_staff)
def add_table(request):
    if request.method == 'POST':
        number = request.POST.get('number')
        if Table.objects.filter(number=number).exists():
            return render(request, 'cafe/add_table.html', {
                'tables': Table.objects.all(),
                'rooms': Room.objects.all(),
                'items': Item.objects.all(),
                'table_reservations': TableReservation.objects.all(),
                'room_reservations': RoomReservation.objects.all(),
                'orders': Order.objects.all(),
                'error': 'Table number already exists'
            })
        Table.objects.create(number=number)
        return redirect('cafe:tables_rooms_page')
    return redirect('cafe:tables_rooms_page')

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def edit_table(request, table_id):
    try:
        table = Table.objects.get(id=table_id)
        if request.method == 'POST':
            new_number = request.POST.get('number')
            if new_number != str(table.number) and Table.objects.filter(number=new_number).exists():
                return render(request, 'cafe/admin_page.html', {
                    'tables': Table.objects.all(),
                    'rooms': Room.objects.all(),
                    'items': Item.objects.all(),
                    'table_reservations': TableReservation.objects.all(),
                    'room_reservations': RoomReservation.objects.all(),
                    'orders': Order.objects.all(),
                    'error': 'Table number already exists'
                })
            table.number = new_number
            table.is_available = request.POST.get('is_available') == 'true'
            table.save()
            return redirect('cafe:admin_page')
        return redirect('cafe:admin_page')
    except Table.DoesNotExist:
        return render(request, 'cafe/admin_page.html', {
            'tables': Table.objects.all(),
            'rooms': Room.objects.all(),
            'items': Item.objects.all(),
            'table_reservations': TableReservation.objects.all(),
            'room_reservations': RoomReservation.objects.all(),
            'orders': Order.objects.all(),
            'error': 'Table not found'
        })

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def delete_table(request, table_id):
    try:
        if request.method == 'POST':
            Table.objects.get(id=table_id).delete()
            return redirect('cafe:admin_page')
        return redirect('cafe:admin_page')
    except Table.DoesNotExist:
        return render(request, 'cafe/admin_page.html', {
            'tables': Table.objects.all(),
            'rooms': Room.objects.all(),
            'items': Item.objects.all(),
            'table_reservations': TableReservation.objects.all(),
            'room_reservations': RoomReservation.objects.all(),
            'orders': Order.objects.all(),
            'error': 'Table not found'
        })

# Admin Room Management
@csrf_exempt
@login_required
@user_passes_test(is_staff)
def add_room(request):
    if request.method == 'POST':
        number = request.POST.get('number')
        if Room.objects.filter(number=number).exists():
            return render(request, 'cafe/admin_page.html', {
                'tables': Table.objects.all(),
                'rooms': Room.objects.all(),
                'items': Item.objects.all(),
                'table_reservations': TableReservation.objects.all(),
                'room_reservations': RoomReservation.objects.all(),
                'orders': Order.objects.all(),
                'error': 'Room number already exists'
            })
        Room.objects.create(number=number)
        return redirect('cafe:tables_rooms_page')
    return redirect('cafe:tables_rooms_page')

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def edit_room(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
        if request.method == 'POST':
            new_number = request.POST.get('number')
            if new_number != str(room.number) and Room.objects.filter(number=new_number).exists():
                return render(request, 'cafe/admin_page.html', {
                    'tables': Table.objects.all(),
                    'rooms': Room.objects.all(),
                    'items': Item.objects.all(),
                    'table_reservations': TableReservation.objects.all(),
                    'room_reservations': RoomReservation.objects.all(),
                    'orders': Order.objects.all(),
                    'error': 'Room number already exists'
                })
            room.number = new_number
            room.is_available = request.POST.get('is_available') == 'true'
            room.save()
            return redirect('cafe:admin_page')
        return redirect('cafe:admin_page')
    except Room.DoesNotExist:
        return render(request, 'cafe/admin_page.html', {
            'tables': Table.objects.all(),
            'rooms': Room.objects.all(),
            'items': Item.objects.all(),
            'table_reservations': TableReservation.objects.all(),
            'room_reservations': RoomReservation.objects.all(),
            'orders': Order.objects.all(),
            'error': 'Room not found'
        })

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def delete_room(request, room_id):
    try:
        if request.method == 'POST':
            Room.objects.get(id=room_id).delete()
            return redirect('cafe:admin_page')
        return redirect('cafe:admin_page')
    except Room.DoesNotExist:
        return render(request, 'cafe/admin_page.html', {
            'tables': Table.objects.all(),
            'rooms': Room.objects.all(),
            'items': Item.objects.all(),
            'table_reservations': TableReservation.objects.all(),
            'room_reservations': RoomReservation.objects.all(),
            'orders': Order.objects.all(),
            'error': 'Room not found'
        })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Item, ITEM_TYPES

# Custom decorator to check if user is staff
def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def add_item(request):
    """
    Handle adding a new item via POST request and render items_page.html.
    
    Args:
        request: HTTP request object.
    
    Returns:
        Renders items_page.html with success or error message.
    """
    # Common context for rendering items_page.html
    context = {
        'items': Item.objects.all(),
        'item_types': ITEM_TYPES
    }

    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        item_type = request.POST.get('item_type')  # Get the selected item_type
        image = request.FILES.get('image')

        # Validate inputs
        if not name or not price or not item_type:
            context['error'] = 'All fields (name, price, item type) are required.'
            return render(request, 'cafe/items_page.html', context)

        try:
            price = float(price)  # Ensure price is a valid number
            # Verify item_type is valid
            if item_type not in dict(ITEM_TYPES):
                raise ValueError("Invalid item type selected.")
            
            # Create and save the new item
            item = Item(
                name=name,
                price=price,
                item_type=item_type,  # Explicitly set item_type
                image=image
            )
            item.save()
            context['message'] = f'Item "{name}" added successfully!'
            # Refresh items list to include the new item
            context['items'] = Item.objects.all()
            return render(request, 'cafe/items_page.html', context)
        except ValueError as e:
            context['error'] = str(e)
            return render(request, 'cafe/items_page.html', context)

    # If not POST, render items_page.html (e.g., initial GET request)
    return render(request, 'cafe/items_page.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def edit_item(request, item_id):
    try:
        item = Item.objects.get(id=item_id)
        if request.method == 'POST':
            new_name = request.POST.get('name')
            new_price = request.POST.get('price')
            if new_name != item.name and Item.objects.filter(name=new_name).exists():
                return render(request, 'cafe/admin_page.html', {
                    'tables': Table.objects.all(),
                    'rooms': Room.objects.all(),
                    'items': Item.objects.all(),
                    'table_reservations': TableReservation.objects.all(),
                    'room_reservations': RoomReservation.objects.all(),
                    'orders': Order.objects.all(),
                    'error': 'Item name already exists'
                })
            try:
                item.name = new_name
                item.price = float(new_price)
                item.is_available = request.POST.get('is_available') == 'true'
                item.save()
                return redirect('cafe:admin_page')
            except ValueError:
                return render(request, 'cafe/admin_page.html', {
                    'tables': Table.objects.all(),
                    'rooms': Room.objects.all(),
                    'items': Item.objects.all(),
                    'table_reservations': TableReservation.objects.all(),
                    'room_reservations': RoomReservation.objects.all(),
                    'orders': Order.objects.all(),
                    'error': 'Invalid price'
                })
        return redirect('cafe:admin_page')
    except Item.DoesNotExist:
        return render(request, 'cafe/admin_page.html', {
            'tables': Table.objects.all(),
            'rooms': Room.objects.all(),
            'items': Item.objects.all(),
            'table_reservations': TableReservation.objects.all(),
            'room_reservations': RoomReservation.objects.all(),
            'orders': Order.objects.all(),
            'error': 'Item not found'
        })

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def delete_item(request, item_id):
    try:
        if request.method == 'POST':
            Item.objects.get(id=item_id).delete()
            return redirect('cafe:admin_page')
        return redirect('cafe:admin_page')
    except Item.DoesNotExist:
        return render(request, 'cafe/admin_page.html', {
            'tables': Table.objects.all(),
            'rooms': Room.objects.all(),
            'items': Item.objects.all(),
            'table_reservations': TableReservation.objects.all(),
            'room_reservations': RoomReservation.objects.all(),
            'orders': Order.objects.all(),
            'error': 'Item not found'
        })