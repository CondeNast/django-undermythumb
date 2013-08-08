from hashlib import sha1
import os

from django.db.models.fields.files import ImageFieldFile


__all__ = ('ThumbnailFieldFile', 'ImageWithThumbnailsFieldFile')


class ThumbnailSet(object):

    def __init__(self, field_file):
        self.file = field_file
        self.field = self.file.field
        self.instance = self.file.instance

        self._cache = {}

    def _populate(self):
        if not self._cache and self.file.name and self.instance:
            for options in self.field.thumbnails:
                try:
                    attname, renderer, key = options
                except ValueError:
                    attname, renderer = options
                    key = attname
                    ext = '.%s' % renderer.format

                name = self.field.get_thumbnail_filename(
                    instance=self.instance,
                    original_file=self.file,
                    thumbnail_name=key,
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
        self._populate()

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
        # set file name to first 8 chars of hash of contents
        _, ext = os.path.splitext(name)
        file_hash = sha1(content.read()).hexdigest()[:8]
        name = file_hash + ext

        # save source file
        super(ImageWithThumbnailsFieldFile, self).save(name, content, save)

        self.thumbnails.clear_cache()

        for thumbnail in self.thumbnails:
            rendered = thumbnail.renderer.generate(content)
            self.field.storage.save(thumbnail.name, rendered)

        if save:
            self.instance.save()
