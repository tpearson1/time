# This is an example of a configuration file for the time management program.
# Feel free to change the logic to suit your schedule

from config_utils import *


# Example implementation which sets expected work time based on the weekday.
# Please note that on the same day, this function should *always* return the
# same length of time. Otherwise, when the program is opened multiple times in
# a day, it is not possible to record the amount of time that still needs to be
# worked.
def expected_work_time_today():
    # The function make_duration takes in a number of hours, and then optional
    # minutes and seconds arguments. The function returns a timedelta.
    today = datetime.today().weekday()
    if today == SATURDAY:
        return make_duration(10, 30)
    if today == SUNDAY:
        return make_duration(0)
    return make_duration(2, 30)


# This function picks the most recent event in the below list
def pick_event():
    events = [
        # An event takes a date and a description string. The format for
        # specifying a date is YEAR-MONTH-DAY.
        Event(date(2019, 1, 1), "New Years Day"),
        Event(date(2018, 12, 25), "Christmas Day")
    ]

    events.sort(key=lambda e: e.occur_date)

    if len(events) == 0 or events[0].happened():
        # No relevant events
        return None

    return events[0]
