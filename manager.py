#!/usr/bin/python

# Time Management Program

import config_utils as cfgu
import config as cfg
import os.path

import parts.timer as timer
import parts.duration as duration
import parts.logentry as logentry
import parts.log as log

from datetime import datetime, date, timedelta

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

PROGRAM_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = PROGRAM_DIR + "/data"
LOG_FILE = DATA_DIR + "/log.txt"

DISPLAY_WEEK = 0
DISPLAY_MONTH = 1
DISPLAY_YEAR = 2
DISPLAY_ALL = 3

FIRST_DAY_WORK_MESSAGE = "First day using this software - You will be able to give \
yourself tomorrow's task(s) at the end of today's work"


def chosen_event_text():
    chosen = cfg.pick_event()
    if chosen is None:
        return "No chosen event"

    days = chosen.days_till_event()
    if days == 0:
        return "Today: " + chosen.description
    return "{} day{} from now: {}".format(days, "" if days == 1 else "s",
                                          chosen.description)


def create_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


class Main:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(PROGRAM_DIR + "/interface.glade")

        self.timer = timer.Timer(self.update_times)
        create_data_dir()
        self.log = log.Log(LOG_FILE)

        handlers = {
            "on-destroy":
            self.shutdown_app,
            "start-counting":
            lambda _: self.start_timer(),
            "stop-counting":
            lambda _: self.stop_timer(),
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

        self.setup_work_input_boxes()

    def start_timer(self):
        self.timer.start()
        # Prevent clicking the button multiple times
        self.start_timer_button.set_sensitive(False)
        self.stop_timer_button.set_sensitive(True)

    def stop_timer(self):
        self.timer.stop()
        # Prevent clicking the button multiple times
        self.stop_timer_button.set_sensitive(False)
        self.start_timer_button.set_sensitive(True)

    def setup_work_input_boxes(self):
        self.accomplished_input_box = self.builder.get_object("work-today")
        self.for_tomorrow_input_box = self.builder.get_object("work-tomorrow")

        today = self.log.entry_for_today()
        if today is None:
            return
        self.accomplished_input_box.set_text(today.accomplished)
        self.for_tomorrow_input_box.set_text(today.for_tomorrow)

    def work_message(self):
        prev = self.log.entry_before_today()
        if prev is None:
            return FIRST_DAY_WORK_MESSAGE
        return prev.for_tomorrow

    def get_event_and_message(self):
        next_event_label = self.builder.get_object("next-event")
        next_event_label.set_text(chosen_event_text())

        message_for_day = self.builder.get_object("message-for-day")
        message_for_day.set_text(self.work_message())

    def get_overdue(self):
        latest = self.log.latest_entry()

        if latest is None:
            # No overdue time from an empty log
            return cfgu.make_duration(0)

        if self.log.entry_for_today_present():
            # Overdue time carries over from previous days
            return latest.overdue
        else:
            unworked_from_earlier = \
                latest.expected_time_working - latest.time_worked
            if unworked_from_earlier.total_seconds() > 0:
                return latest.overdue + unworked_from_earlier
            return latest.overdue

    def remaining_work_time_today(self):
        if self.log.is_empty():
            return cfg.expected_work_time_today()

        today = self.log.entry_for_today()
        if today is not None:
            unworked = today.expected_time_working - today.time_worked
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

        self.start_timer_button = self.builder.get_object("start-timer")
        self.stop_timer_button = self.builder.get_object("stop-timer")

        # Should not be able to click stop unless the timer is running
        self.stop_timer_button.set_sensitive(False)

        self.time_for_today = self.remaining_work_time_today()
        self.time_for_today_secs = self.time_for_today.total_seconds()

        self.overdue_secs = self.get_overdue().total_seconds()

        self.time_worked_secs = 0
        self.set_times()

    def update_times(self):
        self.time_worked_secs += 1

        if self.time_for_today_secs > 0:
            self.time_for_today_secs -= 1
            if self.time_for_today_secs == 0:
                self.done_time_for_today()
        elif self.overdue_secs > 0:
            self.overdue_secs -= 1
            if self.overdue_secs == 0:
                self.timer.stop()
                self.done_all_time()

        self.set_times()

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
            message_text += ", but there is still overdue work to do"
        self.create_message_box(message_text)

    def done_all_time(self):
        self.create_message_box(
            "You have completed all of today's scheduled work time")

    def finish_work(self):
        self.has_clicked_finish = True
        self.timer.stop()

        accomplished = self.builder.get_object("work-today").get_text()
        for_tomorrow = self.builder.get_object("work-tomorrow").get_text()

        time_worked = timedelta(seconds=self.time_worked_secs)
        overdue = timedelta(seconds=self.overdue_secs)

        today = self.log.entry_for_today()
        if today is not None:
            today.time_worked += time_worked
            today.overdue = overdue
            today.accomplished = accomplished
            today.for_tomorrow = for_tomorrow
            self.log.push_entry(today)
        else:
            self.log.push_entry(
                logentry.LogEntry.for_today(cfg.expected_work_time_today(),
                                            time_worked, overdue, accomplished,
                                            for_tomorrow))

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
        for entry in self.log.entries:
            entry_age = date.today() - entry.entry_date
            if period == DISPLAY_WEEK:
                if duration.longer_than(entry_age, timedelta(weeks=1)):
                    continue
            if period == DISPLAY_MONTH:
                if duration.longer_than(entry_age, timedelta(days=30)):
                    continue
            if period == DISPLAY_YEAR:
                if duration.longer_than(entry_age, timedelta(days=365)):
                    continue

            self.log_list_store.append([
                str(entry.entry_date),
                str(entry.expected_time_working),
                str(entry.time_worked),
                str(entry.overdue), entry.accomplished, entry.for_tomorrow
            ])


Main()
Gtk.main()
