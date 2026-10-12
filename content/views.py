from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Category, Content


class ContentListView(ListView):
    template_name = "content/content_list.html"
    context_object_name = "items"
    paginate_by = 9

    def get_queryset(self):
        queryset = Content.objects.published().select_related("category")
        self.category = None
        category_slug = self.request.GET.get("category", "").strip()
        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=self.category)
        self.query = self.request.GET.get("q", "").strip()[:100]
        if self.query:
            queryset = queryset.filter(
                Q(title__icontains=self.query)
                | Q(summary__icontains=self.query)
                | Q(body__icontains=self.query)
            )
        return queryset

    def paginate_queryset(self, queryset, page_size):
        # get_page() falls back to the first/last page for invalid or
        # out-of-range page numbers instead of raising a 404.
        paginator = self.get_paginator(queryset, page_size)
        page = paginator.get_page(self.request.GET.get(self.page_kwarg))
        return paginator, page, page.object_list, page.has_other_pages()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        context["query"] = self.query
        context["categories"] = Category.objects.with_published_counts().filter(
            published_count__gt=0
        )
        return context


class ContentDetailView(DetailView):
    template_name = "content/content_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        queryset = Content.objects.select_related("category")
        # Staff with permission to view content may preview drafts.
        if self.request.user.has_perm("content.view_content"):
            return queryset
        return queryset.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.object
        related = Content.objects.none()
        if item.category_id:
            related = (
                Content.objects.published()
                .filter(category_id=item.category_id)
                .exclude(pk=item.pk)
                .select_related("category")[:3]
            )
        context["related"] = related
        return context
