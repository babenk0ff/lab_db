from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import filters

from .models import Device
from .serializers import DeviceSerializer, SimpleDeviceSerializer


class DeviceModelViewSet(ReadOnlyModelViewSet):
    queryset = Device.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'type__name',
        'index',
        'decimal_num__number',
        'decimal_num__org_code__code',
    ]

    def get_serializer_class(self):
        if self.request.query_params.get('simple') == '1':
            return SimpleDeviceSerializer
        return DeviceSerializer

