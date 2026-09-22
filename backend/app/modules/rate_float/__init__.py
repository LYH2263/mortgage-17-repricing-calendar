"""起息日重定价窗：纯月日窗口逻辑（无 I/O）。"""
import calendar


def valid_month_day(month: int, day: int) -> bool:
    """月日是否合法。以闰年 2000 年定天数，故 2-29 始终允许作为窗界/起息日。"""
    if not isinstance(month, int) or not isinstance(day, int):
        return False
    if month < 1 or month > 12:
        return False
    return 1 <= day <= calendar.monthrange(2000, month)[1]


def in_window(month: int, day: int,
              sm: int, sd: int, em: int, ed: int) -> bool:
    """(month, day) 是否落在 [sm-sd, em-ed] 窗内，两端含。窗可跨年。"""
    cur = (month, day)
    start = (sm, sd)
    end = (em, ed)
    if start <= end:
        return start <= cur <= end
    # 跨年窗，如 12-01 ~ 02-28：>= 起点 或 <= 终点
    return cur >= start or cur <= end


def resolve_rate(rule: dict, month: int, day: int) -> tuple[bool, float]:
    """按起息月日从规则取价，返回 (是否命中窗, 年利率)。"""
    hit = in_window(month, day,
                    rule["start_month"], rule["start_day"],
                    rule["end_month"], rule["end_day"])
    return hit, float(rule["in_rate"] if hit else rule["out_rate"])
