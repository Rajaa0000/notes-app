from django.db import models
from django.contrib.auth.models import User

class ToDoList(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)
    user=models.ForeignKey(User, on_delete=models.CASCADE,blank=False,null=False)
    title=models.CharField(max_length=50)
    day=models.DateField(blank=True,null=True)
    class Meta:
        unique_together=["title","user"]
        indexes=[models.Index(fields=["user","created_at"],name="index_on_created_at")]
        
class Task(models.Model):
    statement=models.TextField(max_length=100,blank=False,null=False)
    priority=models.IntegerField(blank=False,null=False)
    checked=models.BooleanField(default=False)
    todo_list=models.ForeignKey(ToDoList,on_delete=models.CASCADE,blank=False,null=False)
    class Meta:
        unique_together=["priority","todo_list"]
        


# Create your models here.
