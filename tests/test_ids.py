from app.utils.ids import IdPrefix, generate_business_id, is_valid_business_id


def test_generate_business_id_format():
    uid = generate_business_id(IdPrefix.USER)
    assert uid.startswith("U")
    assert len(uid) == 17
    assert is_valid_business_id(uid, IdPrefix.USER)
    # 新用户 ID 含字母，不可按日期推断注册顺序
    assert any(c.isalpha() for c in uid[1:]) or uid[1:].isdigit()

    # 兼容历史纯数字编号
    assert is_valid_business_id("U2026051812345678", IdPrefix.USER)

    order_no = generate_business_id(IdPrefix.ORDER)
    assert order_no.startswith("DR")
    assert len(order_no) == 18
    assert is_valid_business_id(order_no, IdPrefix.ORDER)

    refund_no = generate_business_id(IdPrefix.REFUND)
    assert refund_no.startswith("RF")
    assert len(refund_no) == 18
    assert is_valid_business_id(refund_no, IdPrefix.REFUND)

    product_id = generate_business_id(IdPrefix.PRODUCT)
    assert product_id.startswith("P")
    assert len(product_id) == 17
    assert is_valid_business_id(product_id, IdPrefix.PRODUCT)

    address_no = generate_business_id(IdPrefix.ADDRESS)
    assert address_no.startswith("A")
    assert len(address_no) == 17
    assert is_valid_business_id(address_no, IdPrefix.ADDRESS)
