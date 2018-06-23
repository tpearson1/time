from . import logentry

from datetime import date
import os.path

LOG_HEADER = "Date\tExpected Time Working\tTime Worked\t"
"Overdue\tAccomplished\tFor Tomorrow\n"


class Log:
    def __init__(self, path):
        self.path = path
        self.read()

    def read(self):
        self.entries = []

        try:
            f = open(self.path)
            # Ignore first line which states the columns
            lines = f.readlines()[1:]
            for entry_text in lines:
                if entry_text != "":
                    # We do not want to include the newline character
                    self.entries.append(
                        logentry.LogEntry.from_str(entry_text[:-1]))
        except:
            pass  # Empty list of entries

    def is_empty(self):
        return len(self.entries) == 0

    def latest_entry(self):
        if len(self.entries) == 0:
            return None
        return self.entries[-1]

    def entry_before_today(self):
        if len(self.entries) == 0:
            # There isn't one
            return None

        if not self.entry_for_today_present():
            # The most recent entry is before today
            return self.entries[-1]

        if len(self.entries) == 1:
            # This entry is for today, so there isn't an entry before today
            return None

        # The entry before today's
        return self.entries[-2]

    def entry_for_today_present(self):
        if self.is_empty():
            return False
        return self.latest_entry().entry_date == date.today()

    def entry_for_today(self):
        if self.entry_for_today_present():
            return self.latest_entry()
        return None

    def push_entry(self, log_entry):
        if len(self.entries) == 0:
            # Add the first LogEntry
            self.entries.append(log_entry)
            # Create the log file, adding the header and the first entry
            f = open(self.path, "w")
            f.write(LOG_HEADER)
            f.write(str(log_entry) + "\n")
        elif self.entries[-1].entry_date != log_entry.entry_date:
            # This is a new LogEntry, so add to the end of the list and file
            self.entries.append(log_entry)
            f = open(self.path, "a")
            f.write(str(log_entry) + "\n")
        else:
            # Updating the last entry in the list
            self.entries[-1] = log_entry
            # Change the last line (last LogEntry) in the file. This is done by
            # reading in the file's lines, modifying the last line, and then
            # writing them all back in.
            f = open(self.path)
            lines = f.readlines()
            f.close()
            lines[-1] = str(log_entry)
            f = open(self.path, "w")
            f.writelines(lines)
            f.write("\n")

        f.close()
