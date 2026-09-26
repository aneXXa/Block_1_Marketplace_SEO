from marketplace_poster.platforms.avito import AVITO
from marketplace_poster.platforms.base import PlatformId, PlatformRulePack
from marketplace_poster.platforms.ozon import OZON
from marketplace_poster.platforms.wildberries import WILDBERRIES

PLATFORMS: dict[PlatformId, PlatformRulePack] = {
    pack.id: pack for pack in (WILDBERRIES, OZON, AVITO)
}


def get_platform(platform_id: str | PlatformId) -> PlatformRulePack:
    key = platform_id if isinstance(platform_id, PlatformId) else PlatformId(platform_id)
    return PLATFORMS[key]


__all__ = [
    "AVITO",
    "OZON",
    "PLATFORMS",
    "PlatformId",
    "PlatformRulePack",
    "WILDBERRIES",
    "get_platform",
]
