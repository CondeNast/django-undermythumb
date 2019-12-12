🚨 django-undermythumb is no longer an active project. 🚨
=============

---------

Under My Thumb
==============

The Django thumbnail generator with a heart of stone.

`Read the docs <http://django-undermythumb.readthedocs.org/en/latest/>`_!

Changelog
---------

0.3.1
~~~~~

Updated code for Django 1.7 support. Added `deconstruct()` and `__eq__()`
definitions for serialization support with the new migrations feature.

0.3
~~~

**Important Change**

Filenames are now written with a fingerprint, similar to how ``django-katamari``
fingers its assets.

0.2.2
~~~~~

Added initial project documentation.

- Sphinx-written docs now found in ``/docs`` dir.
- Cleaned up grammatical and formatting mistakes in ``renderers`` module.

0.2.1
~~~~~

Mainteance update.

- Abtracted thumbnail collection object and field files into own modules.
- Added ``*~`` to ``.gitignore``.

0.2
~~~

Improved path traversal and type checking for undermythumb fields.

- ``ImageFallbackField`` performs a better type check to determine
  if its content is a real field upload or the result of a fallback.
- ``BaseRenderer`` now uses a default quality of "100". "75" is ridiculously low.
- Abstracted fallback logic into separate function
- Scrapped current tests in favor of a simple approach. more tests coming soon.
- Cleaned up test runner, models, and settings

0.1.1
~~~~~

- Thumbnail cache now populated only when instances have ids.
- ``FallbackFieldDescriptor`` now ensures that thumbnails it persists
  are actually what it wants to persist.
- More documentation around thicker logic.


0.1.0
~~~~~

- Initial release.
