from django.db.models.fields.files import ImageFieldFile


__all__ = ['ThumbnailFieldFile', 'ImageWithThumbnailsFieldFile']


class ThumbnailSet(object):

    def __init__(self, field_file):
        self.file = field_file
        self.field = self.file.field
        self.instance = self.file.instance

        self._cache = {}
        self._populate()

    def _populate(self):
        if not self._cache and self.file.name and self.instance.id:
            for options in self.field.thumbnails:
                try:
                    attname, renderer, key = options
                except ValueError:
                    attname, renderer = options
                    key = attname
                    ext = '.%s' % renderer.format

                    name = self.field.get_thumbnail_filename(
                        instance=self.instance, 
                        original=self.file,
                        key=key, 
                        ext=ext)                    

                    thumbnail = ThumbnailFieldFile(
                        attname,
                        renderer,
                        self.instance,
                        self.field,
                        name)
                    
                    self._cache[attname] = thumbnail

    def clear_cache(self):
        self._cache = {}

    def __getattr__(self, name):
        try:
            return self._cache[name]
        except KeyError:
            return None

    def __iter__(self):
        self._populate()
        for attname, value in self._cache.iteritems():
            yield value


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
