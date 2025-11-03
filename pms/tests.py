from datetime import date, timedelta

from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import Room, Room_type, Booking, Customer


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class EditBookingDatesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room_type = Room_type.objects.create(name='Doble', price=80.0, max_guests=2)

        cls.room_1 = Room.objects.create(
            name='Room 1.1', room_type=cls.room_type, description='Double room'
        )
        cls.room_2 = Room.objects.create(
            name='Room 2.1', room_type=cls.room_type, description='Double room'
        )

        cls.customer = Customer.objects.create(
            name='Test Customer', email='test@example.com', phone='123456789'
        )

        today = date.today()
        cls.booking_to_edit = Booking.objects.create(
            state='NEW',
            checkin=today,
            checkout=today + timedelta(days=2),
            room=cls.room_1,
            guests=2,
            customer=cls.customer,
            total=160.0,
            code='EDIT0001',
        )

        cls.conflicting_booking = Booking.objects.create(
            state='NEW',
            checkin=today + timedelta(days=5),
            checkout=today + timedelta(days=7),
            room=cls.room_1,
            guests=2,
            customer=cls.customer,
            total=160.0,
            code='CONF0001',
        )

    def setUp(self):
        self.client = Client()
        self.url = reverse('edit_booking_dates', kwargs={'pk': self.booking_to_edit.id})

    def test_view_loads_successfully_and_contains_form(self):
        # Arrange
        expected_status_code = 200

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, expected_status_code)
        self.assertTemplateUsed(response, 'edit_booking_dates.html')
        self.assertIn('booking', response.context)
        self.assertIn('form', response.context)

    def test_post_updates_dates_when_room_is_available(self):
        # Arrange
        today = date.today()
        new_checkin = today + timedelta(days=10)
        new_checkout = today + timedelta(days=12)
        post_data = {
            'checkin': new_checkin.strftime('%Y-%m-%d'),
            'checkout': new_checkout.strftime('%Y-%m-%d'),
        }
        expected_status_code = 302

        # Act
        response = self.client.post(self.url, post_data)

        # Assert
        self.assertEqual(response.status_code, expected_status_code)
        self.assertEqual(response.url, '/')

        self.booking_to_edit.refresh_from_db()
        self.assertEqual(self.booking_to_edit.checkin, new_checkin)
        self.assertEqual(self.booking_to_edit.checkout, new_checkout)

    def test_post_shows_error_when_dates_conflict_with_another_booking(self):
        # Arrange
        today = date.today()
        new_checkin = today + timedelta(days=5)
        new_checkout = today + timedelta(days=6)
        post_data = {
            'checkin': new_checkin.strftime('%Y-%m-%d'),
            'checkout': new_checkout.strftime('%Y-%m-%d'),
        }
        expected_error = 'No hay disponibilidad para las fechas seleccionadas'

        # Act
        response = self.client.post(self.url, post_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_booking_dates.html')
        self.assertIn('error', response.context)
        self.assertEqual(response.context['error'], expected_error)

        self.booking_to_edit.refresh_from_db()
        self.assertEqual(self.booking_to_edit.checkin, date.today())

    def test_post_allows_keeping_same_dates_without_conflict(self):
        # Arrange
        today = date.today()
        post_data = {
            'checkin': today.strftime('%Y-%m-%d'),
            'checkout': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
        }
        expected_status_code = 302

        # Act
        response = self.client.post(self.url, post_data)

        # Assert
        self.assertEqual(response.status_code, expected_status_code)
        self.assertEqual(response.url, '/')

    def test_post_ignores_cancelled_bookings_when_checking_availability(self):
        # Arrange
        today = date.today()
        new_checkin = today + timedelta(days=15)
        new_checkout = today + timedelta(days=17)

        Booking.objects.create(
            state='DEL',
            checkin=new_checkin,
            checkout=new_checkout,
            room=self.room_1,
            guests=2,
            customer=self.customer,
            total=160.0,
            code='CANC0001',
        )

        post_data = {
            'checkin': new_checkin.strftime('%Y-%m-%d'),
            'checkout': new_checkout.strftime('%Y-%m-%d'),
        }
        expected_status_code = 302

        # Act
        response = self.client.post(self.url, post_data)

        # Assert
        self.assertEqual(response.status_code, expected_status_code)
        self.assertEqual(response.url, '/')

    def test_post_allows_same_dates_in_different_room(self):
        # Arrange
        today = date.today()
        new_checkin = today + timedelta(days=20)
        new_checkout = today + timedelta(days=22)

        Booking.objects.create(
            state='NEW',
            checkin=new_checkin,
            checkout=new_checkout,
            room=self.room_2,
            guests=2,
            customer=self.customer,
            total=160.0,
            code='ROOM2001',
        )

        post_data = {
            'checkin': new_checkin.strftime('%Y-%m-%d'),
            'checkout': new_checkout.strftime('%Y-%m-%d'),
        }

        # Act
        response = self.client.post(self.url, post_data)

        # Assert
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
