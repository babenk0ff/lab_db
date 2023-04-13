import re

from django import forms
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.core.validators import RegexValidator
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponse, render, redirect, \
    HttpResponseRedirect

from deviceapp.models import Device, OrgCode, DecimalNumber, Theme, DeviceType

admin.site.register(OrgCode)
admin.site.register(Theme)
admin.site.register(DeviceType)


class DeviceAdminDeviceParseForm(forms.Form):
    template_name = 'parse_form_snippet.html'

    input = forms.CharField(
        label='Полное наименование изделия',
        max_length=100,
        help_text='Формат: Наименование изделия АБВГ.123456.789',
        validators=[
            RegexValidator(
                regex=r'^([а-яА-я-\s]*)\s'
                      r'([А-Я]{2}\d{3}'
                      r'(?:-\d{1,2})?\s)?'
                      r'([А-Я]{4}).([0-9]{6}.[0-9]{3}(?:-[0-9]{2})?)$',
                message='Неверный формат строки',
                code='invalid_code',
            ),
        ],
    )


class DeviceAdminDeviceParsedDataForm(forms.Form):
    template_name = 'parse_form_snippet.html'

    device_type = forms.CharField(
        label='Тип изделия',
        max_length=64,
    )
    device_index = forms.CharField(
        label='Индекс изделия',
        required=False,
    )
    org_code = forms.CharField(
        label='Код организации-разработчика',
        max_length=4,
        validators=[
            RegexValidator(
                regex='^[а-яА-Я]{4}$',
                message='Код должен состоять из четырех кириллических букв',
                code='invalid_code',
            )
        ]
    )
    decimal_number = forms.CharField(
        max_length=13,
        help_text='Формат: 123456.789 или 123456.789-01',
        validators=[
            RegexValidator(
                regex='^[0-9]{6}.[0-9]{3}(-[0-9]{2})?$',
                message='Неверный формат номера'
            ),
        ]
    )


class DeviceAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.decimal_num:
            self.fields['decimal_num'].queryset = DecimalNumber.objects.filter(
                Q(pk=self.instance.decimal_num.id) |
                Q(is_used=False)
            )
        else:
            self.fields['decimal_num'].queryset = DecimalNumber.objects.filter(
                is_used=False
            )


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    form = DeviceAdminForm
    list_display = ('__str__', 'get_themes')
    list_filter = ('type', 'theme')
    filter_horizontal = ('part_of', 'theme')
    change_list_template = 'admin/deviceapp/device/change_list.html'

    def get_themes(self, obj):
        return mark_safe(
            '<br>'.join([theme.name for theme in obj.theme.all()])
        )

    get_themes.short_description = 'Темы'

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is not None:
            cur_decimal = obj.decimal_num
            help_texts = {
                'decimal_num': f'Текущий присвоенный номер: '
                               f'{cur_decimal if cur_decimal else ""}'
            }
            kwargs.update({'help_texts': help_texts})
        return super(DeviceAdmin, self).get_form(request, obj, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('parse/',
                 self.admin_site.admin_view(self.parse),
                 name='device_parse'),
            path('save_parsed_data/',
                 self.admin_site.admin_view(self.save_parsed_data),
                 name='device_save_parsed_data')
        ]
        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            'url_parse': reverse('admin:device_parse'),
            'url_parsed_save': reverse('admin:device_save_parsed_data'),
            'form': DeviceAdminDeviceParseForm,
        }
        return super(DeviceAdmin, self).changelist_view(request, extra_context)

    def parse(self, request):
        if request.method == 'POST':
            form = DeviceAdminDeviceParseForm(request.POST)
            if form.is_valid():
                pattern = re.compile(
                    r'^([а-яА-я-\s]*)\s'
                    r'([А-Я]{2}\d{3}'
                    r'(?:-\d{1,2})?\s)?'
                    r'([А-Я]{4}).([0-9]{6}.[0-9]{3}(?:-[0-9]{2})?)$'
                )
                parsed_data = re.findall(pattern, form.cleaned_data['input'])
                device_type, device_index, org_code, decimal_number = \
                    parsed_data[0]

                form = DeviceAdminDeviceParsedDataForm(
                    {
                        'device_type': device_type,
                        'device_index': device_index,
                        'org_code': org_code,
                        'decimal_number': decimal_number,
                    }
                )
                return render(
                    request,
                    'admin/deviceapp/device/device_parsed_data.html',
                    {'form': form}
                )
        else:
            form = DeviceAdminDeviceParseForm

        context = {
            'form': form,
            'url_parse': reverse('admin:device_parse')
        }

        return render(request,
                      'admin/deviceapp/device/device_parse.html',
                      context)

    def save_parsed_data(self, request):
        if request.method == 'POST':
            form = DeviceAdminDeviceParsedDataForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                try:
                    with transaction.atomic():
                        device_type, _ = DeviceType.objects.get_or_create(
                            name=data['device_type'])
                        org_code, _ = OrgCode.objects.get_or_create(
                            code=data['org_code'])
                        decimal_number = DecimalNumber.objects.create(
                            org_code=org_code,
                            number=data['decimal_number'],
                            is_used=True,
                        )
                        Device.objects.create(
                            type=device_type,
                            index=data['device_index'],
                            decimal_num=decimal_number,
                        )
                except IntegrityError:
                    transaction.rollback()
                return HttpResponseRedirect('/admin')
        else:
            form = DeviceAdminDeviceParsedDataForm

        return render(
            request,
            'admin/deviceapp/device/device_parsed_data.html',
            {'form': form},
        )


@admin.register(DecimalNumber)
class DecimalNumberAdmin(ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('org_code', 'number', 'is_used')
        }),
    )
    list_display = ('__str__', 'is_used', 'get_devices')
    list_filter = ('org_code', 'is_used')
    readonly_fields = ['is_used']

    def get_devices(self, obj):
        device = Device.objects.get(decimal_num=obj)
        return format_html(
            '<a href={}>{} {}</a>',
            f'/admin/deviceapp/deviceapp/{device.id}',
            device.type,
            device.index
        )

    get_devices.short_description = 'Чему присвоен'

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is not None:
            if obj.is_used:
                device = Device.objects.get(decimal_num=obj)
                help_texts = {'is_used': format_html(
                    'Присвоен: <a href={}>{} {}</a>',
                    f'/admin/deviceapp/deviceapp/{device.id}',
                    device.type,
                    device.index
                )}
                kwargs.update({'help_texts': help_texts})
        return super(DecimalNumberAdmin, self).get_form(request, obj, **kwargs)
