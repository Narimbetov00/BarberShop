from django.db import models

# Create your models here.
class Client(models.Model):
    chat_id = models.IntegerField()
    username_tg = models.URLField()
    phone = models.CharField(max_length=20,null=True,blank=True)
    queue = models.IntegerField()
    time_is_up = models.DateTimeField()
    price = models.DecimalField(max_digits=12,decimal_places=2,blank=True,null=True)
    if_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_finished = models.BooleanField(default=False)

