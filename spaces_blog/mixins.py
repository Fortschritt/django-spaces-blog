from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from collab.mixins import SpacesMixin
from .decorators import post_owner_or_admin_required

class SpacesPostMixin(SpacesMixin):
    """ 
    Makes a single-object class based view Space aware:
        user has to have 'access_space' permission and 
        object has to live in current Space.
    """

    def get_object(self):
        obj = super(SpacesPostMixin, self).get_object()
        if not obj.blogpost.blog.space == self.request.SPACE:
            raise Http404(_('Entry does not exist.'))
        return obj

class PostPermissionMixin(SpacesPostMixin):
    """
    Deny access if user doesn't have sufficient permissions for
    editing blog posts.
    """

    @method_decorator(post_owner_or_admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super(PostPermissionMixin, self).dispatch(request, *args, **kwargs)

class SpacesListMixin(SpacesMixin):
    """ 
    Makes a class based view returning a queryset Space aware:
        user has to have 'access_space' permission and 
        object has to live in current Space.
    """

    def get_queryset(self):
        qs = super(SpacesListMixin, self).get_queryset()
        qs = qs.filter(blogpost__blog__space=self.request.SPACE)
        return qs
