from django.apps import AppConfig
from django.db.models.signals import post_migrate
from collab.util import db_table_exists

from spaces_blog.signals import create_notice_types

class SpacesBlogConfig(AppConfig):
    name = 'spaces_blog'

    def ready(self):
        # sections are mandatory in pinax-blog, but we don't need one
        from pinax.blog.models import Blog, Section
        if db_table_exists('blog_section'):
            section = Section.objects.get_or_create(name='Blog', slug='blog')
        if db_table_exists('blog_blog'):
            blog = Blog.objects.get_or_create()

        # activate activity streams for BlogPost
        from actstream import registry
        from .models import BlogPost
        registry.register(BlogPost)

        # register a custom notification
        """
        from spaces_notifications.utils import register_notification
        from django.utils.translation import ugettext_noop as _
        register_notification(
            'spaces_blog_create',
            _('A new blog post has been published.'),
            _('A new blog post has been published.')
        )
        register_notification(
            'spaces_blog_modify',
            _('A blog post has been modified.'),
            _('A blog post has been modified.')
        )
        register_notification(
            'spaces_blog_comment',
            _('A blog post has been commented on.'),
            _('A blog post has been commented on.')
        )
        """
        post_migrate.connect(create_notice_types, sender=self)