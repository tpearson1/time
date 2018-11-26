# Code which helps facilitate the creation of a configuration file

from datetime import datetime, date, timedelta

MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6


def make_duration(hours, minutes=0, seconds=0):
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


class Event:
    def __init__(self, occur_date, description):
        self.occur_date = occur_date
        self.description = description

    def time_till_event(self):
        return self.occur_date - date.today()

    def days_till_event(self):
        return self.time_till_event().days

    def happened(self):
        return self.time_till_event().total_seconds() < 0
