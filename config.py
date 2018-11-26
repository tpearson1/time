# This is an example of a configuration file for the time management program.
# Feel free to change the logic to suit your schedule

from config_utils import *

EVENT_DISPLAY_COUNT = 5


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
def add_yearly_event(events, month, day, desc):
    today = datetime.today()
    # Two events added because if the event already happened this year, the
    # next time is next year
    events.append(Event(date(today.year, month, day), desc))
    events.append(Event(date(today.year + 1, month, day), desc))

def this_year_event(month, day, desc):
    today = datetime.today()
    return Event(date(today.year, month, day), desc)

def add_event_this_year(events, month, day, desc):
    events.append(this_year_event(month, day, desc))


# This function picks the most recent events in the below list
def pick_event():
    events = []
    add_yearly_event(events, 1, 1, "New Years Day")
    add_yearly_event(events, 12, 25, "Christmas Day")

    events.sort(key=lambda e: e.occur_date)

    # Find the closest two events that hasn't happened yet
    firstRelevant = 0
    while firstRelevant < len(events):
        if not events[firstRelevant].happened():
            break
        firstRelevant += 1
    return events[firstRelevant:(firstRelevant + EVENT_DISPLAY_COUNT)]

