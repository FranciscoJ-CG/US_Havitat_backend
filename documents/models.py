# documents/models.py

from django.db import models

class Document(models.Model):
    complex = models.ForeignKey('estate_admin.Complex', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file_data = models.BinaryField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=50)

    def __str__(self):
        return self.title

