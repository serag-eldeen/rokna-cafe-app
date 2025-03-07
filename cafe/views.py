from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import csrf_exempt
from .models import Table, Room, Item, TableReservation, RoomReservation, Order, OrderItem
from django.conf import settings
from datetime import datetime, timedelta
import os
from .models import Testimonial

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
    if request.method == 'POST':
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        duration = int(request.POST.get('duration'))
        table_number = request.POST.get('table_number')

        try:
            table = Table.objects.get(number=table_number)
            # Parse start time and calculate end time
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(minutes=duration)

            # Check for overlapping reservations
            existing_reservations = TableReservation.objects.filter(table=table, date=date)
            for reservation in existing_reservations:
                res_start = datetime.strptime(f"{reservation.date} {reservation.start_time}", "%Y-%m-%d %H:%M")
                res_end = res_start + timedelta(minutes=reservation.duration)
                if (start_datetime < res_end and end_datetime > res_start):
                    return render(request, 'cafe/reserve_table.html', {
                        'tables': Table.objects.all(),
                        'all_tables': Table.objects.all(),
                        'reservations': TableReservation.objects.all(),
                        'error': f'Table {table.number} is booked from {res_start.strftime("%H:%M")} to {res_end.strftime("%H:%M")} on {date}'
                    })

            # No conflict, create new reservation
            reservation = TableReservation(
                user=request.user,
                table=table,
                date=date,
                start_time=start_time,
                duration=duration
            )
            reservation.save()
            return render(request, 'cafe/reserve_table.html', {
                'tables': Table.objects.all(),
                'all_tables': Table.objects.all(),
                'reservations': TableReservation.objects.all(),
                'message': 'Table reserved successfully!'
            })
        except Table.DoesNotExist:
            return render(request, 'cafe/reserve_table.html', {
                'tables': Table.objects.all(),
                'all_tables': Table.objects.all(),
                'reservations': TableReservation.objects.all(),
                'error': 'Invalid table number'
            })
        except ValueError:
            return render(request, 'cafe/reserve_table.html', {
                'tables': Table.objects.all(),
                'all_tables': Table.objects.all(),
                'reservations': TableReservation.objects.all(),
                'error': 'Invalid date or time format'
            })

    tables = Table.objects.all()
    all_tables = Table.objects.all()
    reservations = TableReservation.objects.all()
    return render(request, 'cafe/reserve_table.html', {
        'tables': tables,
        'all_tables': all_tables,
        'reservations': reservations
    })

# Reserve PS Room View
@login_required
def reserve_ps_room(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        duration = int(request.POST.get('duration'))
        room_number = request.POST.get('room_number')

        try:
            room = Room.objects.get(number=room_number)
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(minutes=duration)

            existing_reservations = RoomReservation.objects.filter(room=room, date=date)
            for reservation in existing_reservations:
                res_start = datetime.strptime(f"{reservation.date} {reservation.start_time}", "%Y-%m-%d %H:%M")
                res_end = res_start + timedelta(minutes=reservation.duration)
                if (start_datetime < res_end and end_datetime > res_start):
                    return render(request, 'cafe/reserve_ps_room.html', {
                        'rooms': Room.objects.all(),
                        'all_rooms': Room.objects.all(),
                        'reservations': RoomReservation.objects.all(),
                        'error': f'Room {room.number} is booked from {res_start.strftime("%H:%M")} to {res_end.strftime("%H:%M")} on {date}'
                    })

            reservation = RoomReservation(
                user=request.user,
                room=room,
                date=date,
                start_time=start_time,
                duration=duration
            )
            reservation.save()
            return render(request, 'cafe/reserve_ps_room.html', {
                'rooms': Room.objects.all(),
                'all_rooms': Room.objects.all(),
                'reservations': RoomReservation.objects.all(),
                'message': 'PS Room reserved successfully!'
            })
        except Room.DoesNotExist:
            return render(request, 'cafe/reserve_ps_room.html', {
                'rooms': Room.objects.all(),
                'all_rooms': Room.objects.all(),
                'reservations': RoomReservation.objects.all(),
                'error': 'Invalid room number'
            })
        except ValueError:
            return render(request, 'cafe/reserve_ps_room.html', {
                'rooms': Room.objects.all(),
                'all_rooms': Room.objects.all(),
                'reservations': RoomReservation.objects.all(),
                'error': 'Invalid date or time format'
            })

    rooms = Room.objects.all()
    all_rooms = Room.objects.all()
    reservations = RoomReservation.objects.all()
    return render(request, 'cafe/reserve_ps_room.html', {
        'rooms': rooms,
        'all_rooms': all_rooms,
        'reservations': reservations
    })

# Place Order View
@login_required
def place_order(request):
    if request.method == 'POST':
        items = Item.objects.filter(is_available=True)
        selected_items = []
        for item in items:
            if request.POST.get(f'item_{item.id}'):
                selected_items.append((item, 1))

        if not selected_items:
            return render(request, 'cafe/place_order.html', {
                'items': items,
                'error': 'No items selected'
            })

        order = Order(user=request.user)
        order.save()
        for item, quantity in selected_items:
            if not item.is_available:
                return render(request, 'cafe/place_order.html', {
                    'items': items,
                    'error': f'{item.name} is out of stock'
                })
            OrderItem.objects.create(order=order, item=item, quantity=quantity)
        return render(request, 'cafe/place_order.html', {
            'items': items,
            'message': 'Order placed successfully!'
        })

    items = Item.objects.filter(is_available=True)
    return render(request, 'cafe/place_order.html', {'items': items})

# Staff Check
def is_staff(user):
    return user.is_staff

# Admin Page View
@login_required
@user_passes_test(is_staff)
def admin_page(request):
    tables = Table.objects.all()
    rooms = Room.objects.all()
    items = Item.objects.all()
    table_reservations = TableReservation.objects.all()
    room_reservations = RoomReservation.objects.all()
    orders = Order.objects.all()
    return render(request, 'cafe/admin_page.html', {
        'tables': tables,
        'rooms': rooms,
        'items': items,
        'table_reservations': table_reservations,
        'room_reservations': room_reservations,
        'orders': orders
    })

# Admin Table Management
@csrf_exempt
@login_required
@user_passes_test(is_staff)
def add_table(request):
    if request.method == 'POST':
        number = request.POST.get('number')
        if Table.objects.filter(number=number).exists():
            return render(request, 'cafe/admin_page.html', {
                'tables': Table.objects.all(),
                'rooms': Room.objects.all(),
                'items': Item.objects.all(),
                'table_reservations': TableReservation.objects.all(),
                'room_reservations': RoomReservation.objects.all(),
                'orders': Order.objects.all(),
                'error': 'Table number already exists'
            })
        Table.objects.create(number=number)
        return redirect('cafe:admin_page')
    return redirect('cafe:admin_page')

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
        return redirect('cafe:admin_page')
    return redirect('cafe:admin_page')

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

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def add_item(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        print(f"Name: {name}, Price: {price}, Image: {image}, Image Type: {type(image)}")
        if Item.objects.filter(name=name).exists():
            return render(request, 'cafe/admin_page.html', {
                # Context
                'error': 'Item name already exists'
            })
        try:
            price = float(price)
            item = Item(name=name, price=price)
            if image:
                item.image = image
            item.save()
            print(f"Saved item image path: {item.image.url}")  # Confirm saved URL
            return redirect('cafe:admin_page')
        except ValueError:
            return render(request, 'cafe/admin_page.html', {
                # Context
                'error': 'Invalid price'
            })
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