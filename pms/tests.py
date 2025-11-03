from datetime import date

from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import Room, Room_type, Booking, Customer


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class DashboardViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room_type_single = Room_type.objects.create(
            name='Individual', price=50.0, max_guests=1
        )
        cls.room_type_double = Room_type.objects.create(
            name='Doble', price=80.0, max_guests=2
        )

        cls.room_1 = Room.objects.create(
            name='Room 1.1', room_type=cls.room_type_single, description='Single room'
        )
        cls.room_2 = Room.objects.create(
            name='Room 1.2', room_type=cls.room_type_single, description='Single room'
        )
        cls.room_3 = Room.objects.create(
            name='Room 2.1', room_type=cls.room_type_double, description='Double room'
        )
        cls.room_4 = Room.objects.create(
            name='Room 2.2', room_type=cls.room_type_double, description='Double room'
        )
        cls.room_5 = Room.objects.create(
            name='Room 2.3', room_type=cls.room_type_double, description='Double room'
        )

        cls.customer = Customer.objects.create(
            name='Test Customer', email='test@example.com', phone='123456789'
        )

        today = date.today()

        cls.booking_1 = Booking.objects.create(
            state='NEW',
            checkin=today,
            checkout=today,
            room=cls.room_1,
            guests=1,
            customer=cls.customer,
            total=50.0,
            code='BOOK0001',
        )
        cls.booking_2 = Booking.objects.create(
            state='NEW',
            checkin=today,
            checkout=today,
            room=cls.room_2,
            guests=1,
            customer=cls.customer,
            total=50.0,
            code='BOOK0002',
        )
        cls.booking_3 = Booking.objects.create(
            state='NEW',
            checkin=today,
            checkout=today,
            room=cls.room_3,
            guests=2,
            customer=cls.customer,
            total=80.0,
            code='BOOK0003',
        )
        cls.booking_cancelled = Booking.objects.create(
            state='DEL',
            checkin=today,
            checkout=today,
            room=cls.room_4,
            guests=2,
            customer=cls.customer,
            total=80.0,
            code='BOOK0004',
        )

    def setUp(self):
        self.client = Client()
        self.url = reverse('dashboard')

    def test_view_loads_successfully_and_contains_all_widgets(self):
        # Arrange
        expected_status_code = 200

        # Act
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']

        # Assert
        self.assertEqual(response.status_code, expected_status_code)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertIn('dashboard', response.context)

        self.assertIn('new_bookings', dashboard)
        self.assertIn('incoming_guests', dashboard)
        self.assertIn('outcoming_guests', dashboard)
        self.assertIn('invoiced', dashboard)
        self.assertIn('occupancy_percentage', dashboard)

    def test_get_occupancy_percentage_returns_value_excluding_cancelled_bookings(self):
        # Arrange
        confirmed_count = Booking.objects.filter(state='NEW').count()
        total_rooms = Room.objects.count() or 1  # Avoid division by zero
        expected_percentage = (confirmed_count / total_rooms) * 100

        # Act
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']

        # Assert
        self.assertEqual(dashboard['occupancy_percentage'], expected_percentage)

    def test_get_occupancy_percentage_returns_zero_when_no_rooms(self):
        # Arrange
        Room.objects.all().delete()
        expected_percentage = 0

        # Act
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']

        # Assert
        self.assertEqual(dashboard['occupancy_percentage'], expected_percentage)

    def test_get_occupancy_percentage_returns_zero_when_no_bookings(self):
        # Arrange
        Booking.objects.all().delete()
        expected_percentage = 0

        # Act
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']

        # Assert
        self.assertEqual(dashboard['occupancy_percentage'], expected_percentage)

    def test_occupancy_with_100_percent(self):
        # Arrange
        today = date.today()
        Booking.objects.create(
            state='NEW',
            checkin=today,
            checkout=today,
            room=self.room_4,
            guests=2,
            customer=self.customer,
            total=80.0,
            code='BOOK0005',
        )
        Booking.objects.create(
            state='NEW',
            checkin=today,
            checkout=today,
            room=self.room_5,
            guests=2,
            customer=self.customer,
            total=80.0,
            code='BOOK0006',
        )
        expected_percentage = 100.0

        # Act
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']

        # Assert
        self.assertEqual(dashboard['occupancy_percentage'], expected_percentage)
