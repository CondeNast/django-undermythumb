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

    def test_thumbnails_update_on_save(self):
        author1 = Author.objects.create(image=self._get_image('author1.jpg'))
        self.assertEquals(author1.image, 'authors/author1.jpg')
        self.assertEquals(author1.image.thumbnails.small,
                          'authors/author1-small.png')
        author1.image = self._get_image('author1-1.jpg')
        author1.save()
        self.assertEquals(author1.image, 'authors/author1-1.jpg')
        self.assertEquals(author1.image.thumbnails.small,
                          'authors/author1-1-small.png')

    def test_thumbnail_override_no_source(self):
        """Ensure that an override field correctly mirrors an empty source.
        """
        author = Author.objects.create()
        self.assertEqual(author.image.thumbnails.small, None)
        self.assertEqual(author.small_image, None)
        self.assertEqual(author.image.thumbnails.small,
                         author.small_image)

    def test_thumbnail_mirroring(self):
        """Ensure that an empty override field uses the proper thumbnail.
        """
        author = Author.objects.create(image=self._get_image('author.jpg'))
        self.assertEqual(author.small_image.url,
                         author.image.thumbnails.small.url)

    def test_thumbnail_mirroring_foreign_fields(self):
        """Ensure that fallback paths work across non-m2m relationships.
        """
        author = Author.objects.create(image=self._get_image('author.jpg'))
        book = Book.objects.create(author=author,
                                   image=self._get_image('book.jpg'))

        self.assertEqual(book.author_image.url,
                         author.image.thumbnails.small.url)
        
    def test_thumbnail_override_image(self):
        """Ensure that an overridden thumbnail returns the custom image
        at the right url.
        """

        # create an author, override thumbnail
        author = Author.objects.create(image=self._get_image('author.jpg'),
                                       small_image=self._get_image('author_alt.jpg'))

        # quick check 
        self.assertNotEqual(author.small_image.url,
                            author.image.thumbnails.small.url)

        # check auto-generated thumbnail url
        self.assertEqual(author.image.thumbnails.small.url,
                         'authors/author-small.png')

        # check override thumbnail url
        self.assertEqual(author.small_image.url,
                         'authors/author_alt.jpg')

        os.remove(author.image.path)
        os.remove(author.small_image.path)
        
