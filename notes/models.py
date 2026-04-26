from django.db import models
from django.contrib.auth.models import User

class Note(models.Model):
    title=models.CharField(max_length=50)
    text=models.TextField(null=False,blank=False,max_length=10000)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE,blank=False,null=False,db_index=True)
    bg_color=models.CharField(max_length=7,default="#FFFFFF")
    is_pinned=models.BooleanField(default=False)
    updated_at=models.DateTimeField(auto_now=True)
    is_deleted=models.BooleanField(default=False)
    class Meta:
        unique_together=["user","title"]
        indexes=[models.Index(fields=["user","is_deleted","created_at"],name="index_on_is_deleted")]
        
        