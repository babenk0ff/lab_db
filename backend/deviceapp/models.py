from django.db import models, transaction
from django.core.validators import RegexValidator


class Theme(models.Model):
    name = models.CharField(max_length=128,
                            unique=True,
                            verbose_name='Название темы')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'


class OrgCode(models.Model):
    code = models.CharField(
        max_length=4,
        unique=True,
        verbose_name='Четырехзначный буквенный код',
        validators=[
            RegexValidator(
                regex='^[а-яА-Я]{4}$',
                message='Код должен состоять из четырех кириллических букв',
                code='invalid_code',
            )
        ])

    def __str__(self):
        return self.code.upper()

    class Meta:
        verbose_name = 'Код организации-разработчика'
        verbose_name_plural = 'Коды организаций-разработчиков'


class DecimalNumber(models.Model):
    org_code = models.ForeignKey(OrgCode,
                                 on_delete=models.PROTECT,
                                 verbose_name='Код организации-разработчика')
    number = models.CharField(
        unique=True,
        max_length=13,
        verbose_name='Цифровая часть децимального номера',
        help_text='Формат: 123456.789 или 123456.789-01',
        validators=[
            RegexValidator(
                regex=r'^[0-9]{6}\.[0-9]{3}(-[0-9]{2})?$',
                message='Неверный формат номера'
            )
        ]
    )
    is_used = models.BooleanField(default=False, verbose_name='Присвоен')

    def __str__(self):
        return f'{self.org_code}.{self.number}'

    class Meta:
        verbose_name = 'Децимальный номер'
        verbose_name_plural = 'Децимальные номера'


class DeviceType(models.Model):
    name = models.CharField(max_length=64,
                            unique=True,
                            null=True,
                            blank=True,
                            verbose_name='Наименование типа изделия',
                            help_text='Аппарат, Блок, Комплекс, Ячейка и т.п.')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип изделия'
        verbose_name_plural = 'Типы изделий'


class Device(models.Model):
    def __init__(self, *args, **kwargs):
        super(Device, self).__init__(*args, **kwargs)
        self.__current_decimal_num_id = self.decimal_num.id if \
            self.decimal_num else None

    type = models.ForeignKey(DeviceType,
                             on_delete=models.PROTECT,
                             verbose_name='Тип изделия')
    index = models.CharField(max_length=64,
                             # unique=True,
                             blank=True,
                             null=True,
                             verbose_name='Индекс изделия')
    decimal_num = models.OneToOneField(DecimalNumber,
                                       blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       verbose_name='Децимальный номер')
    part_of = models.ManyToManyField('self',
                                     symmetrical=False,
                                     blank=True,
                                     verbose_name='В какое изделие входит')
    theme = models.ManyToManyField(Theme, blank=True, verbose_name='Тема')

    def __str__(self):
        string = f'{self.type} {self.index}' if self.index else str(self.type)
        return string + f' {self.decimal_num}' if self.decimal_num else string

    def __make_unused(self):
        orig_num_obj = DecimalNumber.objects.get(
            pk=self.__current_decimal_num_id
        )
        orig_num_obj.is_used = False
        orig_num_obj.save()

    def __make_used(self):
        new_num_obj = DecimalNumber.objects.get(pk=self.decimal_num.id)
        new_num_obj.is_used = True
        new_num_obj.save()

    def __manage_use(self, action):
        if action == 'set':
            self.__make_used()
        elif action == 'clean':
            self.__make_unused()
        elif action == 'update':
            self.__make_unused()
            self.__make_used()

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None,
             commit=True):

        curr_num_id = self.__current_decimal_num_id
        new_num_obj = self.decimal_num
        if curr_num_id is not None:
            if new_num_obj is not None:
                if curr_num_id != new_num_obj.id:
                    self.__manage_use('update')
            else:
                self.__manage_use('clean')
        else:
            if new_num_obj is not None:
                self.__manage_use('set')

        super(Device, self).save(force_insert,
                                 force_update,
                                 using,
                                 update_fields)

    def delete(self, using=None, keep_parents=False):
        current_decimal_num = self.decimal_num

        with transaction.atomic():
            current_decimal_num.is_used = False
            current_decimal_num.save()
            super(Device, self).delete(using, keep_parents)

    class Meta:
        verbose_name = 'Изделие'
        verbose_name_plural = 'Изделия'
