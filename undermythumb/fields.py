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


class FallbackFieldDescriptor(ImageFileDescriptor):

    def __get__(self, instance, owner):
        """Returns either the custom thumbnail provided directly
        to this field, or the thumbnail from the mirror field.
        """

        # if this particular field is empty, return the url
        # of the mirror field's thumbnail
        value = super(FallbackFieldDescriptor, self).__get__(instance,
                                                             owner)

        # monkey-patch the thumbnail image field file
        # to note whether or not this is a mirrored value or
        # a value given to this field
        if (type(value) in (ImageFieldFile,
                           ThumbnailFieldFile,
                           ImageWithThumbnailsFieldFile,
                           ImageFallbackField)
               and hasattr(value, 'url')):
            value._empty = False
            return value

        # this field has no value, and is mirroring
        # another field's thumbnail
        if self.field.fallback_path is None:
            if getattr(value, 'name'):
                value._empty = False
            else:
                value._empty = True
            return value

        if callable(self.field.fallback_path):
            # call fallback path function with instance
            fallback_path = self.field.fallback_path(instance)
        else:
            fallback_path = self.field.fallback_path

        path_bits = fallback_path.split('.')
        mirror_value = instance

        while path_bits:
            bit = path_bits.pop(0)
            try:
                bit = int(bit)
                mirror_value = mirror_value[bit]
            except ValueError:
                mirror_value = getattr(mirror_value, bit, None)
                if callable(mirror_value):
                    mirror_value = mirror_value()

        if mirror_value is None:
            return None

        mirror_value._empty = True      
        return mirror_value


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
    descriptor_class = FallbackFieldDescriptor

    def __init__(self, thumbnails=None, thumbnails_upload_to=None,
            thumbnails_storage=None, fallback_path=None, *args, **kwargs):
        super(ImageWithThumbnailsField, self).__init__(*args, **kwargs)
        self.thumbnails = thumbnails or []

        self.thumbnails_storage = thumbnails_storage or self.storage
        self.thumbnails_upload_to = thumbnails_upload_to

        if callable(self.thumbnails_upload_to):
            self.generate_thumbnail_filename = self.thumbnails_upload_to

        # fallback field
        self.fallback_path = fallback_path

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


class ImageFallbackField(ImageField):
    """A special ImageField that allows a user to optionally override
    a particular ImageWithThumbnailsField thumbnail, or transparently
    fall back to another thumbnail if no image is supplied.

    No special transformations are applied to uploaded images.
    """
    descriptor_class = FallbackFieldDescriptor

    def __init__(self, fallback_path, *args, **kwargs):
        kwargs.update(blank=True, null=True)
        super(ImageFallbackField, self).__init__(*args, **kwargs)
        self.fallback_path = fallback_path

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None or \
               (hasattr(value, '_empty') and value._empty is None):
            return None
        return unicode(value)

    def south_field_triple(self):
        """Return a description of this field for South.
        """
        from south.modelsinspector import introspector

        field_class = "django.db.models.fields.files.ImageField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
