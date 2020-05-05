import itertools
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, UpdateView
from django.views.generic.edit import FormView, DeleteView, FormMixin
from actstream.signals import action as actstream_action
from pinax.blog.views import BlogIndexView
from pinax.blog.models import Blog,Post,Revision,Section
from pinax.blog.parsers.markdown_parser import parse as md_parse
from collab.decorators import permission_required_or_403
from collab.mixins import SpacesMixin
from spaces_notifications.mixins import NotificationMixin
from .decorators import post_owner_or_admin_required
from .forms import CreateForm, ImageFormSet, ImageFormSetEmpty, CommentForm
from .mixins import SpacesPostMixin, SpacesListMixin, PostPermissionMixin
from .models import BlogPlugin, BlogPost, SpacesBlog, Image, Comment


class ContextMixin(object):
    """
        Adds
        * the currently active plugin
    """
    def get_context_data(self, **kwargs):
        context = super(ContextMixin, self).get_context_data(**kwargs)
        context['plugin_selected'] = BlogPlugin.name
        return context

class Detail(NotificationMixin, ContextMixin, SpacesPostMixin, DetailView):
    template_name = "spaces_blog/detail.html"
    model = Post
    slug_url_kwarg = "post_slug"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(
            object=self.object, 
            current_section=self.object.section
        )
        return self.render_to_response(context)

    def get_queryset(self):
        queryset = super(Detail, self).get_queryset()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)
        revisions = self.object.revisions.all().order_by('-id') 
        context['revisions'] = revisions
        context['comment_form'] = CommentForm()
        context['comments'] = Comment.objects.filter(post=self.object).order_by('published')
        return context

class History(Detail): # SpacesPostMixin inherited
    template_name = "spaces_blog/history.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        revision = get_object_or_404(
            Revision, 
            post=self.object,
            id=kwargs['revision_id']
        )
        content_html = content_html = md_parse(revision.content)
        context = self.get_context_data(       
            object=self.object,                
            current_section=self.object.section,
            revision=revision,
            content=content_html
        )
        return self.render_to_response(context)

class Index(ContextMixin, SpacesListMixin, BlogIndexView):
    template_name = "spaces_blog/blog_list.html"

    def get_queryset(self):
        queryset = super(Index, self).get_queryset()
        queryset = queryset.exclude(state=Post.STATE_CHOICES[0][0]) # [0][0] == unpublished. 
        return queryset

class Create(NotificationMixin, ContextMixin, SpacesMixin, FormView):
    form_class = CreateForm
    template_name = "spaces_blog/create.html"
    notification_label = 'spaces_blog_create'
    success_message = _("Post was created successfully.")

    def form_valid(self, form):
        context = self.get_context_data()
        author = self.request.user
        teaser = ''
        description = ''
        title=form.cleaned_data['title']
        max_length = Post._meta.get_field('slug').max_length
        start_slug = slug = slugify(title)[:max_length]
        for x in itertools.count(1):
            if not Post.objects.filter(slug__iexact=slug).exists():
                break
            slug = '%s%d' % (start_slug[:max_length - len(str(x))], x)
        markup = 'markdown'
        content = form.cleaned_data['content']
        state = Post.STATE_CHOICES[-1][0] # = the index of "Published"
        section = Section.objects.all().first()
        self.new_post = Post.objects.create(
            blog=Blog.objects.all().first(),
            author=author,
            description=description,
            title=title,
            slug=slug,
            markup=markup,
            state=state,
            section=section,
            published = timezone.now(),
        )
        self.new_revision = Revision.objects.create(
            post=self.new_post,
            title=title,
            teaser=teaser,
            content=content,
            author=author,
            published = self.new_post.published,
        )
        blog = SpacesBlog.objects.get(space=self.request.SPACE)
        self.blogpost = BlogPost.objects.create(
            post=self.new_post,
            blog=blog
        )
        self.new_post.content_html = md_parse(self.new_revision.content)

        formset = context['formset']
        formset.instance = self.new_post
        if formset.is_valid():
            img_list = formset.save()
        self.new_post.save()
        messages.success(self.request, self.success_message)
        actstream_action.send(
            sender=self.request.user,
            verb=_("was created"),
            target=self.request.SPACE,
            action_object=self.blogpost
        )
        self.notification_object_title = self.blogpost
        self.notification_object_link = self.blogpost.get_absolute_url()
        super(Create, self).form_valid(form) # make sure mixin variants of form_valid are called
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(Create, self).get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ImageFormSet(self.request.POST, self.request.FILES)
        else:
            formset = ImageFormSetEmpty()
            context['formset'] = formset
        return context

    def get_success_url(self):
        return reverse_lazy('spaces_blog:detail', args=(self.new_post.slug,))


class Edit(NotificationMixin, ContextMixin, PostPermissionMixin, UpdateView):
    model = Post
    form_class = CreateForm
    template_name = "spaces_blog/edit.html"
    slug_url_kwarg = "post_slug"
    notification_label = 'spaces_blog_modify'
    success_message = _("Post was modified  successfully.")

    def form_valid(self, form):
        self.notification_object_title = self.object.blogpost
        self.notification_object_link = self.object.blogpost.get_absolute_url()
        super(Edit, self).form_valid(form)
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            img_list = formset.save()
        messages.success(self.request, self.success_message)
        actstream_action.send(
            sender=self.request.user,
            verb=_("was modified"),
            target=self.request.SPACE,
            action_object=self.object.blogpost
        )
        return self.get_success_url()

    def get_context_data(self, **kwargs):
        context = super(Edit, self).get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            formset = ImageFormSet(instance=self.object)
            context['formset'] = formset
        return context

    def get_success_url(self):
        return redirect('spaces_blog:detail', self.object.slug)


class NotReallyDelete(ContextMixin, PostPermissionMixin, SuccessMessageMixin, DeleteView):
    """
    Behaves the same as DeleteView, but instead of deleting it just 
    unpublishes the object.
    """
    model = Post
    success_message = _("Post was deleted successfully.")
    success_url = reverse_lazy('spaces_blog:index')
    slug_url_kwarg = "post_slug"
    template_name = "spaces_blog/post_confirm_delete.html"

    @method_decorator(permission_required_or_403('access_space'))
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.state = Post.STATE_CHOICES[0][0] # = unpublished
        self.object.save()
        messages.success(request, self.success_message)
        actstream_action.send(
                sender=request.user,
                verb=_("was deleted"),
                target=request.SPACE,
                action_object=self.get_object().blogpost
            )
        return redirect(success_url)


class CreateComment(NotificationMixin, ContextMixin, SpacesPostMixin, SuccessMessageMixin, FormView):
    form_class = CommentForm
    success_message = _("Comment was added successfully.")
    notification_label = 'spaces_blog_comment'
    notification_send_manually = True

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, slug=kwargs['post_slug'])
        return super(CreateComment, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        super(CreateComment, self).form_valid(form)
        author = self.request.user
        comment = form.cleaned_data['comment']
        self.new_comment = Comment.objects.create(
            author=author,
            comment=comment,
            post=self.object
        )
        actstream_action.send(
            sender=author,
            verb=_("has been commented"),
            target=self.request.SPACE,
            action_object=self.object.blogpost
        )

        #self.notification_object_title = comment[:75] + '...' if len(comment) > 77 else comment
        self.notification_object_title = self.object.blogpost
        self.notification_object_link = self.object.blogpost.get_absolute_url()
        self.send_notification()

        url = self.get_success_url()
        return url

    def get_success_url(self):
        return redirect('spaces_blog:detail', self.object.slug)

        