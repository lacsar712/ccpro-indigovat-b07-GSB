"""染缸状态业务规则。"""

from decimal import Decimal
from typing import Optional

from app.models import DipLot, Vat


class VatRuleError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def assert_can_mark_ready(latest: Optional[DipLot]) -> None:
    """不能将染缸标为 ready，除非最新浸染批次 redoxMv 已填且 <= -500。"""
    if latest is None or latest.redoxMv is None or Decimal(latest.redoxMv) > Decimal("-500"):
        raise VatRuleError(
            "无法设为可染色：最新浸染批次的氧化还原电位为空或高于 -500 mV。"
        )


def vat_config_locked(vat: Vat) -> bool:
    """染种与缸容升数是否只读：缸处于可染色(ready)时锁定，回到闲置后才可改。

    页面展示与保存接口共用本判定，保证两个入口结论一致。
    浸染记录不受此限制，ready 状态下仍可追加。
    """
    return vat.status == Vat.STATUS_READY


def assert_can_edit_vat_config(vat: Vat) -> None:
    if vat_config_locked(vat):
        raise VatRuleError(
            "该缸当前为可染色状态，染种与缸容升数禁止修改；"
            "浸染仍可继续追加，回到闲置后才可修改。"
        )


def validate_vat_status_change(vat: Vat, new_status: str, latest: Optional[DipLot]) -> None:
    if new_status == Vat.STATUS_READY:
        assert_can_mark_ready(latest)
