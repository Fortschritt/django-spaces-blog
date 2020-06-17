from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from pinax.blog.models import Post
from collab.util import is_owner_or_admin


def post_owner_or_admin_required(func):
    """
    method decorator raising 403 if user is neither the owner of the file
    nor a space administrator or manager.
    """
    def _decorator(self, *args, **kwargs):
        if 'post_slug' in kwargs.keys():
            slug = kwargs['post_slug']
        else:
            slug = None
        obj = get_object_or_404(Post, slug=slug)
        if self.user and self.user.is_authenticated:
            is_allowed = is_owner_or_admin(
                self.user, 
                obj.author,
                self.SPACE
            )
            if is_allowed:
                return func(self, *args, **kwargs)
        raise PermissionDenied
    return _decorator