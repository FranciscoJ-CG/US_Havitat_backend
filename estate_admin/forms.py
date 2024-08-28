# estate_admin/forms.py
from django import forms

from .models import  Relationship


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


