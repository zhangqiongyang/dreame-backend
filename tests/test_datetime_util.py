from datetime import timedelta

from app.utils.datetime_util import as_utc, utcnow


def test_compare_aware_with_mysql_naive():
    expire_at_naive = (utcnow() + timedelta(hours=24)).replace(tzinfo=None)
    assert as_utc(utcnow()) < as_utc(expire_at_naive)

    expired_naive = (utcnow() - timedelta(hours=1)).replace(tzinfo=None)
    assert as_utc(utcnow()) > as_utc(expired_naive)
