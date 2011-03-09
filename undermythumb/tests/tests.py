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

    def test_thumbnails_available_with_empty_image(self):
        """Ensure that an empty image field still makes available
        the thumbnails accessor.
        """
        
        author = Author.objects.create()

        # author.image should be None
        self.assertEqual(author.image, None)
        self.assertEqual(author.image.thumbnails.small, None)

    def test_imagefallbackfield_fallback(self):
        """Ensure that an ImageFallbackField returns the correct fallback image.
        """

        author = Author.objects.create(image=self._get_image('author.jpg'))
        book = Book.objects.create(author=author)

        # check for correct image url from source field
        self.assertEqual(author.image.url, 'authors/author.jpg')
        self.assertNotEqual(author.small_image, None)

        # assert that the "small image" url mirrors the
        # small thumbnail from "image"
        self.assertEqual(author.small_image.url,
                         author.image.thumbnails.small.url)

        # assert that fallback paths work with FK relationships
        self.assertEqual(book.author_image.url, author.image.url)

    def test_imagefallbackfield_populated(self):
        """Ensure that an ImageFallbackField doesn't ignore it's own content.
        """

        author = Author.objects.create(image=self._get_image('author.jpg'))
        book = Book.objects.create(author=author,
                                   author_image=self._get_image('book_author.jpg'))

        # assert that the fallback field returns 'book_author.jpg'
        self.assertNotEqual(book.author_image.url, author.image.url)
        self.assertEqual(book.author_image.url,
                         'authors/book_author.jpg')

    def test_thumbnailfield_fallback(self):
        """Ensure that an ImageWithThumbnailsField falls back correctly.

        In this test case, 'book.alt_image' should fall back to
        'book.image' if empty.
        """

        book = Book.objects.create(image=self._get_image('book.jpg'))

        # 'book.alt_image.url' should match 'book.image.url'
        self.assertEqual(book.alt_image.url, book.image.url)

        # 'book.alt_image.thumbnails.small.url' should match
        # that of 'book.image...'
        self.assertEqual(book.alt_image.thumbnails.small.url,
                         book.image.thumbnails.small.url)
        
    def test_thumbnailfield_populated(self):
        """Ensure that a fallback-enabled ImageWithThumbnailsField returns it's own content.
        """

        book = Book.objects.create(name='Thinner',
                                   image=self._get_image('book.jpg'),
                                   alt_image=self._get_image('book_alt.jpg'))

        # 'alt_image' urls should not mirror 'image' urls
        self.assertEqual(book.alt_image.url, 'authors/book_alt.jpg')
        self.assertNotEqual(book.image.url, book.alt_image.url)

        # make sure thumbnails are properly stored, and not mirrored
        self.assertEqual(book.alt_image.thumbnails.small.url,
                         'authors/book_alt-small.jpg')
        self.assertNotEqual(book.alt_image.thumbnails.small.url,
                            book.image.thumbnails.small.url)

    def test_imagefallbackfield_depth(self):
        """Ensure that falling back will continue falling until something is hit.

        In this test case, 'book.alt_author_image' should fall back
        all the way to 'author.image'.
        """

        author = Author.objects.create(image=self._get_image('author.jpg'))
        book = Book.objects.create(author=author)

        self.assertEqual(book.alt_author_image.url,
                         author.image.url)
