from django import forms
from django.conf import settings

from ideascube.widgets import LangSelect

from .models import Document
from .utils import guess_kind_from_content_type, guess_kind_from_filename

import os


class DocumentForm(forms.ModelForm):

    class Meta:
        model = Document
        fields = '__all__'
        widgets = {
            'lang': LangSelect,
        }
        exclude = ['package_id']

    def clean(self):
        cleaned_data = super().clean()

        kind = cleaned_data['kind']
        original = cleaned_data.get('original')

        if original is None:
            # The 'original' field validator already found this was wrong
            return cleaned_data

        if kind != Document.OTHER:
            return cleaned_data

        try:
            new_kind = guess_kind_from_content_type(original.content_type)

        except AttributeError:
            # The document was edited without changing its 'original'
            new_kind = guess_kind_from_filename(original.name)

        cleaned_data['kind'] = new_kind or kind

        return cleaned_data

    def save(self, commit=True):
        document = super().save(commit=commit)

        if commit:
            # Need to save a second time to index the m2m
            document.save()

        return document


class PackagedDocumentForm(forms.ModelForm):

    class Meta:
        model = Document
        exclude = ['original', 'preview']

    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['original'] = forms.FilePathField(path=path)
        self.fields['preview'] = forms.FilePathField(path=path, required=False)

    def save(self, commit=True):
        document = super().save(commit=False)
        original = self.cleaned_data['original']
        original = os.path.relpath(original, settings.MEDIA_ROOT)
        document.original = original

        preview = self.cleaned_data.get('preview', None)
        if preview:
            preview = os.path.relpath(preview, settings.MEDIA_ROOT)
            document.preview = preview

        if commit:
            if not document.id:
                document.save()
            self.save_m2m()
            document.save()
        return document
