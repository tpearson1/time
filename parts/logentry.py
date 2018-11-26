from datetime import datetime, date, timedelta

from . import duration


class LogEntry:
    def for_today(expected_time_working, time_worked, overdue, accomplished,
                  for_tomorrow):
        return LogEntry(date.today(), expected_time_working, time_worked,
                        overdue, accomplished, for_tomorrow)

    def from_str(text):
        results = text.split("\t")
        return LogEntry(
            datetime.strptime(results[0], "%Y-%m-%d").date(),
            duration.duration_from_str(results[1]),
            duration.duration_from_str(results[2]),
            duration.duration_from_str(results[3]), results[4], results[5])

    def __init__(self, entry_date, expected_time_working, time_worked, overdue,
                 accomplished, for_tomorrow):
        self.entry_date = entry_date
        self.expected_time_working = expected_time_working
        self.time_worked = time_worked
        self.overdue = overdue
        self.accomplished = accomplished
        self.for_tomorrow = for_tomorrow

    def __str__(self):
        return "{}\t{}\t{}\t{}\t{}\t{}".format(
            self.entry_date,
            duration.duration_to_str(self.expected_time_working),
            duration.duration_to_str(self.time_worked),
            duration.duration_to_str(self.overdue), self.accomplished,
            self.for_tomorrow)
