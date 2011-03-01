import datetime
import os

from django.core.exceptions import ImproperlyConfigured
from django.db.models import signals
from django.db.models.fields.files import ImageField, ImageFieldFile, \
     ImageFileDescriptor
from django.utils.encoding import force_unicode, smart_str


class ThumbnailFieldFile(ImageFieldFile):

    def __init__(self, attname, renderer, *args, **kwargs):
        self.attname = attname
        self.renderer = renderer
        super(ThumbnailFieldFile, self).__init__(*args, **kwargs)
        self.storage = self.field.thumbnails_storage

    def save(self):
        raise NotImplemented("Can't save thumbnails directly.")


class Thumbnails(object):

    def __init__(self, field_file):
        self.file = field_file
        self.field = self.file.field
        self.instance = self.file.instance

        self._cache = {}
        self._populate()

    def _populate(self):
        if not self._cache and self.file.name:
            for options in self.field.thumbnails:
                try:
                    attname, renderer, key = options
                except ValueError:
                    attname, renderer = options
                    key = attname
                ext = '.%s' % renderer.format
                name = self.field.generate_thumbnail_filename(
                    instance=self.instance,
                    original=self.file,
                    key=key,
                    ext=ext,
                )
                thumbnail = ThumbnailFieldFile(
                    attname,
                    renderer,
                    self.instance,
                    self.field,
                    name,
                )
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


class ImageWithThumbnailsFieldFile(ImageFieldFile):

    def __init__(self, *args, **kwargs):
        super(ImageWithThumbnailsFieldFile, self).__init__(*args, **kwargs)
        self.thumbnails = Thumbnails(self)

    def save(self, name, content, save=True):
        super(ImageWithThumbnailsFieldFile, self).save(name, content, save)
        self.thumbnails.clear_cache()

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
        self.thumbnails_upload_to = thumbnails_upload_to

        if callable(self.thumbnails_upload_to):
            self.generate_thumbnail_filename = self.thumbnails_upload_to

    def generate_thumbnail_filename(self, instance, original, key, ext):
        base, _ext = os.path.splitext(force_unicode(original))
        return '%s-%s%s' % (base, key, ext)

    def south_field_triple(self):
        """Return a description of this field for South.
        """
        from south.modelsinspector import introspector

        field_class = "django.db.models.fields.files.ImageField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)


class ThumbnailOverrideFieldDescriptor(ImageFileDescriptor):

    def __get__(self, instance, owner):        
        # if this particular field is empty, return the url
        # of the mirror field's thumbnail
        mirror_field = self.field.mirror_field
        thumbnail_name = self.field.thumbnail_name

        value = super(ThumbnailOverrideFieldDescriptor, self).__get__(instance, owner)
        
        if value:
            return value

        mirror_attr = getattr(instance, mirror_field)
        thumbnail = getattr(mirror_attr.thumbnails, thumbnail_name)
        return thumbnail


class ThumbnailOverrideField(ImageField):
    """Provides a field for explicitly overriding thumbnails.
    """
    descriptor_class = ThumbnailOverrideFieldDescriptor

    def __init__(self, mirror_field, thumbnail_name, *args, **kwargs):
        kwargs.update(blank=True, null=True)
        super(ThumbnailOverrideField, self).__init__(*args, **kwargs)
        self.mirror_field = mirror_field
        self.thumbnail_name = thumbnail_name

    def south_field_triple(self):
        from south.modelinspector import introspector

        field_class = 'django.db.models.fields.files.ImageField'
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
