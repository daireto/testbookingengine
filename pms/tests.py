from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import Room, Room_type


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class RoomsViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room_type_single = Room_type.objects.create(
            name='Individual',
            price=50.0,
            max_guests=1,
        )
        cls.room_type_double = Room_type.objects.create(
            name='Doble',
            price=80.0,
            max_guests=2,
        )

        cls.room_1_1 = Room.objects.create(
            name='Room 1.1',
            room_type=cls.room_type_single,
            description='Lorem ipsum',
        )
        cls.room_1_2 = Room.objects.create(
            name='Room 1.2',
            room_type=cls.room_type_single,
            description='Lorem ipsum',
        )
        cls.room_1_10 = Room.objects.create(
            name='Room 1.10',
            room_type=cls.room_type_double,
            description='Lorem ipsum',
        )
        cls.room_2_1 = Room.objects.create(
            name='Room 2.1',
            room_type=cls.room_type_double,
            description='Lorem ipsum',
        )
        cls.room_2_2 = Room.objects.create(
            name='Room 2.2',
            room_type=cls.room_type_double,
            description='Lorem ipsum',
        )
        cls.rooms = [
            cls.room_1_1,
            cls.room_1_2,
            cls.room_1_10,
            cls.room_2_1,
            cls.room_2_2,
        ]

    def setUp(self):
        self.client = Client()
        self.url = reverse('rooms')

    def test_get_returns_all_rooms_when_no_filter_is_applied(self):
        # Arrange
        expected_status = 200

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, expected_status)
        self.assertTemplateUsed(response, 'rooms.html')

        rooms = response.context['rooms']
        self.assertEqual(len(rooms), len(self.rooms))

        self.assertEqual(response.context['filter'], '')

        fetched_room_names = [room['name'] for room in rooms]
        actual_room_names = [room.name for room in self.rooms]
        self.assertCountEqual(fetched_room_names, actual_room_names)

    def test_get_returns_filtered_rooms_when_filter_is_applied(self):
        # Arrange
        filter_value = 'Room 1'
        expected_status = 200
        expected_rooms = len([room for room in self.rooms if filter_value in room.name])

        # Act
        response = self.client.get(self.url, {'filter': filter_value})

        # Assert
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response.context['filter'], filter_value)

        rooms = response.context['rooms']
        self.assertEqual(len(rooms), expected_rooms)

        room_names = [room['name'] for room in rooms]
        for room in self.rooms:
            if filter_value in room.name:
                self.assertIn(room.name, room_names)
            else:
                self.assertNotIn(room.name, room_names)

    def test_get_returns_case_insensitive_results_when_filtering(self):
        # Arrange
        expected_status = 200
        expected_rooms = len([room for room in self.rooms if 'Room 1' in room.name])

        # Act
        response_lower = self.client.get(self.url, {'filter': 'room 1'})
        response_upper = self.client.get(self.url, {'filter': 'ROOM 1'})
        response_mixed = self.client.get(self.url, {'filter': 'RoOm 1'})

        # Assert
        self.assertEqual(response_lower.status_code, expected_status)
        self.assertEqual(response_upper.status_code, expected_status)
        self.assertEqual(response_mixed.status_code, expected_status)

        rooms_lower = response_lower.context['rooms']
        rooms_upper = response_upper.context['rooms']
        rooms_mixed = response_mixed.context['rooms']

        self.assertEqual(len(rooms_lower), expected_rooms)
        self.assertEqual(len(rooms_upper), expected_rooms)
        self.assertEqual(len(rooms_mixed), expected_rooms)

        names_lower = set(room['name'] for room in rooms_lower)
        names_upper = set(room['name'] for room in rooms_upper)
        names_mixed = set(room['name'] for room in rooms_mixed)

        self.assertEqual(names_lower, names_upper)
        self.assertEqual(names_lower, names_mixed)

    def test_get_returns_no_results_when_filter_has_no_matches(self):
        # Arrange
        filter_value = 'Room 3.1'
        expected_status = 200
        expected_rooms = 0

        # Act
        response = self.client.get(self.url, {'filter': filter_value})

        # Assert
        self.assertEqual(response.status_code, expected_status)

        rooms = response.context['rooms']
        self.assertEqual(len(rooms), expected_rooms)

        self.assertEqual(response.context['filter'], filter_value)

    def test_get_returns_all_rooms_when_filter_is_empty(self):
        # Arrange
        expected_status = 200

        # Act
        response = self.client.get(self.url, {'filter': ''})

        # Assert
        self.assertEqual(response.status_code, expected_status)

        rooms = response.context['rooms']
        self.assertEqual(len(rooms), len(self.rooms))
