from django.shortcuts import render, get_object_or_404
import markdown
import re
from collections.abc import Iterable

from django.utils.text import slugify
from markdown.extensions.toc import TocExtension
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
# Create your views here.

from django.http import HttpResponse
from .models import Post, Category, Tag
from django.views.generic import ListView
from pure_pagination.mixins import PaginationMixin

class IndexView(PaginationMixin, ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 10


def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        # 记得在顶部引入 TocExtension 和 slugify
        TocExtension(slugify=slugify),
    ])
    post.body = md.convert(post.body)
    post.increase_views()

    m = re.search(r'<div class="toc">\s*<ul>(.*)</ul>\s*</div>', md.toc, re.S)
    post.toc = m.group(1) if m is not None else ''

    return render(request, 'blog/detail.html', context={'post': post})


class ArchiveView(IndexView):
    def get_queryset(self):
        return super(ArchiveView, self).get_queryset().filter(created_time__year=self.kwargs.get('year'),
                                                              created_time__month=self.kwargs.get('month'))

class CategoryView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 5

    def get_queryset(self):
        cate = get_object_or_404(Category, pk=self.kwargs.get('pk'))
        return super(CategoryView, self).get_queryset().filter(category=cate)

class TagView(IndexView):
    def get_queryset(self):
        t = get_object_or_404(Tag, pk=self.kwargs.get('pk'))
        return super(TagView, self).get_queryset().filter(tags=t)
    
def tag(request, pk):
    # 记得在开始部分导入 Tag 类
    t = get_object_or_404(Tag, pk=pk)
    post_list = Post.objects.filter(tags=t).order_by('-created_time')
    return render(request, 'blog/index.html', context={'post_list': post_list})


def search(request):
    q = request.GET.get('q')

    if not q:
        error_msg = "请输入搜索关键词"
        messages.add_message(request, messages.ERROR, error_msg, extra_tags='danger')
        return redirect('blog:index')

    post_list = Post.objects.filter(Q(title__icontains=q) | Q(body__icontains=q))
    return render(request, 'blog/index.html', {'post_list': post_list})