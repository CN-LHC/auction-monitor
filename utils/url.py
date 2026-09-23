def absolute_url(url: str) -> str:
    if not url:
        return ""

    if url.startswith("//"):
        return "https:" + url

    return url
