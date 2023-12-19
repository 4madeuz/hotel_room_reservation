from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Room


@receiver(pre_save, sender=Room)
def calculate_travellers(sender, instance, **kwargs):

    if instance.sleeping_area == Room.BedType.Twin:
        instance.travellers = 1
    elif instance.sleeping_area == Room.BedType.Double:
        instance.travellers = 2
    elif instance.sleeping_area == Room.BedType.TwinBunk:
        instance.travellers = 2
    elif instance.sleeping_area == Room.BedType.DoubleTwinBunk:
        instance.travellers = 4
