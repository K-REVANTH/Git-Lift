from imagekitio import ImageKit
from app.settings import get_settings

settings = get_settings()

imagekit = ImageKit(
    private_key=settings.imagekit_private_key,
    public_key=settings.imagekit_public_key,
    url_endpoint=settings.imagekit_url,
)
