from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class YamlLog(models.Model):
    input_data = models.TextField()
    yaml_objects = models.JSONField()
    created = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="yaml_logs")
    output = models.TextField()
    namespace = models.CharField(max_length=255, default='default')
