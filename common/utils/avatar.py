from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile


def process_user_avatar(avatar) -> InMemoryUploadedFile:
    """
    Process InMemoryUploadedFile
    return size: 256x256
    """

    im = Image.open(avatar)
    assert im.format.upper() in ('PNG', 'JPG', 'JPEG')

    mode = im.mode
    if mode not in ('L', 'RGB'):
        if mode == 'RGBA':
            alpha = im.split()[3]
            bgmask = alpha.point(lambda x: 255 - x)
            im = im.convert('RGB')
            # paste(color, box, mask)
            im.paste((255, 255, 255), None, bgmask)
        else:
            im = im.convert('RGB')

    width, height = im.size
    if width == height:
        region = im
    else:
        if width > height:
            delta = (width - height) / 2
            box = (delta, 0, delta + height, height)
        else:
            delta = (height - width) / 2
            box = (0, delta, width, delta + width)
        region = im.crop(box)

    a = region.resize((256, 256), Image.ANTIALIAS)  # anti-aliasing

    img_io = BytesIO()
    a.save(img_io, im.format)

    img_file = InMemoryUploadedFile(
        file=img_io,
        field_name=None,
        name=avatar.name,
        content_type=avatar.content_type,
        size=img_io.tell(),
        charset=None
    )
    return img_file
