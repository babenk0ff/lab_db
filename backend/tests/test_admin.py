import pytest

from django.urls import reverse
from deviceapp.admin import (
    DeviceAdminDeviceParseForm,
    DeviceAdminDeviceParsedDataForm,
)


class TestAdminIndexView:
    @pytest.mark.django_db
    def test_get_admin_unauthorized(self, client):
        url = reverse('admin:index')
        response = client.get(url)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_superuser_view(self, admin_client):
        url = reverse('admin:index')
        response = admin_client.get(url)
        assert response.status_code == 200


class TestDeviceAdminDeviceParseForm:
    @pytest.mark.parametrize(
        'test_string',
        [
            'Блок А-000 АБВГ.123456.789',
            'Блок АА000 АБВГ.123456.789',
            'Блок АА000-1 АБВГ.123456.789-01',
            'ЗИП-О АБВГ.123456.789',
            'Блочный блок АБВГ.123456.789',
            # 'Блок А000 АБВГ.123456.789',
        ],
    )
    def test_device_admin_parse_form_regex(self, test_string):
        form = DeviceAdminDeviceParseForm(data={
            'input': test_string
        })
        assert form.is_valid()


class TestDeviceAdminDeviceParsedDataForm:
    @pytest.fixture
    def valid_form_data(self):
        return {
            'device_type': 'Блок',
            'device_index': 'АА000',
            'org_code': 'АБВГ',
            'decimal_num': '123456.789',
        }

    @pytest.mark.parametrize(
        'device_type, expected_valid', [
            ('a' * 64, True),
            ('a' * 65, False),
            ('', False),
        ]
    )
    def test_device_type_field_length(self, valid_form_data, device_type,
                                      expected_valid):
        form_data = valid_form_data.copy()
        form_data['device_type'] = device_type

        form = DeviceAdminDeviceParsedDataForm(data=form_data)
        assert form.is_valid() == expected_valid

    @pytest.mark.parametrize(
        'device_index, expected_valid', [
            ('', True),
            ('a' * 65, True),
        ]
    )
    def test_device_index_field_length(self, valid_form_data, device_index,
                                       expected_valid):
        form_data = valid_form_data.copy()
        form_data['device_index'] = device_index

        form = DeviceAdminDeviceParsedDataForm(data=form_data)
        assert form.is_valid() == expected_valid

    @pytest.mark.parametrize(
        'org_code, expected_valid', [
            ('', False),
            ('Б', False),
            ('ББ', False),
            ('БББ', False),
            ('БББББ', False),
            ('1234', False),
            ('ABCD', False),

            ('ББББ', True),
            ('АБВГ', True),
            ('абвг', True),
        ]
    )
    def test_org_code_field(self, valid_form_data, org_code,
                            expected_valid):
        form_data = valid_form_data.copy()
        form_data['org_code'] = org_code

        form = DeviceAdminDeviceParsedDataForm(data=form_data)
        assert form.is_valid() == expected_valid

    @pytest.mark.parametrize(
        'decimal_num, expected_valid', [
            ('', False),
            ('123456789', False),
            ('123456-789', False),
            ('12345.789', False),
            ('123456.78', False),

            ('123456.789', True),
            ('123456.789-01', True),
        ]
    )
    def test_device_index_field_length(self, valid_form_data, decimal_num,
                                       expected_valid):
        form_data = valid_form_data.copy()
        form_data['decimal_num'] = decimal_num

        form = DeviceAdminDeviceParsedDataForm(data=form_data)
        assert form.is_valid() == expected_valid
