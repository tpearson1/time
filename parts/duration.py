import config_utils as cfgu


def duration_from_str(duration):
    # Split by colon character
    elems = duration.split(":")
    try:
        if len(elems) != 3:
            raise ValueError

        hours = int(elems[0])
        minutes = int(elems[1])
        seconds = int(elems[2])
        return cfgu.make_duration(hours, minutes, seconds)

    except ValueError:
        print("Invalid time duration in log file")
        return cfgu.make_duration(0, 0, 0)


def duration_to_str(duration):
    rem_secs = int(duration.total_seconds())
    secs = rem_secs % 60
    rem_secs -= secs
    sec_minutes = rem_secs % 3600
    minutes = sec_minutes // 60
    rem_secs -= sec_minutes
    hours = rem_secs // 3600
    return "{}:{:02}:{:02}".format(hours, minutes, secs)


def longer_than(duration1, duration2):
    return (duration1 - duration2).total_seconds() > 0
