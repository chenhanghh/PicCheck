from django.forms import ClearableFileInput


# 支持多文件上传
class MultiFileInput(ClearableFileInput):

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['multi'] = True
        return context

    def value_from_datadict(self, data, files, name):
        upload = super().value_from_datadict(data, files, name)
        if upload:
            return [upload]
        return []

