Fields
======

The following fields (and concepts) are offered by ``undermythumb``.

Available fields
----------------

``undermythumb`` comes with two fields, each with specific use cases.

``ImageWithThumbnailsField``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The name says it all -- this field is used to accept an image and cut thumbnails.
Thumbnails are stored using whatever storage is available to the field.

Defining thumbnails
*******************

Thumbnails are defined as a tuple of tuples passed as ``thumbnails`` to the field.

Each tuple is defined as ``(thumbnail key, renderer instance)``. The thumbnail key
becomes the thumbnail's key when using the field's ``thumbnails`` attribute to display a thumbnail, 
and part of the filename generated on creation.

Example: ::

    artwork = ImageWithThumbnailsField(    
        thumbnails = (('related_content', CropRenderer(150, 150)), ),
        upload_to='artwork/',
    )

In the example above, ``artwork`` has one thumbnail: ``related_content``.

In a template (or Python code), you can access ``related_content`` via ``thumbnails``: ::

    {# assuming 'object' is an instance of your model #}
    {{ object.artwork.thumbnails.related_content.url }}

.. note:: For a complete list of renderers, see: :ref:`renderers`.

``ImageFallbackField``
~~~~~~~~~~~~~~~~~~~~~~

This field is only a subclass of Django's ``ImageField``
with the ability to use images or thumbnails from another field.

This field came out of the need to offer a way to *optionally* 
override another field's thumbnail. To fall back to another field or thumbnail's value, 
simply define a dotted path to another model attribute. Using the example, above: ::

    related_content_image = ImageFallbackField(
        fallback_path='artwork.thumbnails.related_content',
        upload_to='artwork/'
    )

Since this is at its core an ``ImageField``, using in a template is as simple as: ::

    {# assuming 'object' is an instance of your model #}
    {{ object.related_content_image.url }}

But, here's what makes it special -- as defined, this field will 
do one of two things when accessed:

1. If the field **has a value** (a file has been uploaded), it will return that value.
2. If the field is **empty**, it will return the thumbnail from 
   its fallback path, ``artwork.thumbnails.related_content``.

