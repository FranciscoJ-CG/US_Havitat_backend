# estate_admin/forms.py
from django import forms

from .models import  Relationship, ComplexImage


class RelationshipForm(forms.ModelForm):
    class Meta:
        model = Relationship
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.current_user.is_superuser:
            
            if self.is_havitat_admin:
                self.fields['role'].choices = [
                    (None, '---------')] + [
                    choice for choice in self.fields['role'].choices if choice[0] == 'estate_admin'
                ]
            else:
                # User is complex admin
                self.fields['role'].choices = [
                    choice for choice in self.fields['role'].choices if choice[0] != 'estate_admin'
                ]

        # Dynamically show or hide 'other_role' field based on 'role' field selection
        self.fields['role'].widget.attrs.update({
            'onchange': """
                if (this.value == 'other') {
                    document.getElementById('id_other_role').style.display = 'block';
                } else {
                    document.getElementById('id_other_role').style.display = 'none';
                }
            """
        })


class ComplexImageForm(forms.ModelForm):
    image_upload = forms.ImageField(required=True, label="Upload Image")

    class Meta:
        model = ComplexImage
        fields = ['complex', 'image_upload']

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.cleaned_data.get('image_upload')
        if uploaded_file:
            instance.image_data = uploaded_file.read()
        if commit:
            instance.save()
        return instance

