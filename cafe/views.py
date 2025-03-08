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
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View

def home(request):
    if request.method == 'POST':
        author = request.POST.get('author')
        content = request.POST.get('content')
        if author and content:
            Testimonial.objects.create(author=author, content=content)
        return redirect('cafe:home')  # Redirect to refresh the page

    menu_dir = os.path.join(settings.STATICFILES_DIRS[0], 'menu')
    image_files = [f for f in os.listdir(menu_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.gif'))]
    testimonials = Testimonial.objects.all().order_by('-created_at')  # Latest first
    return render(request, 'cafe/home.html', {
        'menu_images': image_files,
        'testimonials': testimonials
    })
class CustomLoginView(View):
    template_name = 'cafe/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('cafe:home')  # Redirect to home on success
        else:
            # Pass an error flag to the template
            return render(request, self.template_name, {
                'error': True
            })
def submit_feedback(request):
    if request.method == 'POST':
        author = request.POST.get('author')
        content = request.POST.get('content')
        if author and content:
            Testimonial.objects.create(author=author, content=content)
        return redirect('cafe:home')
    return redirect('cafe:home')  # Redirect GET requests to home


# Signup View (No login required)
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'cafe/signup.html', {'form': form})

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
    if request.method == 'POST':
        items = Item.objects.filter(is_available=True)
        table_number = request.POST.get('table_number')
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
                'tables': Table.objects.all(),
                'item_types': ITEM_TYPES,
                'selected_type': item_type,
                'error': 'No items selected'
            })

        if not table_number:
            return render(request, 'cafe/place_order.html', {
                'items': items,
                'tables': Table.objects.all(),
                'item_types': ITEM_TYPES,
                'selected_type': item_type,
                'error': 'Please select a table number'
            })

        try:
            table = Table.objects.get(number=table_number)
        except Table.DoesNotExist:
            return render(request, 'cafe/place_order.html', {
                'items': items,
                'tables': Table.objects.all(),
                'item_types': ITEM_TYPES,
                'selected_type': item_type,
                'error': 'Invalid table number'
            })

        order = Order(user=request.user, table=table)
        order.save()
        for item, quantity in selected_items:
            if not item.is_available:
                order.delete()
                return render(request, 'cafe/place_order.html', {
                    'items': items,
                    'tables': Table.objects.all(),
                    'item_types': ITEM_TYPES,
                    'selected_type': item_type,
                    'error': f'{item.name} is out of stock'
                })
            order_item = OrderItem.objects.create(order=order, item=item, quantity=quantity)
            print(f"Saved OrderItem: {order_item.item.name} x{order_item.quantity}")

        return render(request, 'cafe/place_order.html', {
            'items': items,
            'tables': Table.objects.all(),
            'item_types': ITEM_TYPES,
            'selected_type': item_type,
            'message': 'Order placed successfully!'
        })

    items = Item.objects.filter(is_available=True)
    tables = Table.objects.all()
    return render(request, 'cafe/place_order.html', {
        'items': items,
        'tables': tables,
        'item_types': ITEM_TYPES,
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
                'duration': res.duration  # Add duration here
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
                'table': order.table.number if order.table else 'None',
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
            'table': order.table.number if order.table else 'None',
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
                'duration': res.duration  # Add duration here
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
        try:
            order = Order.objects.get(id=order_id)
            new_status = request.POST.get('status')
            valid_statuses = ['Pending', 'Preparing', 'Ready', 'Delivered']
            if new_status in valid_statuses:
                order.status = new_status
                order.save()
                return HttpResponse(status=200)
            else:
                return HttpResponse('Invalid status', status=400)
        except Order.DoesNotExist:
            return HttpResponse('Order not found', status=404)
        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=500)
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

@login_required
@user_passes_test(is_staff)
def add_item(request):
    """
    Handle adding a new item via POST request from the admin panel.
    
    Args:
        request: HTTP request object.
    
    Returns:
        Redirect to admin_page on success, or with an error message.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        item_type = request.POST.get('item_type')  # Get the selected item_type
        image = request.FILES.get('image')

        # Validate inputs
        if not name or not price or not item_type:
            return render(request, 'cafe/admin_page.html', {
                'error': 'All fields (name, price, item type) are required.',
                'tables': Table.objects.all(),
                'rooms': Room.objects.all(),
                'items': Item.objects.all(),
                'table_reservations': TableReservation.objects.all(),
                'room_reservations': RoomReservation.objects.all(),
                'orders': Order.objects.all(),
                'item_types': ITEM_TYPES
            })

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
            return redirect('cafe:admin_page')
        except ValueError as e:
            return render(request, 'cafe/admin_page.html', {
                'error': str(e),
                'tables': Table.objects.all(),
                'rooms': Room.objects.all(),
                'items': Item.objects.all(),
                'table_reservations': TableReservation.objects.all(),
                'room_reservations': RoomReservation.objects.all(),
                'orders': Order.objects.all(),
                'item_types': ITEM_TYPES
            })

    # If not POST, redirect back to admin page
    return redirect('cafe:admin_page')
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