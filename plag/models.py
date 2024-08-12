
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission



class User(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    groups = models.ManyToManyField(
        Group,
        related_name='plag_users',  # Add a custom related_name
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='plag_users_permissions',  # Add a custom related_name
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='user',
    )


class PlagCheck(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    check_id = models.AutoField(primary_key=True)
    date_uploaded = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.filename} - {self.date_uploaded}'

class UsageStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.check_in} to {self.check_out}'
    

class PlagData(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    plag_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_words = models.IntegerField()
    similarity_score = models.FloatField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.id
    
