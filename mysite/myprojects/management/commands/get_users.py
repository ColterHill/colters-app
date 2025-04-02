from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, date
import pandas as pd

class Command(BaseCommand):
    def handle(self, *args, **options):

        User = get_user_model()
        users = User.objects.all()
        print(users)

        print(date.today()-timedelta(days=3))