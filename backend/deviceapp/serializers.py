from rest_framework.serializers import ModelSerializer, StringRelatedField

from .models import Device, DeviceType, DecimalNumber, Theme, OrgCode


class DeviceTypeSerializer(ModelSerializer):
    class Meta:
        model = DeviceType
        fields = '__all__'


class OrgCodeSerializer(ModelSerializer):
    class Meta:
        model = OrgCode
        fields = '__all__'


class DecimalNumberSerializer(ModelSerializer):
    org_code = OrgCodeSerializer()

    class Meta:
        model = DecimalNumber
        fields = '__all__'


class ThemeSerializer(ModelSerializer):
    class Meta:
        model = Theme
        fields = '__all__'


class DeviceSerializer(ModelSerializer):
    type = DeviceTypeSerializer()
    decimal_num = DecimalNumberSerializer()
    theme = ThemeSerializer()

    class Meta:
        model = Device
        fields = '__all__'


class SimpleDeviceSerializer(ModelSerializer):
    type = StringRelatedField()
    decimal_num = StringRelatedField()

    class Meta:
        model = Device
        fields = [
            'type',
            'index',
            'decimal_num',
        ]

