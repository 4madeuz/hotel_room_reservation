import uuid
from typing import AnyStr

from dateutil import rrule
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ReservationlManager(models.Manager):
    def booked_and_active(self):
        return self.filter(
            status__in=[Reservation.Status.Booked, Reservation.Status.Active]
        )

    def reserved_dates(self, room_id: AnyStr):
        return self.booked_and_active().filter(room=room_id)

    def reserves_dates_exclude_update_reservation(self, room_id, reserv_id):
        return (
            self.booked_and_active().filter(room=room_id).exclude(id=reserv_id)
        )


User = get_user_model()


class TimeStampedMixin(models.Model):
    created_at = models.DateTimeField(_('created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated'), auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Room(UUIDMixin, TimeStampedMixin):
    class BedType(models.TextChoices):
        Twin = _('twin')
        Double = _('double')
        TwinBunk = _('twin_bunk')
        DoubleTwinBunk = _('double_twin_bunk')

    name = models.TextField(_('name'), blank=False)
    number = models.CharField(_('number'), blank=False, max_length=20)
    day_cost = models.FloatField(_('day_cost'),)
    travellers = models.FloatField(_('travellers'), blank=True, null=True)
    rating = models.FloatField(
        _('rating'),
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=0,
    )
    refundable = models.BooleanField(_('refundable'), default=True)
    # предположим, что в комнате может быть кровать только одного типа
    # для комнат в хостеле это правда, но если нужно расширить этот класс до Property
    # то возможно стоит выделить sleeping_area как отдельтую сущность
    sleeping_area = models.TextField(
        _('sleeping_area'), choices=BedType.choices, default=BedType.Twin
    )
    active = models.BooleanField(_('active'), default=True)

    def __str__(self) -> str:
        return self.name

    def reserved_dates(self, reserv_id: AnyStr = None):
        if reserv_id:
            date_ranges = Reservation.objects.reserves_dates_exclude_update_reservation(
                self.id, reserv_id
            )
        else:
            date_ranges = Reservation.objects.reserved_dates(self.id)
        reserved_dates = []

        for date_range in date_ranges:
            start_date = date_range.starting_date.date()
            end_date = date_range.ending_date.date()

            rule = rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date)

            reserved_dates.extend(list(rule))

        return reserved_dates

    class Meta:
        db_table = 'content"."rooms'
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'number'], name='name_number_constraint'
            )
        ]


class Reservation(UUIDMixin, TimeStampedMixin):

    objects = ReservationlManager()

    class Status(models.TextChoices):
        Booked = _('booked')
        Refused = _('refused')
        Active = _('active')
        Expired = _('expired')

    def validate_date_within_two_weeks(value):
        two_weeks_from_now = timezone.now() + timezone.timedelta(weeks=2)
        if value.date() > two_weeks_from_now.date():
            raise ValidationError(
                'Дата не может быть больше чем две недели от текущей даты.'
            )

    def validate_future_date(value):
        if value.date() < timezone.now().date():
            raise ValidationError('Дата должна быть больше текущей.')

    starting_date = models.DateTimeField(
        _('starting_date'),
        validators=[validate_date_within_two_weeks, validate_future_date],
    )
    ending_date = models.DateTimeField(
        _('ending_date'),
        validators=[validate_date_within_two_weeks, validate_future_date],
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='reservations'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reservations'
    )
    status = models.TextField(
        _('status'), choices=Status.choices, default=Status.Booked
    )

    def __str__(self) -> str:
        return f'{self.room.name} ({self.starting_date} - {self.ending_date}) by {self.user.username}'

    class Meta:
        db_table = 'content"."reservations'
        verbose_name = _('Reservation')
        verbose_name_plural = _('Reservations')
