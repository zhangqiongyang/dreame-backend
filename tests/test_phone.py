import pytest

from app.utils.phone import PHONE_INVALID_MSG, normalize_phone, validate_cn_mobile, validate_cn_mobile_optional


def test_normalize_phone():
    assert normalize_phone(" 138 0013 8888 ") == "13800138888"
    assert normalize_phone("138-0013-8888") == "13800138888"


@pytest.mark.parametrize(
    "phone",
    ["13800138000", "15912345678", "18812345678", "19912345678"],
)
def test_validate_cn_mobile_ok(phone: str):
    assert validate_cn_mobile(phone) == phone


@pytest.mark.parametrize(
    "phone",
    ["", "12345678901", "23800138000", "12800138000", "1380013800", "138001380001", "abcdefghijk"],
)
def test_validate_cn_mobile_fail(phone: str):
    with pytest.raises(ValueError, match=PHONE_INVALID_MSG):
        validate_cn_mobile(phone)


def test_validate_cn_mobile_optional():
    assert validate_cn_mobile_optional(None) is None
    assert validate_cn_mobile_optional("") is None
    assert validate_cn_mobile_optional("13800138000") == "13800138000"
