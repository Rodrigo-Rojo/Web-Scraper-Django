from django.db import models


# Create your models here.
class WebScraper(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    img = models.URLField(max_length=500)
    url = models.URLField(max_length=500)
    date = models.DateField(auto_now=True)

    def __str__(self):
        return self.title
