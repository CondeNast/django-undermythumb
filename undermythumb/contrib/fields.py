from django.db import models

from undermythumb.fields import ImageWithThumbnailsField, ImageFallbackField


class PostSaveImageField(ImageWithThumbnailsField):

    def __init__(self, *args, **kwargs):
        kwargs.update(blank=True, null=True)
        super(PostSaveImageField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(PostSaveImageField, self).contribute_to_class(cls, name)
        models.signals.post_save.connect(self.save_file, sender=cls)

    def save_file(self, sender, instance, created, **kwargs):
        img_file = super(PostSaveImageField, self).pre_save(instance, created)

        if img_file:
            (instance.__class__._default_manager
             .filter(pk=instance.pk).update(**{self.attname: img_file}))

    def pre_save(self, *args, **kwargs):
        return ''


class PostSaveImageFallbackField(ImageFallbackField):

    def __init__(self, *args, **kwargs):
        kwargs.update(blank=True, null=True)
        super(PostSaveImageFallbackField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(PostSaveImageFallbackField, self).contribute_to_class(cls, name)
        models.signals.post_save.connect(self.save_file, sender=cls)

    def save_file(self, sender, instance, created, **kwargs):
        img_file = super(PostSaveImageFallbackField, self).pre_save(instance, created)

        if img_file:
            (instance.__class__._default_manager
             .filter(pk=instance.pk).update(**{self.attname: img_file}))

    def pre_save(self, *args, **kwargs):
        return ''
