from django.core.validators import RegexValidator

org_code_validator = RegexValidator(
    regex=r'^[а-яА-Я]{4}$',
    message='Код должен состоять из четырех кириллических букв',
    code='invalid_code',
)
