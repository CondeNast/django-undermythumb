from undermythumb.files import ThumbnailFieldFile


class ThumbnailSet(object):

    def __init__(self, field_file):
        self.file = field_file
        self.field = self.file.field
        self.instance = self.file.instance

        self._cache = {}
        self._populate()

    def _populate(self):
        if not self._cache and self.file.name and self.instance.id:
            for options in self.field.thumbnails:
                try:
                    attname, renderer, key = options
                except ValueError:
                    attname, renderer = options
                    key = attname
                    ext = '.%s' % renderer.format

                    name = self.field.get_thumbnail_filename(
                        instance=self.instance,
                        original=self.file,
                        key=key,
                        ext=ext)

                    thumbnail = ThumbnailFieldFile(
                        attname,
                        renderer,
                        self.instance,
                        self.field,
                        name)

                    self._cache[attname] = thumbnail

    def clear_cache(self):
        self._cache = {}

    def __getattr__(self, name):
        try:
            return self._cache[name]
        except KeyError:
            return None

    def __iter__(self):
        self._populate()
        for attname, value in self._cache.iteritems():
            yield value
