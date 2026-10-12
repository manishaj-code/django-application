from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from content.models import Category, Content

pytestmark = pytest.mark.django_db
LIST_URL = reverse("content:list")


class TestHome:
    def test_empty_state(self, client):
        response = client.get(reverse("core:home"))
        assert response.status_code == 200
        assert b"Nothing published yet" in response.content

    def test_shows_latest_published_only(self, client, published, draft, scheduled):
        response = client.get(reverse("core:home"))
        assert list(response.context["latest"]) == [published]
        assert b"Draft item" not in response.content
        assert b"Future item" not in response.content


class TestContentList:
    def test_empty_state(self, client):
        response = client.get(LIST_URL)
        assert response.status_code == 200
        assert b"Nothing here yet" in response.content

    def test_lists_only_public_content(self, client, published, draft, scheduled):
        response = client.get(LIST_URL)
        assert list(response.context["items"]) == [published]

    def test_pagination(self, client, make_content):
        now = timezone.now()
        for i in range(20):
            make_content(f"Item {i:02d}", published_at=now - timedelta(minutes=i))
        first = client.get(LIST_URL)
        assert len(first.context["items"]) == 9
        assert first.context["is_paginated"]
        assert first.context["paginator"].num_pages == 3
        assert b'rel="next"' in first.content

        last = client.get(LIST_URL, {"page": 3})
        assert len(last.context["items"]) == 2
        assert last.context["items"][0].title == "Item 18"

    @pytest.mark.parametrize("page, expected", [("abc", 1), ("999", 2), ("-1", 2), ("", 1)])
    def test_invalid_page_numbers_fall_back(self, client, make_content, page, expected):
        for i in range(10):
            make_content(f"Item {i}")
        response = client.get(LIST_URL, {"page": page})
        assert response.status_code == 200
        assert response.context["page_obj"].number == expected

    def test_pagination_links_keep_filters(self, client, make_content, category):
        for i in range(10):
            make_content(f"Match {i}", category=category)
        response = client.get(LIST_URL, {"q": "Match", "category": category.slug})
        assert f"?q=Match&amp;category={category.slug}&amp;page=2".encode() in response.content

    def test_filter_by_category(self, client, published, make_content):
        other = Category.objects.create(name="Other")
        make_content("Elsewhere", category=other)
        response = client.get(LIST_URL, {"category": published.category.slug})
        assert list(response.context["items"]) == [published]
        assert response.context["category"] == published.category

    def test_unknown_category_returns_404(self, client, db):
        response = client.get(LIST_URL, {"category": "does-not-exist"})
        assert response.status_code == 404

    def test_search(self, client, make_content):
        make_content("Django tips", body="All about the ORM")
        make_content("Gardening", summary="Plants", body="Tomatoes")
        make_content("Hidden", body="Django draft", status=Content.Status.DRAFT)
        response = client.get(LIST_URL, {"q": "django"})
        assert [i.title for i in response.context["items"]] == ["Django tips"]
        response = client.get(LIST_URL, {"q": "tomatoes"})
        assert [i.title for i in response.context["items"]] == ["Gardening"]

    def test_search_without_results(self, client, published):
        response = client.get(LIST_URL, {"q": "zzz-nothing"})
        assert b"No matches" in response.content

    def test_search_input_is_escaped(self, client, published):
        response = client.get(LIST_URL, {"q": "<script>alert(1)</script>"})
        assert b"<script>alert(1)</script>" not in response.content
        assert b"&lt;script&gt;" in response.content

    def test_query_count_is_constant(self, client, make_content, category, django_assert_max_num_queries):
        for i in range(9):
            make_content(f"Item {i}", category=category)
        with django_assert_max_num_queries(8):
            client.get(LIST_URL)


class TestContentDetail:
    def test_published_detail(self, client, published):
        response = client.get(published.get_absolute_url())
        assert response.status_code == 200
        assert response.context["item"] == published
        assert b"<p>First paragraph.</p>" in response.content
        assert b"Preview." not in response.content

    @pytest.mark.parametrize("fixture", ["draft", "scheduled"])
    def test_hidden_content_is_404_for_public(self, client, request, fixture):
        item = request.getfixturevalue(fixture)
        assert client.get(item.get_absolute_url()).status_code == 404

    def test_hidden_content_is_404_for_regular_user(self, client, user, draft):
        client.force_login(user)
        assert client.get(draft.get_absolute_url()).status_code == 404

    def test_editor_can_preview_draft(self, client, editor, draft):
        client.force_login(editor)
        response = client.get(draft.get_absolute_url())
        assert response.status_code == 200
        assert b"This item is a draft" in response.content
        assert b"Edit in admin" in response.content

    def test_missing_slug_returns_404(self, client, db):
        response = client.get(reverse("content:detail", args=["no-such-item"]))
        assert response.status_code == 404
        assert b"Page not found" in response.content

    def test_body_html_is_escaped(self, client, make_content):
        item = make_content("XSS", body='<script>alert("x")</script>')
        response = client.get(item.get_absolute_url())
        assert b'<script>alert("x")</script>' not in response.content
        assert b"&lt;script&gt;" in response.content

    def test_related_items_from_same_category(self, client, published, make_content):
        sibling = make_content("Sibling", category=published.category)
        make_content("Unrelated")
        response = client.get(published.get_absolute_url())
        assert list(response.context["related"]) == [sibling]

    def test_featured_image_rendered(self, client, image_file, make_content):
        item = make_content("With image", featured_image=image_file)
        response = client.get(item.get_absolute_url())
        assert item.featured_image.url.encode() in response.content
