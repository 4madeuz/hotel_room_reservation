# tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from rooms.models import Reservation

logger = get_task_logger(__name__)


@shared_task
def update_reservation_status():
    today = timezone.now().date()
    unwanted_statuses = [Reservation.Status.Refused, Reservation.Status.Expired]
    reservations_to_update = Reservation.objects.exclude(
        status__in=unwanted_statuses
    )
    if reservations_to_update:
        for reservation in reservations_to_update:
            if reservation.status == Reservation.Status.Booked:
                if reservation.starting_date.date() == today:
                    reservation.status = Reservation.Status.Active
                    reservation.save()
            if reservation.status == Reservation.Status.Active:
                if reservation.ending_date.date() < today:
                    reservation.status = Reservation.Status.Expired
                    reservation.save()
    return 'статусы обновлены'
