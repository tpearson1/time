# Time Management Program

import config_utils as cfgu
import config as cfg
import os.path

from datetime import datetime, date, timedelta

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

LOG_FILE = "data/log.txt"

DISPLAY_WEEK = 0
DISPLAY_MONTH = 1
DISPLAY_YEAR = 2
DISPLAY_ALL = 3


def chosen_event_text():
    chosen = cfg.pick_event()
    if chosen is None:
        return "No chosen event"

    days = chosen.days_till_event()
    return "{} day{} from now: {}".format(days, "" if days == 1 else "s",
                                          chosen.description)


def duration_from_str(duration):
    # Get as a date-time
    dt = datetime.strptime(duration, "%H:%M:%S")
    # Take the hours, minutes and seconds to construct a timedelta
    return cfgu.make_duration(dt.hour, dt.minute, dt.second)


def longer_than(duration1, duration2):
    return (duration1 - duration2).total_seconds() > 0


class LogEntry:
    def for_today(expected_time_working, time_worked, overdue, accomplished,
                  for_tomorrow):
        return LogEntry(date.today(), expected_time_working, time_worked,
                        overdue, accomplished, for_tomorrow)

    def from_str(text):
        results = text.split("\t")
        return LogEntry(
            datetime.strptime(results[0], "%Y-%m-%d").date(),
            duration_from_str(results[1]), duration_from_str(results[2]),
            duration_from_str(results[3]), results[4], results[5])

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
            self.entry_date, self.expected_time_working, self.time_worked,
            self.overdue, self.accomplished, self.for_tomorrow)


def write_to_log(log_entry):
    f = None
    if not os.path.exists(LOG_FILE):
        f = open(LOG_FILE, "w")
        f.write("Date\tExpected Time Working\tTime Worked\t"
                "Overdue\tAccomplished\tFor Tomorrow\n")
    else:
        f = open(LOG_FILE, "a")

    f.write(str(log_entry) + "\n")
    f.close()


def read_log():
    try:
        f = open(LOG_FILE)
        # Ignore first line which states the columns
        lines = f.readlines()[1:]

        entries = []
        for entry in lines:
            if entry != "":
                entries.append(LogEntry.from_str(entry))
        return entries
    except IOError:
        # File didn't exist - empty log
        return []


def create_data_dir():
    if not os.path.exists("data"):
        os.makedirs("data")


