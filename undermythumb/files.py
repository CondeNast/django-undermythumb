from django.db.models.fields.files import ImageFieldFile


__all__ = ['ThumbnailFieldFile', 'ImageWithThumbnailsFieldFile']


class ThumbnailFieldFile(ImageFieldFile):

    def __init__(self, attname, renderer, *args, **kwargs):
        self.attname = attname
        self.renderer = renderer
        super(ThumbnailFieldFile, self).__init__(*args, **kwargs)

    def save(self):
        raise NotImplemented('Thumbnails cannot be saved directly.')


class ImageWithThumbnailsFieldFile(ImageFieldFile):
    """File container for an ``ImageWithThumbnailsField``.
    """

    def __init__(self, *args, **kwargs):
        super(ImageWithThumbnailsFieldFile, self).__init__(*args, **kwargs)
        self.thumbnails = ThumbnailSet(self)

    def save(self, name, content, save=True):
        """Save the original image, and its thumbnails.
        """
        super(ImageWithThumbnailsFieldFile, self).save(name, content, save)

        self.thumbnails.clear_cache()

        # iterate over thumbnail
        for thumbnail in self.thumbnails:
            rendered = thumbnail.renderer.generate(content)
            self.field.storage.save(thumbnail.name, rendered)
