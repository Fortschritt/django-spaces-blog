from django.conf.urls import url
from spaces.urls import space_patterns
from .views import Create, Index, Detail, Edit, NotReallyDelete, History, CreateComment

app_name = 'spaces_blog'
urlpatterns = (

    url(r'^blog/$', Index.as_view(), name='index'),
    url(r'^blog/create/$', Create.as_view(), name='create'),
    url(r"^blog/(?P<post_slug>[-\w]+)/edit/$", Edit.as_view(), name="edit"),
    url(r"^blog/(?P<post_slug>[-\w]+)/delete/$", NotReallyDelete.as_view(), name="delete"),
    url(r"^blog/(?P<post_slug>[-\w]+)/create_comment/$", CreateComment.as_view(), name="create_comment"),
    url(r"^blog/(?P<post_slug>[-\w]+)/history/(?P<revision_id>\d+)$", History.as_view(), name="history"),
    url(r"^blog/(?P<post_slug>[-\w]+)/$", Detail.as_view(), name="detail"),
)