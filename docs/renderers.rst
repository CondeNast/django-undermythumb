Renderers
=========

.. _renderers:

List of available renderers
---------------------------

.. _resize-renderer:

``ResizeRenderer``
~~~~~~~~~~~~~~~~~~

Resizes an image, maintaining the image's aspect ratio.

Example: ::

    # resize an image to 150px wide, 84px tall
    ResizeRenderer(150, 84)

If you would like to ignore the aspect ratio, pass in ``constrain=False``.

``CropRenderer``
~~~~~~~~~~~~~~~~~~

Resizes an image, crops to an area.

Example: ::

    # resize an image to 150 on it's largest side,
    # and select a 150x150 square from the center.x
    CropRenderer(150, 150)

Internally, ``CropRenderer`` uses PIL's ``ImageOps.fit`` to
scale and select the image.

``LetterboxRenderer``
~~~~~~~~~~~~~~~~~~~~~

Resizes an image using the :ref:`resize-renderer` and centers over a 
given background color. Background colors are provided as hex values.

Example: ::

    # resize an image, place on black background
    LetterboxRenderer(150, 150, bg_color='#000000')

Creating your own renderers
---------------------------

Better documentation forthcoming. In the meantime, subclass 
``undermythumb.renderers.BaseRenderer`` and implement custom image
logic in a method called ``_render``.