class Main:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("interface.glade")

        handlers = {
            "on-destroy":
            self.shutdown_app,
            "start-counting":
            lambda _: self.continue_counting(),
            "stop-counting":
            lambda _: self.stop_counting(),
            "finish-work":
            lambda _: self.finish_work(),
            "build-week-display":
            lambda _: self.build_log_display(DISPLAY_WEEK),
            "build-month-display":
            lambda _: self.build_log_display(DISPLAY_MONTH),
            "build-year-display":
            lambda _: self.build_log_display(DISPLAY_YEAR),
            "build-full-display":
            lambda _: self.build_log_display(DISPLAY_ALL)
        }
        self.builder.connect_signals(handlers)

        self.window = self.builder.get_object("main-window")
        self.window.show_all()

        self.has_clicked_finish = False

        self.get_event_and_message()
        self.setup_times()

        self.log_list_store = self.builder.get_object("work-log-data")
        self.build_log_display(DISPLAY_WEEK)

    def get_event_and_message(self):
        next_event_label = self.builder.get_object("next-event")
        next_event_label.set_text(chosen_event_text())

        create_data_dir()

        self.log = read_log()
        if len(self.log) == 0:
            # New to the app
            message = \
                "First day using this software - You will be able to give "\
                "yourself tomorrow's task(s) at the end of today's work"
        else:
            message = self.log[-1].for_tomorrow

        message_for_day = self.builder.get_object("message-for-day")
        message_for_day.set_text(message)

    def get_overdue(self):
        if len(self.log) == 0:
            # No overdue time from an empty log
            return cfgu.make_duration(0)

        last_entry = self.log[-1]
        if self.log_entry_for_today_present():
            # Overdue time carries over from previous days
            return last_entry.overdue
        else:
            unworked_from_earlier = \
                last_entry.expected_time_working - last_entry.time_worked
            if unworked_from_earlier.total_seconds() > 0:
                return last_entry.overdue + unworked_from_earlier
            return last_entry.overdue

    def remaining_time_to_work_today(self):
        if len(self.log) == 0:
            return cfg.expected_work_time_today()

        last_entry = self.log[-1]
        if self.log_entry_for_today_present():
            unworked = last_entry.expected_time_working - last_entry.time_worked
            if unworked.total_seconds() > 0:
                return unworked
            else:
                # No work required today
                return cfgu.make_duration(0)
        else:
            # Since they haven't worked today yet, we can just use the
            # expected work time for today
            return cfg.expected_work_time_today()

    def setup_times(self):
        self.time_remaining_label = self.builder.get_object("time-remaining")
        self.time_for_today_label = self.builder.get_object("time-for-today")
        self.overdue_label = self.builder.get_object("overdue")

        self.time_for_today = self.remaining_time_to_work_today()
        self.time_for_today_secs = self.time_for_today.total_seconds()

        self.overdue = self.get_overdue()
        self.overdue_secs = self.overdue.total_seconds()

        self.time_worked_secs = 0

        GObject.timeout_add_seconds(1, self.update_times)
        self.stop_counting()
        self.set_times()

    def stop_counting(self):
        self.currently_counting = False

    def continue_counting(self):
        self.currently_counting = True
        GObject.timeout_add_seconds(1, self.update_times)

    def update_times(self):
        if not self.currently_counting:
            return

        self.time_worked_secs += 1

        if self.time_for_today_secs > 0:
            self.time_for_today_secs -= 1
            if self.time_for_today_secs == 0:
                self.done_time_for_today()
        elif self.overdue_secs > 0:
            self.overdue_secs -= 1
            if self.overdue_secs == 0:
                self.stop_counting()
                self.done_all_time()
                self.set_times()
                return

        self.set_times()
        GObject.timeout_add_seconds(1, self.update_times)

    def get_time_remaining(self):
        return self.time_for_today_secs + self.overdue_secs

    def create_message_box(self, text):
        message = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO,
                                    Gtk.ButtonsType.CLOSE, text)
        message.run()
        message.destroy()

    def done_time_for_today(self):
        message_text = "You have completed all of today's scheduled work time"
        if self.overdue_secs != 0:
            message_text += ", but there is still overdue work for you"
        self.create_message_box(message_text)

    def done_all_time(self):
        self.create_message_box(
            "You have completed all of your scheduled work time")

    def log_entry_for_today_present(self):
        if len(self.log) == 0:
            return False
        return self.log[-1].entry_date == date.today()

    def finish_work(self):
        self.has_clicked_finish = True
        self.stop_counting()

        accomplished = self.builder.get_object("work-today").get_text()
        for_tomorrow = self.builder.get_object("work-tomorrow").get_text()

        time_worked = timedelta(seconds=self.time_worked_secs)
        if self.log_entry_for_today_present():
            # Add time done earlier today
            time_worked += self.log[-1].time_worked
        overdue = timedelta(seconds=self.overdue_secs)

        if self.log_entry_for_today_present():
            f = open(LOG_FILE)
            lines = f.readlines()
            f.close()
            lines[-1] = str(
                LogEntry.for_today(cfg.expected_work_time_today(), time_worked,
                                   overdue, accomplished, for_tomorrow))
            f = open(LOG_FILE, "w")
            f.writelines(lines)
            f.close()
        else:
            write_to_log(
                LogEntry.for_today(cfg.expected_work_time_today(), time_worked,
                                   overdue, accomplished, for_tomorrow))

    def set_times(self):
        self.time_remaining_label.set_text(
            str(timedelta(seconds=self.get_time_remaining())))
        self.time_for_today_label.set_text(
            str(timedelta(seconds=self.time_for_today_secs)))
        self.overdue_label.set_text(str(timedelta(seconds=self.overdue_secs)))

    def shutdown_app(self, o, d=None):
        if not self.has_clicked_finish:
            self.finish_work()
        Gtk.main_quit(o, d)

    def build_log_display(self, period):
        self.log_list_store.clear()
        for entry in self.log:
            entry_age = date.today() - entry.entry_date
            if period == DISPLAY_WEEK:
                if longer_than(entry_age, timedelta(weeks=1)):
                    continue
            if period == DISPLAY_MONTH:
                if longer_than(entry_age, timedelta(days=30)):
                    continue
            if period == DISPLAY_YEAR:
                if longer_than(entry_age, timedelta(days=365)):
                    continue

            self.log_list_store.append([
                str(entry.entry_date),
                str(entry.expected_time_working),
                str(entry.time_worked),
                str(entry.overdue), entry.accomplished, entry.for_tomorrow
            ])


Main()
Gtk.main()
