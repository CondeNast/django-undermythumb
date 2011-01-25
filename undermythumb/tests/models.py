import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from undermythumb.fields import ImageWithThumbnailsField
from undermythumb.renderers import CropRenderer


class Car(models.Model):
    image = ImageWithThumbnailsField(
        upload_to='original',
        storage=FileSystemStorage(settings.TEST_MEDIA_ROOT),
        thumbnails=(
            ('small', CropRenderer(25, 25)),
            ('medium', CropRenderer(50, 50)),
            ('large', CropRenderer(75, 75)),
        ),
    )


def original_upload_to(instance, filename):
    base, ext = os.path.splitext(filename)
    return os.path.join(instance.name, 'original%s' % ext)


def thumbnails_upload_to(instance, original, key, ext):
    return os.path.join(instance.name, '%s%s' % (key, ext))


class Book(models.Model):
    name = models.CharField(max_length=32)
    image = ImageWithThumbnailsField(
        upload_to=original_upload_to,
        storage=FileSystemStorage(settings.TEST_MEDIA_ROOT),
        thumbnails_upload_to=thumbnails_upload_to,
        thumbnails=(
            ('small', CropRenderer(25, 25)),
            ('medium', CropRenderer(50, 50)),
            ('large', CropRenderer(75, 75)),
        ),
    )


class Author(models.Model):
    image = ImageWithThumbnailsField(
        upload_to='authors',
        storage=FileSystemStorage(settings.TEST_MEDIA_ROOT),
        thumbnails_storage=FileSystemStorage(settings.TEST_MEDIA_CUSTOM_ROOT),
        thumbnails=(
            ('small', CropRenderer(25, 25, format='png')),
            ('medium', CropRenderer(50, 50)),
            ('large', CropRenderer(75, 75)),
        ),
    )
