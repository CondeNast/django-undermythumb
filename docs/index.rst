Introduction
============

``undermythumb`` is a simple thumbnailing library for Django with a twist:
its fields can optionally fall back to thumbnails from another field.

This app is currently used around `Pitchfork <http://pitchfork.com/>`_,
and is under active development.

Issues can be reported `here <https://github.com/pitchfork/django-undermythumb/issues>`_.

Why another thumbnailer?
------------------------

At `Pitchfork <http://pitchfork.com>`_, we needed a simple way to cut thumbnails, 
place them on the field's storage, do without fancy renderers we'd never use, 
and give editors a *simple* way to override auto-generated thumbnails
without littering our templates with unnecessary logic.

Basic example
-------------

In ``models.py``: ::

    from django.db import models

    from undermythumb.fields import (ImageWithThumbnailsField, 
                                     ImageFallbackField)
    from undermythumb.renderers import CropRenderer


    class BlogPost(models.Model):
        title = models.CharField(max_length=100)

        # an image with thumbnails
        artwork = ImageWithThumbnailsField(
             max_length=255,
             upload_to='artwork/',
             thumbnails=(('homepage_image', CropRenderer(300, 150)),
                         ('pagination_image', CropRenderer(150, 75))),
             help_text='Blog post header artwork.')
             
        # an override field, capable of rolling up a dotted path
        # if the field is empty.
        # ``fallback_path`` should point to something that returns an ``ImageFieldFile``,
        # or anything that has an ``url`` attribute, and displays an image.
        #
        # under the hood, this is just an ImageField.
        homepage_image = ImageFallbackField(
            fallback_path='artwork.thumbnails.homepage_image',
            upload_to='artwork/',
            help_text='Optional override for "homepage_image" thumbnail.')

        def __unicode__(self):
            return self.title


In a template, where ``object`` is an instance of ``BlogPost``: ::

    <!-- does the job: auto-generated thumbnail from "artwork" -->
    <img src="{{ object.artwork.thumbnails.homepage_image.url }}" />

    <!-- smarter: value of "homepage_image", or, if empty, value of "artwork.thumbnails.homepage_image" -->
    <img src="{{ object.homepage_image.url }}" />

Falling back? What?
-------------------

Sometimes system generated thumbnails are ugly, or need to be overridden. 
In this case, offering an override field allows designers and editors a way to
control the thumbnail used across your site.

Sometimes, default thumbnails are perfect, and no additional work is required.

The easiest way to account for both scenarios is to have a single field
that allows an optional override, and can fall back to another image if
no override is needed.

This way,

- Content editors need only cut thumbnails when what the system's generated 
- Developers need only reference one thumbnail field in templates and code

Documentation
=============

.. toctree::
   :maxdepth: 2

   installation
   fields
   renderers
   

