from django import forms
from django.utils import timezone
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from pinax.blog.forms import AdminPostForm
from pinax.blog.models import Post, Revision
from pinax.blog.parsers.markdown_parser import parse as md_parse
from markdown_ckeditor.ckeditor import CKEditorWidget
from .models import Image, Comment

# Due to deprecation of django.forms.util in Django 1.9
try:
    from django.forms.utils import flatatt
except ImportError:
    from django.forms.util import flatatt

# Historical name of force_text(). Only available under Python 2.
try:
    from django.utils.encoding import force_unicode
except ImportError:
    def force_unicode(x):
        return(x)

class CreateForm(AdminPostForm):
    slug = None
    description = None
    content = forms.CharField(
        widget=CKEditorWidget()
    )

    def __init__(self, *args, **kwargs):
        # we don't actually use the following fields, but pinax blog assumes its presence
        self.fields = {}
        self.fields["teaser"] = forms.CharField(widget=forms.Textarea())
        super(AdminPostForm, self).__init__(*args, **kwargs)
        self.fields.pop("teaser")

        post = self.instance

        # grab the latest revision of the Post instance
        latest_revision = post.latest()

        if latest_revision:
            # set initial data from the latest revision
            self.fields["content"].initial = latest_revision.content

    def save(self):
        post = super(AdminPostForm, self).save(commit=False)

        post.teaser_html = ''
        post.content_html = md_parse(self.cleaned_data["content"])
        post.updated = timezone.now()
        post.save()

        r = Revision()
        r.post = post
        r.title = post.title
        r.teaser = ''
        r.content = self.cleaned_data["content"]
        r.author = post.author
        r.updated = post.updated
        r.published = post.published
        r.save()

        return post


    class Meta:
        model = Post
        fields = ["title", "content"]

    class Media:
        js = ("spaces_blog/spaces_blog.js",
        )

class CreateImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image',]

ImageFormSet = forms.inlineformset_factory(
    Post, 
    Image, 
    fields=('image',), 
    can_delete=False, 
    extra=0)

ImageFormSetEmpty = forms.inlineformset_factory(
    Post, 
    Image, 
    fields=('image',), 
    can_delete=False, 
    extra=1)


class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        widget = forms.Textarea(attrs={'rows': 4}),
        required = False
    )

    class Meta:
        model = Comment
        fields = ('comment',)