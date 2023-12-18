# Django Model Forge



## Usage
You have three choices how to use the model forge.
The first one would be providing your model as a fixture.
Alternatively, you may define these models in your test package’s `__init__.py`.
Or, create a new model dynamically on the fly.

### Using fixture
```python
""" tests.py """

from django.db import models
import pytest

import model_forge


pytestmark = pytest.mark.django_db


# schema_editor requires an unblocked database
@pytest.fixture(scope='module', autouse=True)
def django_db_setup(django_db_setup, django_db_blocker):
    django_db_blocker.unblock()

# define your models as fixtures in your test.py
@pytest.fixture
def my_model():
    @model_forge.reforge
    class MyModel(models.Model):
        my_field = models.IntegerField(unique=True)
        ...
    return MyModel

# use them in your tests
def test_my_model(my_model):
    one, _ = my_model.objects.get_or_create(my_field=1)
    assert one.my_field == 1
    assert my_model.objects.filter(my_field=1).count() == 1
```

### Using module __init__
*untested*
```python
""" `tests/__init__.py` """
from django.db import models
import pytest

import model_forge


pytestmark = pytest.mark.django_db


# schema_editor requires an unblocked database
@pytest.fixture(scope='module', autouse=True)
def django_db_setup(django_db_setup, django_db_blocker):
    django_db_blocker.unblock()


@model_forge.reforge
class MyModel(models.Model):
    my_field = models.IntegerField(unique=True)
```

### dynamically

```python
"""
Create a new model and add it to `myapp`. As in the examples above, you must ensure your database is unblocked.
"""
from django.db import models
from myapp.models import MyModelMixin
import model_forge

fields = {'my_field': models.IntegerField(unique=True)}
meta = {'app_label': 'myapp'}

MyModel = model_forge.forge(
    'MyModel',
    fields=fields, meta=meta,
    superclasses=(MyModelMixin, models.Model)
)
```
