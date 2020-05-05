import time
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from pinax.blog.models import Post
from spaces.models import Space,SpacePluginRegistry, SpacePlugin, SpaceModel
from private_media.storages import PrivateMediaStorage

def file_upload_path(instance, filename):
    space = instance.post.blogpost.blog.space.slug
    time_string = time.strftime('%Y/%m/%d')
    return 'spaces_blog/%s/%s/%s' % (space, time_string, filename)


class Image(models.Model):
    """
    Image class to replace pinax.blog.models.Image as that stores images publicly.
    """
    image = models.FileField(upload_to=file_upload_path, storage=PrivateMediaStorage(), verbose_name=_('Image'))
    post = models.OneToOneField(Post, on_delete=models.CASCADE)


class SpacesBlog(SpacePlugin):
    """
    Blog plugin for django-spaces. Intended for internal use of Space members.
    This only provides general metadata per space. Content is available in 
    BlogPost instances.
    """
    # active field (boolean) inherited from SpacePlugin
    # space field (foreignkey) inherited from SpacePlugin
    reverse_url = 'spaces_blog:index'


class BlogPost(SpaceModel):
    post = models.OneToOneField(Post, on_delete=models.CASCADE)
    blog = models.ForeignKey(SpacesBlog, on_delete=models.CASCADE)


    spaceplugin_field_name = "blog"

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')

    def __str__(self):
        return self.post.__str__()

    def get_absolute_url(self):
        return reverse('spaces_blog:detail', args=(self.post.slug,))

    def deleted(self):
        return self.post.state == Post.STATE_CHOICES[0][0] # = unpublished

class BlogPlugin(SpacePluginRegistry):
    """
    Provide a blog plugin for Spaces. This makes the SpacesBlog class visible to
    the plugin system.
    """
    name = 'spaces_blog'
    title = _('Blog')
    plugin_model = SpacesBlog
    searchable_fields = (BlogPost, ('post__title','post__markup'))


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name=_('Comment'))
    published = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


# pinax.blog unfortunately doesn't register its field names for translation,
# so we create this dummy dict for 'makemessages' to find and process.
strings_to_translate = {
    'foo': _('Content')
}