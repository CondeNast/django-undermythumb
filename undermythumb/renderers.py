try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import struct

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
    Renders an image resized to the width and height you provide.
    The image will maintain its aspect ratio unless ``constrain``
    is ``False``. If desired dimensions are 
    """

    def __init__(self, width, height, constrain=True, upscale=False,
                 *args, **kwargs):
        self.width = width
        self.height = height
        self.constrain = constrain
        self.upscale = upscale
        super(ResizeRenderer, self).__init__(*args, **kwargs)

    def _render(self, image):
        dw, dh = self.width, self.height
        sw, sh = image.size
        
        if self.constrain:
            sr = float(sw) / float(sh)
            if sw > sh:
                dh = dw / sr
            else:
                dh = dw * sr

        # resize if the source dimensions are smaller than the desired,
        # or the user has requested upscaling
        if (((dw > sw) or (dh > sh)) and self.upscale) or \
               ((dw < sw) or (dh < sh)):
            image = image.resize((int(dw), int(dh)), Image.ANTIALIAS)

        return image


class LetterboxRenderer(ResizeRenderer):
    """
    Letterboxes an image smaller than a requested size by
    centering it on a larger canvas. Canvas optionally uses
    a hex background color, defaulting to ``#FFFFFF``.
    """
    
    def __init__(self, width, height, bg_color='#FFFFFF',
                 *args, **kwargs):
        super(LetterboxRenderer, self).__init__(width,
                                                height,
                                                *args,
                                                **kwargs)
        # convert hex string to rgba quadruple
        bg_color = bg_color.strip('#')
        bg_hex = bg_color.decode('hex')
        self.bg_color = struct.unpack('BBB', bg_hex) + (0, )

    def _render(self, image):
        image = super(LetterboxRenderer, self)._render(image)
        src_w, src_h = image.size

        # place image on canvas and save
        canvas = Image.new('RGBA',
                           (self.width, self.height),
                           self.bg_color)
        paste_x = (self.width - src_w) / 2
        paste_y = (self.height - src_h) / 2
        canvas.paste(image, (paste_x, paste_y))
        
        return canvas
