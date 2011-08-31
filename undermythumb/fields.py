import datetime
import os

from django.core.exceptions import ImproperlyConfigured
from django.db.models import signals
from django.db.models.fields.files import (ImageField, 
                                           ImageFieldFile,
                                           ImageFileDescriptor)
from django.utils.encoding import force_unicode, smart_str

from undermythumb.files import (ThumbnailFieldFile, 
                                ImageWithThumbnailsFieldFile)


def traverse_fallback_path(instance, fallback_path):
    """Ramble down a dotted path, looking for the end of the road.

    Break down the path, and traverse.
    If the path is ``article_header.thumbnails.list``,
    the order would be: ``article_header -> thumbnails -> list``.

    See also: http://en.wikipedia.org/wiki/The_Hunt_(The_Twilight_Zone)
    """

    value = instance
    path_bits = fallback_path.split('.')
    
    while path_bits:
        bit = path_bits.pop(0)

        try:
            bit = int(bit)
            value = value[bit]
        except IndexError:
            value = None
            break
        except ValueError:
            if isinstance(value, dict):
                value = value[bit]
            else:
                value = getattr(value, bit, None)
                if callable(value):
                    value = value()

    return value


class FallbackFieldDescriptor(ImageFileDescriptor):

    def __get__(self, instance, owner):
        """Returns a field's image. If no image is found, this descriptor
        inspects and traverses its field's ``fallback_path``, to find and return
        whatever lies at the end of the path.
        """

        # if this particular field is empty, return the url
        # of the mirror field's thumbnail
        value = super(FallbackFieldDescriptor, self).__get__(instance, owner)

        # if given a real value, mark as non-empty and return
        if (isinstance(value, (ImageFieldFile,
                               ThumbnailFieldFile,
                               ImageWithThumbnailsFieldFile,
                               ImageFallbackField))
            and hasattr(value, 'url')):
            value._empty = False
            return value
        
        # this value has no content. mark it as empty.
        value._empty = True

        # check to see if this image has a fallback path
        # no fallback path? check to see if the field
        # has a name, mark as empty/filled, and return.
        if self.field.fallback_path is None:
            if getattr(value, 'name'):
                value._empty = False
            return value

        # using the instance, trace through the fallback path
        mirror_value = traverse_fallback_path(instance, 
                                              self.field.fallback_path)

        if mirror_value is None:
            return None

        mirror_value._empty = True

        return mirror_value


class ImageWithThumbnailsField(ImageField):
    """An ``ImageField`` subclass, extended with zero to many thumbnails.
    """
    attr_class = ImageWithThumbnailsFieldFile
    descriptor_class = FallbackFieldDescriptor

    def __init__(self, thumbnails=None, fallback_path=None, *args, **kwargs):                 
        super(ImageWithThumbnailsField, self).__init__(*args, **kwargs)

        self.thumbnails = thumbnails or []
        self.fallback_path = fallback_path

    def get_thumbnail_filename(self, instance, original, key, ext):
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
    """A special ``ImageField`` subclass for defining an image field
    capable of falling back to the value of another field if empty.
    """
    descriptor_class = FallbackFieldDescriptor

    def __init__(self, fallback_path, *args, **kwargs):
        kwargs.update(blank=True, null=True)
        super(ImageFallbackField, self).__init__(*args, **kwargs)
        self.fallback_path = fallback_path

    def get_db_prep_value(self, value, connection, prepared=False):
        """Ensures that a given value comes from *this* field instance,
        is not empty, and is *only* an ``ImageFieldFile``.

        This logic prevents values from fallback path traversal from
        being persisted.
        """

        if not value:
            return None

        # we only want ImageFieldFile instances given to *this* field
        if ((type(value) == ImageFieldFile) and 
            (value.field == self) and
            (hasattr(value, '_empty') and not value._empty)):
            return unicode(value)
        
        return None

    def south_field_triple(self):
        """South field descriptor.
        """
        from south.modelsinspector import introspector

        field_class = "django.db.models.fields.files.ImageField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
