from datetime import datetime, timedelta

from app.utils.datetime_util import TZ_CN, format_dt, now_cn


def test_now_cn_is_naive_beijing():
    t = now_cn()
    assert t.tzinfo is None
    # 与带时区的北京时间同一天同一小时（允许秒级误差）
    aware = datetime.now(TZ_CN)
    assert t.date() == aware.date()
    assert abs(t.hour - aware.hour) <= 1


def test_format_dt_direct():
    naive = datetime(2026, 5, 18, 15, 30, 0)
    assert format_dt(naive) == "2026-05-18 15:30"


def test_expire_compare():
    expire_at = now_cn() + timedelta(hours=24)
    assert now_cn() < expire_at
    expired = now_cn() - timedelta(hours=1)
    assert now_cn() > expired
