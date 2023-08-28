import pytest

from deviceapp.models import (
    Theme,
    OrgCode,
    DecimalNumber,
    DeviceType,
    Device,
)


class TestTheme:
    @pytest.mark.django_db
    def test_create_theme(self):
        name = 'a' * 128
        theme = Theme.objects.create(name=name)
        assert theme.name == name

    @pytest.mark.django_db
    def test_create_theme(self):
        name = 'a' * 129
        theme = Theme.objects.create(name=name)
        assert theme.name == name


