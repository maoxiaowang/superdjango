from django import forms
from django.contrib.contenttypes.models import ContentType

from base.models import Resource
from common.forms.fields import ListField, DictField, JsonField
from common.forms import ModelForm
from vserver.models import VM


class UserResourceCreatForm(forms.Form):
    """
    Create userpermission
    """
    user_id = forms.IntegerField(label='user_id', required=True)
    resource_type = forms.ChoiceField(label="资源对象type",
                                      choices=[("vm", "vm"), ("host", "host"), ("storagedomain", "storagedomain"),
                                               ("network", "network")])
    resource_list = ListField(label='用户资源编辑关系', required=True, help_text='[{"object_pk":xxxx,"action":1},{....}]')

    def clean_resource(self):
        resource_list = self.cleaned_data.get('resource_list')
        resource_type = self.cleaned_data.get('resource_type')
        ct = ContentType.objects.filter(app_label='vserver', model=resource_type).first()
        if ct is None:
            raise forms.ValidationError("资源模块不存在，无法分配资源。")
        if ct.model == 'vm':
            for i in iter(resource_list):
                if Resource.objects.filter(object_pk=i['object_pk'], object_ct=ct) and i['action'] == 0:
                    # 如果是虚拟机模块并且创建者为管理员 则判断是否存在
                    vm = VM.objects.get(id=i['object_pk'])
                    raise forms.ValidationError("虚拟机: %s 已分配给其他人员，请检查。" % vm.name)
        return resource_list
