from __future__ import annotations

from typing import Any, Dict, List

from backend.core.db import connect
from backend.core.settings import get_setting


def get_enabled_affiliates() -> List[Dict[str, Any]]:
    """
    Returns a list of enabled affiliates from the database.
    """
    with connect() as cx:
        cur = cx.execute(
            "SELECT name, url, tag FROM affiliates WHERE enabled = 1 ORDER BY name ASC"
        )
        return [dict(row) for row in cur.fetchall()]


def build_affiliate_footer() -> str:
    """
    Builds an affiliate footer string based on enabled affiliates and settings.
    """
    # Check if affiliate embedding is enabled
    embed_enabled = get_setting("affiliate_embed_enabled", "false").lower() == "true"
    if not embed_enabled:
        return ""

    affiliates = get_enabled_affiliates()
    if not affiliates:
        return ""

    # Get footer template from settings
    template = get_setting(
        "affiliate_footer_template",
        "\\n\\n--- Affiliate Links ---\\n{links}\\n\\nSupport us by using these links!",
    )

    # Build links
    links = []
    for aff in affiliates:
        name = aff["name"]
        url = aff["url"]
        tag = aff.get("tag", "")

        # Add tag to URL if present
        final_url = url
        if tag:
            separator = "&" if "?" in url else "?"
            final_url = f"{url}{separator}{tag}"

        links.append(f"• {name}: {final_url}")

    return template.format(links="\\n".join(links))
