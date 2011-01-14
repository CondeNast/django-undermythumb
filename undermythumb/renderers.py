try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


class BaseRenderer(object):
    """
    You can subclass this to get basic rendering behavior.

    """
    def __init__(self, format='jpg', quality=75, force_rgb=True,
            *args, **kwargs):
        self.format = format
        self.quality = quality
        self.force_rgb = force_rgb
        self.options = kwargs

    def _normalize_format(self):
        format = self.format.upper()
        if format in ['JPG']:
            format = 'JPEG'
        return format

    def _create_tmp_image(self, content):
        content.seek(0)
        image = Image.open(content)
        if self.force_rgb and image.mode not in ('L', 'RGB', 'RGBA'):
            image = image.convert('RGB')
        return image

    def _create_content_file(self, content):
        io = StringIO()
        content.save(io, self._normalize_format(), quality=self.quality)
        return ContentFile(io.getvalue())

    def generate(self, content):
        """
        Performs resizing on anything content that 'PIL.Image.open`
        excepts. This should return a `django.core.files.images.ImageFile`.

        """
        tmp = self._create_tmp_image(content)
        rendered = self._render(tmp)
        return self._create_content_file(rendered)

    def _render(self, image):
        """
        Subclasses need to provide this method. It should except
        a `PIL.Image` object and return a rendered `PIL.Image`.

        """
        raise NotImplementedError("No render method found.")


class CropRenderer(BaseRenderer):
    """
    Renders a image cropped to the width and height you provide.

    """
    def __init__(self, width, height, *args, **kwargs):
        self.width = width
        self.height = height
        super(CropRenderer, self).__init__(*args, **kwargs)

    def _render(self, image):
        return ImageOps.fit(image, (int(self.width), int(self.height)),
                            Image.ANTIALIAS, 0, (0.5, 0.5))


class ResizeRenderer(BaseRenderer):
    """
    Renders a image resized to the width and height you provide. The
    image will maintain its aspect ratio unless `constrain` is `False`.

    """
    def __init__(self, width, height, constrain=True, *args, **kwargs):
        self.width = width
        self.height = height
        self.constrain = constrain
        super(ResizeRenderer, self).__init__(*args, **kwargs)

    def _render(self, image):
        dw, dh = self.width, self.height
        if self.constrain:
            sw, sh = image.size
            sr = float(sw) / float(sh)
            if sw > sh:
                dh = dw / sr
            else:
                dh = dw * sr
        return image.resize((int(dw), int(dh)), Image.ANTIALIAS)
