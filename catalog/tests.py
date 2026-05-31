from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, Tag


class ModelRelationshipTests(TestCase):
    def setUp(self):
        self.electronics = Category.objects.create(name='Electronics')
        self.wireless = Tag.objects.create(name='Wireless')
        self.audio = Tag.objects.create(name='Audio')
        self.product = Product.objects.create(
            name='Headphones',
            description='Noise cancelling over-ear headphones',
            price=Decimal('199.99'),
            category=self.electronics,
        )
        self.product.tags.add(self.wireless, self.audio)

    def test_product_belongs_to_one_category(self):
        self.assertEqual(self.product.category, self.electronics)

    def test_category_reverse_relation(self):
        self.assertIn(self.product, self.electronics.products.all())

    def test_product_has_many_tags(self):
        self.assertEqual(self.product.tags.count(), 2)

    def test_tag_reverse_relation(self):
        self.assertIn(self.product, self.wireless.products.all())


class ProductListViewTests(TestCase):
    def setUp(self):
        self.electronics = Category.objects.create(name='Electronics')
        self.books = Category.objects.create(name='Books')

        self.wireless = Tag.objects.create(name='Wireless')
        self.bestseller = Tag.objects.create(name='Bestseller')

        self.headphones = Product.objects.create(
            name='Headphones',
            description='Wireless noise cancelling headphones',
            price=Decimal('199.99'),
            category=self.electronics,
        )
        self.headphones.tags.add(self.wireless)

        self.novel = Product.objects.create(
            name='Mystery Novel',
            description='A thrilling page-turner',
            price=Decimal('14.99'),
            category=self.books,
        )
        self.novel.tags.add(self.bestseller)

        self.url = reverse('catalog:product_list')

    def test_no_filters_returns_all_products(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 2)

    def test_search_by_description_matches(self):
        response = self.client.get(self.url, {'q': 'thrilling'})
        products = response.context['products']
        self.assertEqual(list(products), [self.novel])

    def test_search_by_description_no_match(self):
        response = self.client.get(self.url, {'q': 'nonexistent'})
        self.assertEqual(len(response.context['products']), 0)

    def test_filter_by_category(self):
        response = self.client.get(self.url, {'category': self.electronics.id})
        self.assertEqual(list(response.context['products']), [self.headphones])

    def test_filter_by_tag(self):
        response = self.client.get(self.url, {'tags': [self.bestseller.id]})
        self.assertEqual(list(response.context['products']), [self.novel])

    def test_filter_by_multiple_tags_uses_or_semantics(self):
        response = self.client.get(
            self.url, {'tags': [self.wireless.id, self.bestseller.id]}
        )
        self.assertEqual(len(response.context['products']), 2)

    def test_combined_filters_narrow_results(self):
        # Description matches the novel, but category restricts to electronics,
        # so the combination should return nothing.
        response = self.client.get(
            self.url, {'q': 'thrilling', 'category': self.electronics.id}
        )
        self.assertEqual(len(response.context['products']), 0)

    def test_combined_search_and_tag_match(self):
        response = self.client.get(
            self.url, {'q': 'wireless', 'tags': [self.wireless.id]}
        )
        self.assertEqual(list(response.context['products']), [self.headphones])

    def test_non_numeric_category_is_ignored(self):
        # A garbage category value must not raise; it is ignored (all products).
        response = self.client.get(self.url, {'category': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 2)

    def test_non_numeric_tag_is_ignored(self):
        response = self.client.get(self.url, {'tags': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 2)

    def test_nonexistent_category_returns_empty(self):
        # A valid-but-unknown id is a legitimate query that simply matches nothing.
        response = self.client.get(self.url, {'category': 99999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)

    def test_mixed_valid_and_invalid_tags(self):
        # Non-numeric tag ids are dropped; valid ones still filter.
        response = self.client.get(self.url, {'tags': ['abc', self.wireless.id]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['products']), [self.headphones])


class CreateAdminCommandTests(TestCase):
    def _password_from(self, output):
        for line in output.splitlines():
            if line.startswith('Password: '):
                return line[len('Password: '):]
        return None

    def test_creates_working_superuser_and_prints_password(self):
        out = StringIO()
        call_command('create_admin', stdout=out)
        output = out.getvalue()

        self.assertIn('Username: admin', output)
        password = self._password_from(output)
        self.assertTrue(password)

        user = get_user_model().objects.get(username='admin')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        # The printed password must actually log the user in.
        self.assertTrue(user.check_password(password))

    def test_rerun_resets_password(self):
        out1 = StringIO()
        call_command('create_admin', stdout=out1)
        first = self._password_from(out1.getvalue())

        out2 = StringIO()
        call_command('create_admin', stdout=out2)
        second = self._password_from(out2.getvalue())

        # Still exactly one admin, and the latest printed password is the valid one.
        self.assertEqual(get_user_model().objects.filter(username='admin').count(), 1)
        self.assertNotEqual(first, second)
        self.assertTrue(get_user_model().objects.get(username='admin').check_password(second))
