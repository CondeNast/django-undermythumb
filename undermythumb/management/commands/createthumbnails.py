from optparse import make_option

from django.core.files.base import ContentFile
from django.db.models.fields import FieldDoesNotExist
from django.db.models.loading import get_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-c', '--contenttype',
            dest='content_type', action='store',
            help='Content type of thumbnail field.'),
        make_option('-f', '--fieldname',
            dest='field_name', action='store',
            help='Field name of thumbnail field.'),
        make_option('-s', '--size',
            dest='sizes', action='append'),
    )
    help = ("Selectively creates thumbnails for a model's "
            "image thumbnail field.")
    args = '[appname.modelname.fieldname.size  ...]'

    def handle(self, *args, **options):
        content_type_path = options.get('content_type', '')
        field_name = options.get('field_name', '')
        sizes = options.get('sizes', [])

        try:
            app_label, model_name = content_type_path.split('.')
            model = get_model(app_label, model_name)
            if model is None:
                raise ValueError
        except (ValueError, AttributeError):
            raise CommandError('Invalid content type %s' %  content_type_path)

        try:
            field = model._meta.get_field_by_name(field_name)[0]
        except FieldDoesNotExist:
            raise CommandError('Invalid field name %s' %  field_name)

        if sizes is None:
            raise CommandError('Must specify sizes, -s or --size')

        thumbnails = [t[0] for t in field.thumbnails for s in sizes]
        invalid_sizes = [s for s in sizes if s not in thumbnails]
        if invalid_sizes:
            raise CommandError('No thumbnails for sizes %r' %  invalid_sizes)

        objects = model._default_manager.only(field_name)
        for obj in objects:
            field_instance = getattr(obj, field_name)
            self.create_thumbnails(field_instance, sizes)

        self.stdout.write('Done.\n')


    def create_thumbnails(self, field_instance, sizes):
        thumbnails = [t for t in field_instance.thumbnails
                     if t.attname in sizes]

        if not thumbnails:
            return

        self.stdout.write('Reading %s ...\n' % field_instance.url)
        try:
            # Ignore bad files, this should log in the future.
            content = ContentFile(field_instance.read())
        except IOError:
            return
        for thumbnail in thumbnails:
            self.create_thumbnail(thumbnail, content)

    def create_thumbnail(self, thumbnail, content):
        self.stdout.write('Creating thumbnail %s ...\n' % thumbnail.url)
        rendered = thumbnail.renderer.generate(content)
        thumbnail.storage.save(thumbnail.name, rendered)
