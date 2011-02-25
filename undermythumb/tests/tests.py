import os
import shutil
import uuid

from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.files.images import ImageFile
from django.test import TestCase

from PIL import Image

from undermythumb.fields import ImageWithThumbnailsField
from undermythumb.renderers import BaseRenderer, CropRenderer, \
     ResizeRenderer, LetterboxRenderer
from undermythumb.tests.models import Car, Book, Author


class AutoThumbsTestCase(TestCase):

    def setUp(self):
        root = os.path.dirname(__file__)
        self.tmpname = os.path.join(root, '_image.jpg')
        try:
            os.mkdir(settings.TEST_MEDIA_ROOT)
            os.mkdir(settings.TEST_MEDIA_CUSTOM_ROOT)
        except OSError:
            pass

    def tearDown(self):
        shutil.rmtree(settings.TEST_MEDIA_ROOT)
        shutil.rmtree(settings.TEST_MEDIA_CUSTOM_ROOT)

    def _get_image(self, name=None):
        return ImageFile(open(self.tmpname), name=name)

    def test_base_renderer(self):
        renderer = BaseRenderer()

        tmp = renderer._create_tmp_image(self._get_image())
        self.assertTrue(isinstance(tmp, Image.Image))

        img = renderer._create_content_file(tmp)
        self.assertTrue(isinstance(img, ContentFile))

        self.assertRaises(NotImplementedError, renderer.generate,
                          self._get_image())

    def test_crop_renderer(self):
        renderer = CropRenderer(50, 50)
        content = renderer.generate(self._get_image())
        img = ImageFile(content)
        self.assertEqual((img.width, img.height), (50, 50))

        renderer = CropRenderer(50, 10)
        content = renderer.generate(self._get_image())
        img = ImageFile(content)
        self.assertEqual((img.width, img.height), (50, 10))

    def test_resize_renderer(self):
        renderer = ResizeRenderer(50, 10, upscale=True)
        content = renderer.generate(self._get_image())
        img = ImageFile(content)
        self.assertEqual((img.width, img.height), (50, 50))

        renderer = ResizeRenderer(50, 10, constrain=False)
        content = renderer.generate(self._get_image())
        img = ImageFile(content)
        self.assertEqual((img.width, img.height), (50, 10))

    def test_resize_renderer_upscaling(self):
        renderer = ResizeRenderer(500, 500, upscale=False)
        content = renderer.generate(self._get_image())
        img = ImageFile(content)
        self.assertEqual((img.width, img.height), (100, 100))

        renderer = ResizeRenderer(500, 500, upscale=True)
        content = renderer.generate(self._get_image())
        img = ImageFile(content)
        self.assertEqual((img.width, img.height), (500, 500))

    def test_letterbox_renderer(self):
        # TODO: needs a better test. this only checks that
        # the image is the correct size, and not that it's
        # been letterboxed properly. A proper letterboxing
        # test would check the border around each side.
        
        renderer = LetterboxRenderer(500, 500, bg_color='#000000',
                                     quality=100, upscale=False)
        content = renderer.generate(self._get_image())
        img = ImageFile(content)
        self.assertEqual((img.width, img.height), (500, 500))

    def test_on_static_upload_to(self):
        scion = Car.objects.create(image=self._get_image('scion.jpg'))

        self.assertEqual((scion.image.width, scion.image.height), (100, 100))
        self.assertEqual(scion.image.name,
                         os.path.join('original', 'scion.jpg'))

        self.assertEqual((scion.image.thumbnails.small.width,
                          scion.image.thumbnails.small.height), (25, 25))
        self.assertEqual(scion.image.thumbnails.small,
                         os.path.join('thumbs', 'scion-small.jpg'))

        self.assertEqual((scion.image.thumbnails.medium.width,
                          scion.image.thumbnails.medium.height), (50, 50))
        self.assertEqual(scion.image.thumbnails.medium,
                         os.path.join('thumbs', 'scion-medium.jpg'))

        self.assertEqual((scion.image.thumbnails.large.width,
                          scion.image.thumbnails.large.height), (75, 75))
        self.assertEqual(scion.image.thumbnails.large,
                         os.path.join('thumbs', 'scion-large.jpg'))

        matrix = Car.objects.create(image=self._get_image('matrix.jpg'))

        self.assertEqual(matrix.image.name,
                         os.path.join('original', 'matrix.jpg'))

        self.assertEqual(matrix.image.thumbnails.small.name,
                         os.path.join('thumbs', 'matrix-small.jpg'))

        self.assertEqual(matrix.image.thumbnails.medium,
                         os.path.join('thumbs', 'matrix-medium.jpg'))

    def test_on_func_upload(self):
        book1_uuid = unicode(uuid.uuid4())
        book1 = Book(name=book1_uuid, image=self._get_image('book1.jpg'))
        book1.save()

        self.assertEqual(book1.image.name,
                         os.path.join(book1_uuid, 'original.jpg'))

        self.assertEqual(book1.image.thumbnails.small.name,
                         os.path.join(book1_uuid, 'small.jpg'))

        self.assertEqual(book1.image.thumbnails.medium.name,
                         os.path.join(book1_uuid, 'medium.jpg'))

        self.assertEqual(book1.image.thumbnails.large.name,
                         os.path.join(book1_uuid, 'large.jpg'))

        book2_uuid = unicode(uuid.uuid4())
        book2 = Book(name=book2_uuid, image=self._get_image('book2.jpg'))
        book2.save()

        self.assertEqual(book2.image.name,
                         os.path.join(book2_uuid, 'original.jpg'))

        self.assertEqual(book2.image.thumbnails.small.name,
                         os.path.join(book2_uuid, 'small.jpg'))

        self.assertEqual(book2.image.thumbnails.medium.name,
                         os.path.join(book2_uuid, 'medium.jpg'))

        self.assertEqual(book2.image.thumbnails.large.name,
                         os.path.join(book2_uuid, 'large.jpg'))

    def test_custom_thumbnails_storage(self):
        author1 = Author.objects.create(image=self._get_image('author1.jpg'))
        self.assertTrue(settings.TEST_MEDIA_ROOT in author1.image.path)
        self.assertTrue(settings.TEST_MEDIA_CUSTOM_ROOT in
            author1.image.thumbnails.small.path)

    def test_thumbnail_override_empty(self):
        """Ensure that an empty override field uses the proper thumbnail.
        """
        author1 = Author.objects.create(image=self._get_image('author1.jpg'))
        self.assertEqual(author1.small_image.url,
                         author1.image.thumbnails.small.url)

    def test_thumbnail_override_image(self):
        """Ensure that an overridden thumbnail returns the custom image.
        """
        author1 = Author.objects.create(image=self._get_image('author1.jpg'),
                                        small_image=self._get_image('author1_alt.jpg'))
        self.assertNotEqual(author1.small_image.url,
                            author1.image.thumbnails.small.url)
