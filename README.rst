Under My Thumb
==============

The Django thumbnail generator with a heart of stone.

Usage
-----

Documentation forthcoming.

Changelog
---------

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
