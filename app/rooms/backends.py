from datetime import datetime, timedelta

from dateutil import parser, rrule
from django.db.models import Q
from drf_yasg.openapi import IN_QUERY, TYPE_STRING, Parameter
from rest_framework import filters
from rest_framework.exceptions import ValidationError


class DateRangeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)
        try:
            if not start_date_str:
                start_date = datetime.now().date()
            else:
                start_date = parser.parse(start_date_str).date()

            if not end_date_str:
                end_date = datetime.now().date() + timedelta(weeks=2)
            else:
                end_date = parser.parse(end_date_str).date()

        except ValueError:
            return queryset

        if start_date > end_date:
            raise ValidationError(detail='Invalid time period')

        rule = rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date)
        set_dates = set(list(rule))

        queryset = [
            entity
            for entity in queryset
            if not all(elem in entity.reserved_dates() for elem in set_dates)
        ]

        return queryset


class DayCostFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        day_cost = request.query_params.get('day_cost', None)

        if not day_cost:
            return queryset

        return queryset.filter(day_cost__lte=day_cost)


class TravellersFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        travellers = request.query_params.get('travellers', None)

        if not travellers:
            return queryset

        return queryset.filter(travellers__gte=travellers)
