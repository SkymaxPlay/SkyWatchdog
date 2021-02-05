import datetime


def format_dt(dt=None):
    if dt is None:
        dt = datetime.datetime.now()

    return dt.strftime("%d.%m.%Y %H:%M:%S")
