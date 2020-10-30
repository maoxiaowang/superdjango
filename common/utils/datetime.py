import datetime
import re
import time
import typing

import pytz
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext_lazy as _n, gettext

__all__ = [
    'str_to_datetime',
    'to_aware_datetime',
    'humanize_seconds',
    'datetime_to_countdown',
    'millisecond_timestamp_to_datetime',
]

YEAR_MONTH_DAY = "%Y-%m-%d"


def str_to_datetime(date_string, fmt='%Y-%m-%d %H:%M:%S'):
    """
    Support style:
    2018-12-07T06:24:24.000000
    2018-12-07T06:24:24Z
    2018-12-07 06:24:24
    ...
    """
    ds = re.findall(r'^(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2}:\d{2}).*$', date_string)
    if not ds:
        raise ValueError('Invalid datetime string: %s' % date_string)
    ds = ds[0]
    date_string = '%s %s' % (ds[0], ds[1])
    return datetime.datetime.strptime(date_string, fmt)


def to_aware_datetime(dt: typing.Union[str, datetime.datetime], tz=None):
    """
    Make an naive datetime using a given timezone(tz)

    Notice: tz if the timezone of dt, make sure they are matched
    """
    if dt is None:
        return
    if tz is None:
        tz = timezone.get_current_timezone()
    else:
        if isinstance(tz, str):
            tz = pytz.timezone(tz)
    if isinstance(dt, datetime.datetime):
        if timezone.is_aware(dt):
            return dt
        else:
            # Asia/Shanghai, same to settings
            return timezone.make_aware(dt)
    elif isinstance(dt, str):
        dt = str_to_datetime(dt)
        aware = timezone.make_aware(dt, timezone=tz)
        return aware
    raise ValueError


def humanize_seconds(secs: int):
    """
    seconds turn into hummable datetime string
    """
    a_day = 86400
    an_hour = 3600
    a_minute = 60
    timetot = ''
    total_secs = secs
    if secs > a_day:  # 60sec * 60min * 24hrs
        days = int(secs // a_day)
        # timetot += "{} {}".format(int(days), _('days'))
        timetot += _n('%(num)s day', '%(num)s days', days) % {'num': days}
        secs = secs - days * a_day

    if secs > an_hour:
        hrs = int(secs // an_hour)
        # timetot += " {} {}".format(int(hrs), _('hours'))
        timetot += ' '
        timetot += _n('%(num)s hour', '%(num)s hours', hrs) % {'num': hrs}
        secs = secs - hrs * an_hour

    if secs > a_minute and total_secs < a_day:
        mins = int(secs // a_minute)
        timetot += ' '
        timetot += _n('%(num)s minute', '%(num)s minutes', mins) % {'num': mins}
        secs = secs - mins * a_minute

    if secs > 0 and total_secs < an_hour:
        secs = int(secs)
        timetot += ' '
        timetot += _n('%(num)s second', '%(num)s seconds', secs) % {'num': secs}
    return timetot


def datetime_to_countdown(dt: typing.Union[str, datetime.datetime], show_direction=True):
    """
    Convert a datetime.timedelta object into Days, Hours, Minutes, Seconds.
    """
    if isinstance(dt, str):
        dt = to_aware_datetime(dt)
    delta = dt - timezone.datetime.now(tz=timezone.get_current_timezone())
    a_day = 86400
    an_hour = 3600
    a_minute = 60
    timetot = ''
    total_secs = secs = delta.total_seconds()
    if secs > 0:
        direction = _('later')
    elif secs < 0:
        direction = _('ago')
        total_secs = -total_secs
        secs = -secs
    else:
        return _('now')
    if secs > a_day:  # 60sec * 60min * 24hrs
        days = int(secs // a_day)
        # timetot += "{} {}".format(int(days), _('days'))
        timetot += _n('%(num)s day', '%(num)s days', days) % {'num': days}
        secs = secs - days * a_day

    if secs > an_hour:
        hrs = int(secs // an_hour)
        # timetot += " {} {}".format(int(hrs), _('hours'))
        timetot += ' '
        timetot += _n('%(num)s hour', '%(num)s hours', hrs) % {'num': hrs}
        secs = secs - hrs * an_hour

    if secs > a_minute and total_secs < a_day:
        mins = int(secs // a_minute)
        timetot += ' '
        timetot += _n('%(num)s minute', '%(num)s minutes', mins) % {'num': mins}
        secs = secs - mins * a_minute

    if secs > 0 and total_secs < an_hour:
        secs = int(secs)
        timetot += ' '
        timetot += _n('%(num)s second', '%(num)s seconds', secs) % {'num': secs}

    if not timetot and secs == 0:
        timetot = gettext('just now')
    else:
        if show_direction:
            timetot += ' %s' % direction
    return timetot


def timestamp_to_datetime(stamp, tz=False):
    """
    将时间戳转换为datetime类型时间
    :param stamp: 时间戳
    :param tz: 是否带时区默认不带
    :return:
    """
    assert int(stamp)

    date_array = datetime.datetime.fromtimestamp(stamp)
    if tz:
        date_array = to_aware_datetime(date_array)
    format_time = date_array.strftime("%Y-%m-%d %H:%M:%S")

    return format_time


def millisecond_timestamp_to_datetime(timeNum):
    """
    毫秒时间戳转换为time
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(timeNum / 1000)))
