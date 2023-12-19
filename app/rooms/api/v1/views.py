from dateutil import parser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rooms.api.v1.serializers import ReservationSerializer, RoomSerializer
from rooms.backends import (
    DateRangeFilterBackend,
    DayCostFilter,
    TravellersFilter,
)
from rooms.models import Reservation, Room
from rooms.permissions import IsOwnerOrAdminPermission


class RoomViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    pagination_class = PageNumberPagination
    permission_classes = [
        AllowAny,
    ]
    filterset_fields = ['day_cost', 'travellers']
    ordering_fields = ['day_cost', 'travellers']

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'start_date',
                openapi.IN_QUERY,
                description='Start date for filtering rooms',
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'end_date',
                openapi.IN_QUERY,
                description='End date for filtering rooms',
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        self.filter_backends = [
            OrderingFilter,
            DayCostFilter,
            TravellersFilter,
            DateRangeFilterBackend,
        ]
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    def check_conflicting_dates(
        self, room, starting_date, ending_date, reservation_id=None
    ):
        reserved_dates = room.reserved_dates(reserv_id=reservation_id)
        reserved_dates = [date.date() for date in reserved_dates]
        conflicting_dates = [
            date
            for date in reserved_dates
            if starting_date <= date <= ending_date
        ]
        return conflicting_dates

    def create(self, request, *args, **kwargs):
        room_id = request.data.get('room')
        starting_date_str = request.data.get('starting_date', None)
        ending_date_str = request.data.get('ending_date', None)

        if not (starting_date_str and ending_date_str):
            return Response(
                {'Invalid time period'}, status=status.HTTP_400_BAD_REQUEST
            )

        starting_date = parser.parse(starting_date_str).date()
        ending_date = parser.parse(ending_date_str).date()

        room = get_object_or_404(Room, pk=room_id)

        if not room.active:
            return Response(
                {'Room is unavaliable at the moment'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conflicting_dates = self.check_conflicting_dates(
            room, starting_date, ending_date
        )

        if conflicting_dates:
            return Response(
                {
                    'error': f'Conflicting dates: {", ".join(map(str, conflicting_dates))}'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ReservationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):

        room_id = request.data.get('room')
        starting_date_str = request.data.get('starting_date', None)
        ending_date_str = request.data.get('ending_date', None)

        instance = self.get_object()

        if not starting_date_str:
            starting_date = instance.starting_date.date()
        else:
            starting_date = parser.parse(starting_date_str).date()
        if not ending_date_str:
            ending_date = instance.ending_date.date()
        else:
            ending_date = parser.parse(ending_date_str).date()

        room = get_object_or_404(Room, pk=room_id)

        if not room.active:
            return Response(
                {'Room is unavaliable at the moment'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conflicting_dates = self.check_conflicting_dates(
            room, starting_date, ending_date, instance.id
        )

        if conflicting_dates:
            return Response(
                {
                    'error': f'Conflicting dates: {", ".join(map(str, conflicting_dates))}'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(instance, serializer.validated_data)
        return Response(
            {
                'message': 'Reservation updated successfully',
                'data': serializer.data,
            }
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        room = get_object_or_404(Room, name=instance.room)
        if not room.refundable:
            return Response(
                {'This room is unrefundable'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = instance.Status.Refused
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(instance, serializer.validated_data)
        return Response(
            {'message': 'Status changed successfully', 'data': serializer.data}
        )

    def get_permissions(self):
        if self.action == 'create' or 'get':
            return [IsAuthenticated()]
        else:
            return [IsOwnerOrAdminPermission()]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user.id)
