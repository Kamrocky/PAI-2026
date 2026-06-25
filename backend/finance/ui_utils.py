MODAL_CLOSE_HTML = '<div id="home-modal" hx-swap-oob="innerHTML"></div>'


def inject_oob_outer_swap(html: str, element_id: str) -> str:
    needle = f'id="{element_id}"'
    replacement = f'id="{element_id}" hx-swap-oob="outerHTML"'
    if needle not in html:
        return html
    return html.replace(needle, replacement, 1)


def prepend_modal_close(content: str) -> str:
    return MODAL_CLOSE_HTML + content


def prepend_modal_close_to_response(response):
    response.content = prepend_modal_close(response.content.decode()).encode()
    return response
