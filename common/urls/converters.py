"""
Custom converters
"""
from django.urls.converters import StringConverter


class CommaSeparatedIntConverter:
    """
    逗号分隔的数字
    """
    regex = r'[0-9,]+'

    def to_python(self, value):
        return [int(item) for item in value.split(',')]

    def to_url(self, value):
        return str(value)


class CommaSeparatedUUIdsConverter:
    """
    逗号分隔的UUID
    """
    regex = r'[0-9a-zA-Z,-]+'

    def to_python(self, value):
        return [str(item) for item in value.split(',')]

    def to_url(self, value):
        return str(value)


class AlphaDigitConverter(StringConverter):
    """
    字母数字混合
    """
    regex = '[a-zA-Z0-9]+'
