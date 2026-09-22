"""起息日重定价窗：按月日判断起息日是否落入利率窗，窗可跨年。"""

_DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def valid_month_day(month: int, day: int) -> bool:
    """月日是否合法（2 月允许 29 日，窗与具体年份无关）。"""
    return 1 <= month <= 12 and 1 <= day <= _DAYS_IN_MONTH[month - 1]


def _key(month: int, day: int) -> int:
    return month * 100 + day


def in_window(start_month: int, start_day: int, end_month: int, end_day: int, month: int, day: int) -> bool:
    """起息月日 (month, day) 是否落入 [窗起, 窗止]（两端含）。窗止小于窗起视为跨年窗。"""
    s = _key(start_month, start_day)
    e = _key(end_month, end_day)
    k = _key(month, day)
    if s <= e:
        return s <= k <= e
    return k >= s or k <= e
