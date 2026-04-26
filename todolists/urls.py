from django.urls import path 
from .views import ToDoListView,TaskView,ToDoListAllView,TaskMarkerView,ToDoListCreateTasksView

urlpatterns = [
    # 1. Getting all lists (GET) or Creating a new list (POST)
    # This points to your View that has def get(self, request) and def post(self, request)
    path("lists/", ToDoListAllView.as_view(), name="lists-creation-or-retrieving"), 
    path("lists/tasks/", ToDoListCreateTasksView.as_view(), name="todo-list-task-creation"),
    # 2. Operations on a specific list (GET, PATCH, DELETE)
    path("lists/<int:list_id>/", ToDoListView.as_view(), name="todo-list-details"),
    path("tasks/done", TaskMarkerView.as_view(), name="tasks-checked"),


    path("tasks/", TaskView.as_view(), name="tasks-root"),

    # 4. Operations on a specific task (GET, PATCH, DELETE)
    path("tasks/<int:task_id>/", TaskView.as_view(), name="tasks-details"),
]