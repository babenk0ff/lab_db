import re

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.decorators import action, display
from django.core.validators import RegexValidator
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from django.urls import path, reverse
from django.shortcuts import render, redirect

from deviceapp.models import Device, OrgCode, DecimalNumber, Theme, DeviceType

admin.site.register(OrgCode)
admin.site.register(Theme)
admin.site.register(DeviceType)


class DeviceTypeForm(forms.ModelForm):
    class Meta:
        model = DeviceType
        fields = ['name']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')

        if name:
            try:
                existing_object = DeviceType.objects.get(name=name)
                self.instance = existing_object
            except DeviceType.DoesNotExist:
                pass

        return cleaned_data


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['index']


class DecimalNumForm(forms.ModelForm):
    class Meta:
        model = DecimalNumber
        fields = ['number']


class OrgCodeForm(forms.ModelForm):
    class Meta:
        model = OrgCode
        fields = ['code']

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')

        if code:
            try:
                existing_object = OrgCode.objects.get(code=code)
                self.instance = existing_object
            except OrgCode.DoesNotExist:
                pass

        return cleaned_data


class DeviceAdminDeviceParseForm(forms.Form):
    template_name = 'parse_form_snippet.html'
    parse_regex = re.compile(
        r'^([а-яА-я-\s]*[а-яА-я])\s*'
        r'((?:[А-Я]{2}\d{3}|[А-Я]-\d{3})(?:-\d{1,2})?)?\s?'
        r'([А-Я]{4}).([0-9]{6}.[0-9]{3}(?:-[0-9]{2})?)$'
    )

    input = forms.CharField(
        label='Полное наименование изделия',
        max_length=100,
        help_text='Формат: Наименование изделия АБВГ.123456.789',
        validators=[
            RegexValidator(
                regex=parse_regex,
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
        help_text='Формат: АБВГ',
        required=True,
        validators=[
            RegexValidator(
                regex='^[а-яА-Я]{4}$',
                message='Код должен состоять из четырех кириллических букв',
                code='invalid_code',
            )
        ]
    )
    decimal_num = forms.CharField(
        label='Цифровая часть децимального номера',
        max_length=13,
        help_text='Формат: 123456.789 или 123456.789-01',
        validators=[
            RegexValidator(
                regex=r'^[0-9]{6}\.[0-9]{3}(-[0-9]{2})?$',
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


class DeviceAdminAssignThemeActionForm(forms.Form):
    themes = forms.ChoiceField(label='Тема')

    def __init__(self, *args, **kwargs):
        super(DeviceAdminAssignThemeActionForm, self).__init__(*args, **kwargs)
        self.fields['themes'].choices = [
            (theme.id, theme.name) for theme in Theme.objects.all()
        ]


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    form = DeviceAdminForm
    list_display = ('__str__', 'is_part_of', 'get_themes')
    list_filter = ('type', 'theme')
    filter_horizontal = ('part_of', 'theme')
    change_list_template = 'admin/deviceapp/device/change_list.html'
    actions = ('action_assign_theme',)
    list_per_page = 50
    ordering = ('type', 'decimal_num')

    @display(description='Темы')
    def get_themes(self, obj):
        themes = []
        for theme in obj.theme.all():
            a_tag = mark_safe('<a href="{}">{}</a>'.format(
                reverse('admin:deviceapp_theme_change', args=(theme.id,)),
                theme.name
            ))
            themes.append(
                '''
                <span class="{}"
                      style="display: block; margin-bottom: 4px;">{}
                </span>
                '''.format('thm-elem', a_tag)
            )
        return mark_safe(''.join(themes))

    @display(description='Входимость', boolean=True)
    def is_part_of(self, obj):
        if obj.part_of.count() > 0:
            return True
        return False

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
                 name='device_save_parsed_data'),
        ]
        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            'url_parse': reverse('admin:device_parse'),
            'url_parsed_save': reverse('admin:device_save_parsed_data'),
        }
        return super(DeviceAdmin, self).changelist_view(request, extra_context)

    def parse(self, request):
        if request.method == 'POST':
            form = DeviceAdminDeviceParseForm(request.POST)
            if form.is_valid():
                prepared_string = re.sub(
                    pattern=' {2,}',
                    repl=' ',
                    string=form.cleaned_data['input'],
                )
                pattern = DeviceAdminDeviceParseForm.parse_regex
                parsed_data = re.findall(pattern, prepared_string)
                device_type, device_index, org_code, decimal_number = \
                    map(str.strip, parsed_data[0])

                form_device_type = DeviceTypeForm(
                    initial={'name': device_type}
                )

                form_device = DeviceForm(
                    initial={'index': device_index}
                )

                form_org_code = OrgCodeForm(
                    initial={'code': org_code}
                )

                form_decimal_num = DecimalNumForm(
                    initial={'number': decimal_number}
                )

                context = {
                    'form_device_type': form_device_type,
                    'form_device': form_device,
                    'form_org_code': form_org_code,
                    'form_decimal_num': form_decimal_num,
                }

                return render(
                    request,
                    'admin/deviceapp/device/device_parsed_data.html',
                    context,
                )
        else:
            context = {
                'form': DeviceAdminDeviceParseForm()
            }

        return render(
            request,
            'admin/deviceapp/device/device_parse.html',
            context,
        )

    def save_parsed_data(self, request):
        if request.method == 'POST':

            form_device_type = DeviceTypeForm(request.POST)
            form_device = DeviceForm(request.POST)
            form_org_code = OrgCodeForm(request.POST)
            form_decimal_num = DecimalNumForm(request.POST)

            if form_device_type.is_valid() \
                    and form_device.is_valid() \
                    and form_org_code.is_valid() \
                    and form_decimal_num.is_valid():

                device_type = form_device_type.cleaned_data['name']
                device = form_device.cleaned_data['index']
                org_code = form_org_code.cleaned_data['code']
                decimal_num = form_decimal_num.cleaned_data['number']

                try:
                    with transaction.atomic():
                        device_type_obj, _ = DeviceType \
                            .objects.get_or_create(name=device_type)

                        org_code_obj, _ = OrgCode \
                            .objects.get_or_create(code=org_code)

                        decimal_number_obj, created = DecimalNumber \
                            .objects.get_or_create(org_code=org_code_obj,
                                                   number=decimal_num,
                                                   defaults={'is_used': True})

                        if not created and not decimal_number_obj.is_used:
                            decimal_number_obj.is_used = True
                            decimal_number_obj.save()
                        Device.objects.create(
                            type=device_type_obj,
                            index=device,
                            decimal_num=decimal_number_obj,
                        )

                except (IntegrityError, ValueError) as e:
                    form_device.add_error(None, 'Ошибка при сохранении')
                    model_attr = e.args[0].split('.')[1].replace('_id', '')
                    if model_attr == 'index':
                        field = 'device_index'
                    else:
                        field = model_attr
                    error = 'Уже существует'
                    form_device.add_error(field, error)

                    context = {
                        'form_device_type': form_device_type,
                        'form_device': form_device,
                        'form_org_code': form_org_code,
                        'form_decimal_num': form_decimal_num,
                    }

                    return render(
                        request,
                        'admin/deviceapp/device/device_parsed_data.html',
                        context,
                    )
                else:
                    context = {
                        'redirect_url': reverse(
                            'admin:deviceapp_device_changelist'
                        ),
                    }
                    return render(
                        request,
                        'admin/deviceapp/device/device_parsed_data.html',
                        context,
                    )
            else:
                context = {
                    'form_device_type': form_device_type,
                    'form_device': form_device,
                    'form_org_code': form_org_code,
                    'form_decimal_num': form_decimal_num,
                }
                return render(
                    request,
                    'admin/deviceapp/device/device_parsed_data.html',
                    context,
                )

        return redirect('admin:deviceapp_device_changelist')

    def delete_queryset(self, request, queryset):
        for each in queryset:
            each.delete()

    @action(description='Присвоить тему')
    def action_assign_theme(self, request, queryset):
        form = DeviceAdminAssignThemeActionForm()
        device_count = queryset.count()
        if 'apply' in request.POST:
            with transaction.atomic():
                try:
                    theme = Theme.objects.get(pk=request.POST['themes'])
                    for device in queryset:
                        device.theme.add(theme)
                except IntegrityError:
                    self.message_user(
                        request,
                        'Не удалось присвоить тему "{}"'.format(theme.name),
                        messages.ERROR
                    )
                else:
                    self.message_user(
                        request,
                        'Тема "{}" успешно присвоена изделиям '
                        'в количестве {} шт'.format(theme.name, device_count),
                        messages.SUCCESS
                    )
                return None

        context = {
            'form': form,
            'devices': queryset,
            'device_count': device_count,
        }
        return render(request,
                      'admin/deviceapp/device/assign_theme.html',
                      context)


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
            reverse('admin:deviceapp_device_change', args=(device.id,)),
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
                    reverse('admin:deviceapp_device_change',
                            args=(device.id,)),
                    device.type,
                    device.index
                )}
                kwargs.update({'help_texts': help_texts})
        return super(DecimalNumberAdmin, self).get_form(request, obj, **kwargs)
