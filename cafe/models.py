from django.db import models
from django.contrib.auth.models import User

# Define ITEM_TYPES at the module level
ITEM_TYPES = [
    ('dessert', 'Dessert'),
    ('yogurt', 'Yogurt'),
    ('fruit_salad', 'Fruit Salad'),
    ('iced_coffee', 'Iced Coffee'),
    ('hot_drinks', 'Hot Drinks'),
    ('herbs', 'Herbs'),
    ('soda_cocktail', 'Soda Cocktail'),
    ('milkshake', 'Milkshake'),
    ('coffee', 'Coffee'),
    ('espresso', 'Espresso'),
    ('fruit_cocktail', 'Fruit Cocktail'),
    ('smoothie', 'Smoothie'),
    ('waffle', 'Waffle'),
    ('juices', 'Juices'),
    ('tea', 'Tea'),
    ('iced_tea', 'Iced Tea'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True)  # e.g., "+1234567890"

    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"

class Table(models.Model):
    number = models.IntegerField(unique=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.number}"

class Room(models.Model):
    number = models.IntegerField(unique=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.number}"

class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='items/', null=True, blank=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='dessert')

    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()})"

class TableReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    duration = models.IntegerField(choices=[(30, '30 min'), (60, '1 hour'), (120, '2 hours')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Table {self.table.number} - {self.date}"

class RoomReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    duration = models.IntegerField(choices=[(30, '30 min'), (60, '1 hour'), (120, '2 hours')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Room {self.room.number} - {self.date}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=50)  # e.g., "table_1" or "room_1"
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"Order by {self.user.username} - {self.location} - {self.created_at}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Testimonial(models.Model):
    author = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} - {self.content[:50]}"