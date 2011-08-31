import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from undermythumb.fields import ImageWithThumbnailsField, ImageFallbackField
from undermythumb.renderers import CropRenderer


class BlogPost(models.Model):
    title = models.CharField(max_length=100)

    # an image with thumbnails
    artwork = ImageWithThumbnailsField(max_length=255,
                                       upload_to='artwork/',
                                       thumbnails=(('homepage_image', CropRenderer(300, 150)),
                                                   ('pagination_image', CropRenderer(150, 75))))

    # an override field, capable of rolling up a path
    # when it has no value. useful for overriding 
    # auto-generated thumbnails. the fallback path
    # should point to an ImageFieldFile of some sort.
    #
    # under the hood, this is just an ImageField
    homepage_image = ImageFallbackField(fallback_path='artwork.thumbnails.homepage_image',
                                        upload_to='artwork/')

    def __unicode__(self):
        return self.title
                                       
