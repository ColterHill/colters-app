from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ringcentral_jwt_code = models.TextField(null=True, blank=True)
    sf_user_id = models.CharField(null=True, blank=True, max_length=19)
    rep_ringcentral_number = models.CharField(null=True, blank=True, max_length=10)

    def __str__(self):
        return self.user.username