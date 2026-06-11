from urllib.parse import urlparse

from rest_framework import serializers


ALLOWED_VIDEO_HOST = "youtube.com"


def validate_youtube_url(value: str) -> str:
    """В поле для видеоурока разрешаются только ссылки на youtube.com.

    Использование внешних образовательных платформ и личных веб-сайтов запрещено.
    Допустимые примеры: https://youtube.com/watch?v=..., https://www.youtube.com/watch?v=...
    """
    if not value:
        return value

    parsed_url = urlparse(value)
    host = parsed_url.netloc.lower()

    if host.startswith("www."):
        host = host[4:]

    if host != ALLOWED_VIDEO_HOST and not host.endswith(f".{ALLOWED_VIDEO_HOST}"):
        raise serializers.ValidationError(
            "Разрешены только ссылки на видео с домена youtube.com."
        )

    return value
