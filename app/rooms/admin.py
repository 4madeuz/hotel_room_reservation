from django.contrib import admin

from .models import Reservation, Room


class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number',
        'day_cost',
        'travellers',
        'rating',
        'refundable',
        'sleeping_area',
        'active',
    )
    search_fields = ('name', 'number')
    list_filter = ('refundable', 'sleeping_area', 'active')
    readonly_fields = ('rating', 'travellers')


class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'starting_date',
        'ending_date',
        'room',
        'user',
        'status',
    )
    search_fields = ('room__name', 'user__username')
    list_filter = ('status',)


admin.site.register(Room, RoomAdmin)
admin.site.register(Reservation, ReservationAdmin)
