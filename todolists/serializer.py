from rest_framework import serializers
from .models import Task,ToDoList

#class todo_list(models.Model):
  

class TodoListSerializer(serializers.ModelSerializer):
    class Meta:
        model=ToDoList
        fields=[    
        
    "created_at",
    "user",
    "title",
    "day",
    "id"]
        read_only_fields=["user","created_at","id"]


    
class TaskBulkSerializer(serializers.ModelSerializer):
    class Meta:
        model=Task
        fields=[
           "statement",
    "priority",
    "checked",
    "todo_list",
    "id"

    ]
        read_only_fields=["id","todo_list"] 

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model=Task
        fields=[
           "statement",
    "priority",
    "checked",
    "todo_list",
    "id"

    ]
        

class TodoListNestedSerializer(serializers.ModelSerializer):
    task_set=TaskSerializer(many=True, read_only=True)
    class Meta:
        model=ToDoList
        fields=[    
        
    "date",
    "user",
    "title",
    "day",
    "id",
    "task_set"]
        read_only_fields=["user","created_at","id"]

