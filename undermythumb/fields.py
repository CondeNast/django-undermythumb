import datetime
import os

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
        assert False, "Can't save this."


class Thumbnails(object):

    def __init__(self, field_file):
        self._thumbnail_attnames = set()

        field = field_file.field
        instance = field_file.instance

        for options in field.thumbnails:
            try:
                attname, renderer, key = options
            except ValueError:
                attname, renderer = options
                key = attname
            ext = '.%s' % renderer.format
            filename = os.path.basename(field_file.name)
            name = field.generate_thumbnail_filename(instance=instance,
                                                     filename=filename,
                                                     key=key,
                                                     ext=ext)
            thumbnail = ThumbnailFieldFile(attname, renderer, instance,
                                           field, name)
            self._thumbnail_attnames.add(attname)
            setattr(self, attname, thumbnail)

    def __iter__(self):
        for attname, value in self.__dict__.iteritems():
            if attname in self._thumbnail_attnames:
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

        current_value = instance.__dict__.get(self.field.name)
        if current_value:
            return current_value

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
    
