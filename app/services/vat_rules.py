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


def validate_vat_status_change(vat: Vat, new_status: str, latest: Optional[DipLot]) -> None:
    if new_status == Vat.STATUS_READY:
        assert_can_mark_ready(latest)


# ---- 可染色档案锁 ----

#: 可染色时锁定的档案字段：染种 / 缸容升数
PROFILE_LOCKED_FIELDS = ("dyeType", "volumeL")


def is_profile_locked(vat: Vat) -> bool:
    """缸处于可染色时档案只读；回到闲置（或还原中）后允许再改。

    页面展示与保存接口共用此判定，保证两入口结论一致。
    """
    return vat.status == Vat.STATUS_READY


def assert_can_edit_profile(vat: Vat, dye_type: str, volume_l: Decimal) -> None:
    """可染色缸禁止修改染种与缸容升数（浸染仍可追加）；未变更的提交放行。"""
    if not is_profile_locked(vat):
        return
    changed = []
    if dye_type != vat.dyeType:
        changed.append("染种")
    if Decimal(volume_l) != Decimal(vat.volumeL):
        changed.append("缸容升数")
    if changed:
        raise VatRuleError(
            f"染缸 {vat.code} 正处于可染色状态，{'、'.join(changed)}禁止修改；"
            "浸染仍可追加，如需调整请先改回闲置。"
        )
