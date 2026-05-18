"""与 dreame-web-mini catalog 对齐的商品种子数据（price 为元，写入 DB 时转分）。"""

from app.data.product_ids import PRODUCT_ID_STANDARD, PRODUCT_ID_STATION, PRODUCT_ID_X1_PRO

PRODUCT_SEEDS = [
    {
        "id": PRODUCT_ID_STANDARD,
        "name": "追觅C1 标准版",
        "price": 1599,
        "market_price": 1899,
        "tags": ["5500Pa吸力", "轻巧灵活"],
        "cover_url": "https://modao.cc/agent-py/media/generated_images/2026-05-13/45347639c88141bbb0737f7373952ecf.jpg",
        "is_hot": False,
        "sort": 1,
        "title": "追觅C1 标准版擦窗机器人 5500Pa大吸力 轻巧灵活",
        "promo": "限时特惠",
        "spec_tags": ["5500Pa大吸力", "AI路径规划", "自动回充", "双盘旋转"],
        "params": [
            {"label": "最大吸力", "value": "5500 Pa"},
            {"label": "续航时间", "value": "180 min"},
            {"label": "水箱容量", "value": "80 ml"},
            {"label": "主机重量", "value": "1.25 kg"},
        ],
        "highlights": [
            {"title": "一体化基站设计", "desc": "解决线缆杂乱、断电跌落痛点。"},
            {"title": "CornerClean 覆盖边角", "desc": "算法与结构优化，死角清洁到位。"},
        ],
        "hero_image": "https://modao.cc/agent-py/media/generated_images/2026-05-13/a54a7560b55f4238a1be9b4c39848808.jpg",
        "detail_images": [
            "https://modao.cc/agent-py/media/generated_images/2026-05-13/f6f81e9026294382b8183fd4c847fe26.jpg",
            "https://modao.cc/agent-py/media/generated_images/2026-05-13/2ad55e46d3864757a96f8145c14542f4.jpg",
        ],
    },
    {
        "id": PRODUCT_ID_STATION,
        "name": "追觅C1 Station 基站版",
        "price": 3499,
        "market_price": 3999,
        "tags": ["自动回充基站", "自动收线"],
        "cover_url": "https://modao.cc/agent-py/media/generated_images/2026-05-13/5a7cb077303f46c8af73a97277b8e289.jpg",
        "is_hot": True,
        "sort": 2,
        "title": "追觅C1 Station 基站版擦窗机器人 自动回充 自动收线续擦 CornerClean边角清洁",
        "promo": "限时特惠",
        "spec_tags": ["5500Pa大吸力", "AI路径规划", "自动回充", "双盘旋转"],
        "params": [
            {"label": "最大吸力", "value": "5500 Pa"},
            {"label": "续航时间", "value": "180 min"},
            {"label": "水箱容量", "value": "80 ml"},
            {"label": "主机重量", "value": "1.25 kg"},
        ],
        "highlights": [
            {"title": "一体化基站设计", "desc": "解决线缆杂乱、断电跌落痛点。"},
            {"title": "CornerClean 覆盖边角", "desc": "算法与结构优化，死角清洁到位。"},
        ],
        "hero_image": "https://modao.cc/agent-py/media/generated_images/2026-05-13/a54a7560b55f4238a1be9b4c39848808.jpg",
        "detail_images": [
            "https://modao.cc/agent-py/media/generated_images/2026-05-13/f6f81e9026294382b8183fd4c847fe26.jpg",
            "https://modao.cc/agent-py/media/generated_images/2026-05-13/2ad55e46d3864757a96f8145c14542f4.jpg",
        ],
    },
    {
        "id": PRODUCT_ID_X1_PRO,
        "name": "追觅X1 Pro 旗舰款",
        "price": 2699,
        "market_price": 2999,
        "tags": ["双面清洁", "AI视觉导航"],
        "cover_url": "https://modao.cc/agent-py/media/generated_images/2026-05-13/2ab31038c48c4eaebe960679283e93f8.jpg",
        "is_hot": False,
        "sort": 3,
        "title": "追觅X1 Pro 旗舰款 双面清洁 AI视觉导航",
        "promo": "限时特惠",
        "spec_tags": ["5500Pa大吸力", "AI路径规划", "自动回充", "双盘旋转"],
        "params": [
            {"label": "最大吸力", "value": "5500 Pa"},
            {"label": "续航时间", "value": "180 min"},
            {"label": "水箱容量", "value": "80 ml"},
            {"label": "主机重量", "value": "1.25 kg"},
        ],
        "highlights": [
            {"title": "一体化基站设计", "desc": "解决线缆杂乱、断电跌落痛点。"},
            {"title": "CornerClean 覆盖边角", "desc": "算法与结构优化，死角清洁到位。"},
        ],
        "hero_image": "https://modao.cc/agent-py/media/generated_images/2026-05-13/a54a7560b55f4238a1be9b4c39848808.jpg",
        "detail_images": [
            "https://modao.cc/agent-py/media/generated_images/2026-05-13/f6f81e9026294382b8183fd4c847fe26.jpg",
            "https://modao.cc/agent-py/media/generated_images/2026-05-13/2ad55e46d3864757a96f8145c14542f4.jpg",
        ],
    },
]
