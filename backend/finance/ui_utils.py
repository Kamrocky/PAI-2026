def inject_oob_outer_swap(html: str, element_id: str) -> str:
    needle = f'id="{element_id}"'
    replacement = f'id="{element_id}" hx-swap-oob="outerHTML"'
    if needle not in html:
        return html
    return html.replace(needle, replacement, 1)
