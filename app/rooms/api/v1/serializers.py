from dateutil import rrule
from rest_framework import serializers

from rooms.models import Reservation, Room


class ReservationDateslSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ('starting_date', 'ending_date')


class RoomSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['reserved_dates'] = instance.reserved_dates()
        return representation

    class Meta:
        model = Room
        fields = '__all__'
        # fields = ['id', 'name', 'number', 'day_cost', 'travellers', 'rating', 'refundable', 'sleeping_area']


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ['user', 'status']
