from django import forms


# 多文件上传
class FileFieldForm(forms.Form):
    # file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={"allow_multiple_selected": True}),
                                 required=False)
