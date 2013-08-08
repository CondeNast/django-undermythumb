INSTALLED_APPS = (
    'undermythumb',
    'undermythumb.tests',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3'
    }
}

TEST_MEDIA_ROOT = '/tmp/thumbnails-test/'
TEST_MEDIA_CUSTOM_ROOT = '/tmp/thumbnails-test-custom/'

DEFAULT_FILE_STORAGE = 'undermythumb.tests.storage.FileSystemOverwriteStorage'

SECRET_KEY = 'SOMEMODERATELYLONGSECRETKEY'
