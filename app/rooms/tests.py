from datetime import datetime, timedelta

import factory
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Reservation, Room

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    password = factory.Faker('password')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create a user with JWT token."""
        user = super()._create(model_class, *args, **kwargs)
        refresh = RefreshToken.for_user(user)
        user.auth_token = str(refresh.access_token)
        return user


class RoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Room

    name = factory.Faker('word')
    number = factory.Sequence(lambda n: f'Room-{n}')
    day_cost = factory.Faker('pyfloat', left_digits=3, right_digits=2)
    travellers = factory.Faker('pyfloat', left_digits=1, right_digits=1)
    rating = factory.Faker('pyfloat', left_digits=1, right_digits=1)
    refundable = True
    sleeping_area = factory.Faker(
        'random_element',
        elements=[choice[0] for choice in Room.BedType.choices],
    )
    active = True


class ReservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reservation

    starting_date = factory.Faker(
        'date_time_this_month', before_now=False, after_now=True
    )
    ending_date = factory.Faker(
        'date_time_this_month', before_now=False, after_now=True
    )
    room = factory.SubFactory(RoomFactory)
    user = factory.SubFactory(UserFactory)
    status = Reservation.Status.Booked


class RoomTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse('room-list')
        self.detail_url = reverse('room-detail', args=[1])

    def test_get_room_list(self):
        """Получение списка комнат"""

        RoomFactory.create_batch(3)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_room_detail(self):
        """Получение конкретной комнаты"""
        room = RoomFactory()

        detail_url = reverse('room-detail', args=[room.id])

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], room.name)
        self.assertEqual(response.data['number'], room.number)


class ReservationViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.room = RoomFactory()
        self.list_url = reverse('reservation-list')

    def get_authenticated_client(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}'
        )

    def test_create_reservation(self):
        """Создание брони"""

        reservation_data = {
            'starting_date': str(datetime.now()),
            'ending_date': str(datetime.now()),
            'room': self.room.id,
        }

        self.get_authenticated_client()
        response = self.client.post(
            self.list_url, reservation_data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_get_reservation_list(self):
        """Получение списка броней"""

        ReservationFactory.create_batch(3, user=self.user)

        self.get_authenticated_client()
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_reservation_detail(self):
        """Получение бронни по id"""

        reservation = ReservationFactory.create(user=self.user, room=self.room)

        detail_url = reverse('reservation-detail', args=[reservation.id])

        self.get_authenticated_client()
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['room'], reservation.room.id)

    def test_same_date_reservation(self):
        """Бронирование уже занятой в этот момент комнаты"""

        reservation_data = {
            'starting_date': str(datetime.now()),
            'ending_date': str(datetime.now()),
            'room': self.room.id,
        }

        self.get_authenticated_client()

        response = self.client.post(
            self.list_url, reservation_data, format='json'
        )
        response = self.client.post(
            self.list_url, reservation_data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_wrong_date_reservation_two_weeks(self):
        """Создание брони с датой больше чем две недели от текущей"""

        reservation_data = {
            'starting_date': str(datetime.now() + timedelta(30)),
            'ending_date': str(datetime.now() + timedelta(30)),
            'room': self.room.id,
        }

        self.get_authenticated_client()
        response = self.client.post(
            self.list_url, reservation_data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_wrong_date_reservation_less_then_current(self):
        """Создание брони с датой меньше текущей"""

        reservation_data = {
            'starting_date': str(datetime.now() - timedelta(30)),
            'ending_date': str(datetime.now() - timedelta(30)),
            'room': self.room.id,
        }

        self.get_authenticated_client()
        response = self.client.post(
            self.list_url, reservation_data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_get_anothers_reservation_detail(self):
        """Получение чужой брони по id"""

        reservation = ReservationFactory.create(user=self.user, room=self.room)

        detail_url = reverse('reservation-detail', args=[reservation.id])

        self.get_authenticated_client()
        response = self.client.get(detail_url)

        another_user = UserFactory()
        refresh = RefreshToken.for_user(another_user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}'
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_anauth_reservation_create(self):
        """Создание брони неаутентифицированным пользователем"""

        reservation_data = {
            'starting_date': str(datetime.now()),
            'ending_date': str(datetime.now()),
            'room': self.room.id,
        }

        response = self.client.post(
            self.list_url, reservation_data, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_reservation_delete(self):
        """Удаление брони, в данном случае смена статута"""

        reservation = ReservationFactory.create(user=self.user, room=self.room)

        detail_url = reverse('reservation-detail', args=[reservation.id])

        self.get_authenticated_client()
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['data']['status'], reservation.Status.Refused
        )


class TestFilers(TestCase):
    def setUp(self):

        self.client = APIClient()
        self.user = UserFactory()
        self.room = RoomFactory(day_cost=500, sleeping_area=Room.BedType.Twin)
        self.list_reservation_url = reverse('reservation-list')
        self.list_room_url = reverse('room-list')

    def get_authenticated_client(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}'
        )

    def test_invalid_date_filter(self):
        """Тест фильтрации, у комнаты нет свобоных дат в заданный промежуток"""
        # бронируем удинственную комнату на 4 дня
        reservation_data = {
            'starting_date': str(datetime.now()),
            'ending_date': str(datetime.now() + timedelta(3)),
            'room': self.room.id,
        }

        self.get_authenticated_client()
        self.client.post(
            self.list_reservation_url, reservation_data, format='json'
        )
        # фильтруем комнаты в забронированные даты
        response = self.client.get(
            self.list_room_url,
            data={
                'start_date': str(datetime.now().date()),
                'end_date': str(datetime.now().date()),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_valid_date_filter(self):
        """Тест фильтрации дат, у комнаты есть свободные даты в заданный промежуток"""
        # бронируем удинственную комнату на 4 дня
        reservation_data = {
            'starting_date': str(datetime.now()),
            'ending_date': str(datetime.now() + timedelta(3)),
            'room': self.room.id,
        }

        self.get_authenticated_client()
        self.client.post(
            self.list_reservation_url, reservation_data, format='json'
        )
        # фильтруем комнаты в промежуток до 5 дней
        response = self.client.get(
            self.list_room_url,
            data={
                'start_date': str(datetime.now().date()),
                'end_date': str(datetime.now().date() + timedelta(4)),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_day_cost_filter(self):
        """Тест фильтрации стоимости за день, убирает комнаты стоимостью выше введённой"""

        room = RoomFactory(day_cost=200)

        response = self.client.get(self.list_room_url, data={'day_cost': 400})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Room.objects.count(), 2)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(room.id))

    def test_travellers_filter(self):
        """Тест фильтрации количества людей, убирает комнаты количеством людей меньше введённого"""

        room = RoomFactory(sleeping_area=Room.BedType.DoubleTwinBunk)
        # для DoubleTwinBunk количество мест - 4
        response = self.client.get(self.list_room_url, data={'travellers': 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Room.objects.count(), 2)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(room.id))
