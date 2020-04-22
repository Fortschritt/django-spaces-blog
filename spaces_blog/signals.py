from django.conf import settings
from django.utils.translation import ugettext_noop as _

def create_notice_types(sender, **kwargs):
    if "pinax.notifications" in settings.INSTALLED_APPS:
        from spaces_notifications.utils import register_notification
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