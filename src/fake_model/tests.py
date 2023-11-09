from typing import Type

from django.db import models
import pytest

import fake_model


pytestmark = pytest.mark.django_db


# schema_editor requires an unblocked database
@pytest.fixture(scope='module', autouse=True)
def django_db_setup(django_db_setup, django_db_blocker):
    django_db_blocker.unblock()


class TestFakedModel:

    @pytest.fixture(scope='class')
    def virtual_user(self) -> Type[models.Model]:
        @fake_model.register
        class VirtualUser(models.Model):
            alias = models.CharField(max_length=16, null=False, unique=True)
            email = models.EmailField(null=False, unique=True)

        return VirtualUser

    def test_model_creation(self, virtual_user):
        assert issubclass(virtual_user, models.Model)

    def test_virtual_user_create(self, virtual_user):
        user = virtual_user.objects.create(alias="test", email="test@domain.org")
        assert user.alias == "test"
        assert user.email == "test@domain.org"
        assert virtual_user.objects.filter(alias="test").count() == 1


class TestFakedModelRelation:

    @pytest.fixture
    def authors(self):
        return [
            'J.R.R. Tolkien',
            'George Orwell',
            'Leo Tolstoy',
            'Stephen Hawking'
        ]

    @pytest.fixture
    def work_of_tolkien(self):
        return [
            'The Hobbit (1937)',
            'The Fellowship of the Ring(1954)',
            'The Two Towers (1954)',
            'The Return of the King (1955)',
            'The Silmarillion (1977)',
            'Unfinished Tales of Númenor and Middle-Earth (1980)',
            'The Children of Húrin (2007)',
            'The Book of Lost Tales (Part One and Two)',
            'The Letters of J.R.R.Tolkien (1981)',
        ]

    @pytest.fixture(scope='class')
    def fake_author(self):
        @fake_model.register
        class FakeAuthor(models.Model):
            name = models.CharField(max_length=32, unique=True)

        return FakeAuthor

    @pytest.fixture(scope='class')
    def fake_book(self, fake_author):
        @fake_model.register
        class FakeBook(models.Model):
            author = models.ForeignKey(fake_author, on_delete=models.CASCADE, related_name='books')
            title = models.CharField(null=False, blank=False, max_length=128)

        return FakeBook

    def test_create_author(self, fake_author, authors):
        for name in authors:
            fake_author.objects.create(name=name)
            author = fake_author.objects.get(name=name)
            assert author is not None

    def test_count(self, fake_author, authors):
        for name in authors:
            fake_author.objects.get_or_create(name=name)
        assert fake_author.objects.count() == len(authors)

    def test_relation(self, fake_author, fake_book, work_of_tolkien):
        tolkien, _ = fake_author.objects.get_or_create(name='J.R.R. Tolkien')
        for book_name in work_of_tolkien:
            fake_book.objects.update_or_create(title=book_name, author=tolkien)
        # via count
        assert fake_book.objects.filter(author=tolkien, title__in=work_of_tolkien).count() == len(work_of_tolkien)
        # via reverse_related aggregation
        agg = fake_author.objects.filter(name='J.R.R. Tolkien').aggregate(book_count=models.Count('books'))
        assert agg['book_count'] == len(work_of_tolkien)
