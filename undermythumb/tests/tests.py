import os
import shutil

from django.core.files.images import ImageFile
from django.db import connection
from django.test import TestCase

from undermythumb.tests.models import BlogPost


root = os.path.dirname(__file__)
path = lambda *p: os.path.join(root, *p)


class UnderMyThumbTestSuite(TestCase):
    """Test the follow scenarios:

    1. Upload 'artwork' image, verify that ImageFallbackField fields are blank.
    2. Re-save uploaded artwork, verify that ImageFallbackField
       fields are blank.
    3. Upload image into ImageFallbackField, ensure correct filename.
    4. Clear image from ImageFallbackField, ensure db value is None,
       ensure field returns correct fallback image.
    """

    def setUp(self):
        self.cursor = connection.cursor()

    def tearDown(self):
        shutil.rmtree(os.path.realpath('./artwork'))

    def get_test_image(self):
        return ImageFile(open(path('statler_waldorf.jpg')))

    def get_test_thumbnail(self):
        return ImageFile(open(path('sweetums_lecture.jpg')))

    def get_db_thumbnails(self, db_table, instance_id, *thumbnail_names):
        self.cursor.execute('select homepage_image from %s where id=%s' %
                            (db_table, instance_id))
        return self.cursor.fetchone()

    def test_simple_fallback(self):
        """Ensures fallbacks from one field to another work,
        and that no fallback values are persisted.
        """

        post = BlogPost.objects.create(title='Test Post',
                                       artwork=self.get_test_image())
        post_id = post.id
        post = BlogPost.objects.get(id=post_id)

        # ensure the file was uploaded correctly
        self.assertEqual(post.artwork.url, 'artwork/b3d23ba4.jpg')

        # ensure that "homepage_image" falls back to the right thumbnail
        self.assertEqual(post.homepage_image.url,
                         post.artwork.thumbnails.homepage_image.url)

        # ensure that no value was saved to "homepage_image"
        self.assertEqual(self.get_db_thumbnails(BlogPost._meta.db_table,
                                                post_id,
                                                'homepage_image'),
                         (None, ))

    def test_uploading_image_to_fallback_field(self):
        """Ensures fallback field uploads are properly persisted.
        """

        post = BlogPost.objects.create(title='Test Post',
                                       artwork=self.get_test_image())

        # save post with a thumbnail
        post.homepage_image = self.get_test_thumbnail()
        post.save()

        # reload post
        post_id = post.id
        post = BlogPost.objects.get(id=post_id)

        # ensure "artwork" field is unchanged
        self.assertEqual(post.artwork.url, 'artwork/b3d23ba4.jpg')

        # ensure upload was successful
        self.assertEqual(post.homepage_image.url,
                         'artwork/sweetums_lecture.jpg')

        # ensure thumbnail value as persisted properly
        self.assertEqual(self.get_db_thumbnails(BlogPost._meta.db_table,
                                                post_id,
                                                'homepage_image'),
                         ('artwork/sweetums_lecture.jpg', ))

    def test_clearing_image_from_fallback_field(self):
        """Ensures that clearing an ImageFallbackField image leaves
        the db field empty, and rolls back properly.
        """

        post = BlogPost.objects.create(
            title='Test Post',
            artwork=self.get_test_image(),
            homepage_image=self.get_test_thumbnail())
        post.save()

        # load post
        post_id = post.id
        post = BlogPost.objects.get(id=post_id)

        # remove "homepage_image" from the post
        post.homepage_image = None
        post.save()

        # assert that this change has been persisted
        self.assertEqual(self.get_db_thumbnails(BlogPost._meta.db_table,
                                                post_id,
                                                'homepage_image'),
                         (None, ))

        # assert that the correct thumbnail is generated
        self.assertEqual(post.homepage_image.url,
                         post.artwork.thumbnails.homepage_image.url)
