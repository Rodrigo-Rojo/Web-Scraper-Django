from django.db import models


# Create your models here.
class New(models.Model):
    title = models.CharField(max_length=200)
    site = models.CharField(max_length=100)
    body = models.TextField()
    img = models.URLField(max_length=500)
    url = models.URLField(max_length=500)
    date = models.DateTimeField()

    def __str__(self):
        return self.title
