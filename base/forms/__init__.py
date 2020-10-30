from django import forms

from base.models import SystemSettings
from common.forms import ModelForm

__all__ = [
    'SystemSettingsUpdateForm',
]


class SystemSettingsUpdateForm(ModelForm):

    def clean_val(self):
        val = self.cleaned_data['val']
        choices = self.instance.val_choices
        upper = self.instance.val_max
        lower = self.instance.val_min
        if choices is not None:
            try:
                choice_names = (c['name'] for c in choices)
                _ = (c['value'] for c in choices)
            except KeyError:
                self.add_error(
                    'val',
                    forms.ValidationError(
                        'val_choices格式错误',
                        code='wrong_val_choice_format'
                    )
                )
            else:
                if choices is not None and val not in choice_names:
                    self.add_error(
                        'val',
                        forms.ValidationError(
                            '%(val)s不可用, 可选值为 %(choice_names)s',
                            params={'val': val, 'choice_names': ', '.join(choice_names)},
                            code='wrong_choice_names'
                        )
                    )
                if upper is not None and val > upper:
                    self.add_error(
                        'val',
                        forms.ValidationError(
                            '%(val)s 不能大于 %(upper)s',
                            params={'val': val, 'upper': upper},
                            code='wrong_value_upper'
                        )
                    )
                if lower is not None and val < lower:
                    self.add_error(
                        'val',
                        forms.ValidationError(
                            '%(val)s 不能小于 %(lower)s',
                            params={'val': val, 'lower': lower},
                            code='wrong_value_lower'
                        )
                    )
        return val

    class Meta:
        model = SystemSettings
        fields = ('val',)
