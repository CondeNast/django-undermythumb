import datetime
import os

from django.db.models import signals
from django.db.models.fields.files import ImageField, ImageFieldFile
from django.utils.encoding import force_unicode, smart_str


class ThumbnailFieldFile(ImageFieldFile):

    def __init__(self, key, renderer, *args, **kwargs):
        self.key = key
        self.renderer = renderer
        super(ThumbnailFieldFile, self).__init__(*args, **kwargs)
        self.storage = self.field.thumbnails_storage

    def save(self):
        assert False, "Can save this."


class Thumbnails(object):

    def __init__(self, field_file):
        self._thumbnail_keys = set()

        field = field_file.field
        instance = field_file.instance

        for options in field.thumbnails:
            try:
                key, renderer, filename = options
            except ValueError:
                key, renderer = options
                filename = os.path.basename(field_file.name)
            ext = '.%s' % renderer.format
            name = field.generate_thumbnail_filename(instance=instance,
                                                     filename=filename,
                                                     key=key,
                                                     ext=ext)
            thumbnail = ThumbnailFieldFile(key, renderer, instance,
                                           field, name)
            self._thumbnail_keys.add(key)
            setattr(self, key, thumbnail)

    def __iter__(self):
        for key, value in self.__dict__.iteritems():
            if key in self._thumbnail_keys:
                yield value


class ImageWithThumbnailsFieldFile(ImageFieldFile):

    def __init__(self, *args, **kwargs):
        super(ImageWithThumbnailsFieldFile, self).__init__(*args, **kwargs)
        setattr(self, 'thumbnails', Thumbnails(self))

    def save(self, name, content, save=True):
        super(ImageWithThumbnailsFieldFile, self).save(name, content, save)

        for thumbnail in self.thumbnails:
            rendered = thumbnail.renderer.generate(content)
            self.field.thumbnails_storage.save(thumbnail.name, rendered)


class ImageWithThumbnailsField(ImageField):
    attr_class = ImageWithThumbnailsFieldFile

    def __init__(self, thumbnails=None, thumbnails_upload_to=None,
            thumbnails_storage=None, *args, **kwargs):
        super(ImageWithThumbnailsField, self).__init__(*args, **kwargs)
        self.thumbnails = thumbnails or []
        self.thumbnails_storage = thumbnails_storage or self.storage
        self.thumbnails_upload_to = thumbnails_upload_to or self.upload_to

        if callable(self.thumbnails_upload_to):
            self.generate_thumbnail_filename = self.thumbnails_upload_to

    def get_thumbnail_directory_name(self):
        now = datetime.datetime.now()
        dirname = smart_str(self.thumbnails_upload_to)
        dirpath = force_unicode(now.strftime(dirname))
        return os.path.normpath(dirpath)

    def get_thumbnail_filename(self, filename, key, ext):
        basename, _ext = os.path.splitext(filename)
        name = self.thumbnails_storage.get_valid_name(basename)
        return '%s-%s%s' % (name, key, ext)

    def generate_thumbnail_filename(self, instance, filename, key, ext):
        dirname = self.get_thumbnail_directory_name()
        filename = self.get_thumbnail_filename(filename, key, ext)
        return os.path.join(dirname, filename)
