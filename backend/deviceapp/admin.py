from django import forms
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db.models import Q
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .models import Device, OrgCode, DecimalNumber, Theme, DeviceType

admin.site.register(OrgCode)
admin.site.register(Theme)
admin.site.register(DeviceType)


class DeviceAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.decimal_num:
            self.fields['decimal_num'].queryset = DecimalNumber.objects.filter(
                Q(pk=self.instance.decimal_num.id) |
                Q(is_used=False)
            )
        else:
            self.fields['decimal_num'].queryset = DecimalNumber.objects.filter(is_used=False)


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    form = DeviceAdminForm
    list_display = ('__str__', 'get_themes')
    list_filter = ('type', 'theme')
    filter_horizontal = ('part_of', 'theme')

    def get_themes(self, obj):
        return mark_safe('<br>'.join([theme.name for theme in obj.theme.all()]))

    get_themes.short_description = 'Темы'

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is not None:
            cur_decimal = obj.decimal_num
            help_texts = {'decimal_num': f'Текущий присвоенный номер: {cur_decimal if cur_decimal else ""}'}
            kwargs.update({'help_texts': help_texts})
        return super(DeviceAdmin, self).get_form(request, obj, **kwargs)


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
            '<a href={}>{} {}</a>', f'/admin/deviceapp/device/{device.id}', device.type, device.index
        )

    get_devices.short_description = 'Чему присвоен'

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is not None:
            if obj.is_used:
                device = Device.objects.get(decimal_num=obj)
                help_texts = {'is_used': format_html(
                    'Присвоен: <a href={}>{} {}</a>',
                    f'/admin/deviceapp/device/{device.id}', device.type, device.index
                )}
                kwargs.update({'help_texts': help_texts})
        return super(DecimalNumberAdmin, self).get_form(request, obj, **kwargs)

