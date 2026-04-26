from .models import ToDoList,Task
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializer import TaskSerializer, TodoListSerializer,TodoListNestedSerializer,TaskBulkSerializer
from notes.pagination import StandardCursorPagination
from django.db.models import prefetch_related_objects


class ToDoListView(APIView): #views related to the  todolist with an  id 
    permission_classes=[IsAuthenticated]
    def patch(self,request,list_id):
        
            if list_id is not None:
                old_todo_list=ToDoList.objects.filter(id=list_id,user=request.user).first()
                if old_todo_list :
                    list_obj=TodoListSerializer(old_todo_list,data=request.data,partial=True)
                    if list_obj.is_valid():
                        list_obj.save()
                        return Response(list_obj.data,status=200)
                    else :
                        return Response({"error":list_obj.errors},status=400)
                else: 
                    return Response({"error":"List Not Found"},status=404)
            else : 
                return Response({"error":"Missing Credentials "},status=400)
        

    def get(self,request,list_id):
        
            if list_id is not None:
                
                todo_list_obj= ToDoList.objects.filter(id=list_id,user=request.user).prefetch_related("task_set").first()
                
                if todo_list_obj :    
                    return Response(TodoListNestedSerializer(todo_list_obj).data,status=200)
                else:
                    return Response({"error":"List Not Found"},status=404)
                
            else :
                return Response({"error":"Missing Credentials "},status=400)
        
    def delete(self,request,list_id):
        
            if list_id is not None:
                list_obj= ToDoList.objects.filter(id=list_id,user=request.user).first()
                if list_obj:
                    list_obj.delete()
                    return Response({},status=204)     
                else :
                    return Response({"error":"List Not Found"},status=404)

class ToDoListAllView(APIView):

    permission_classes=[IsAuthenticated]
    def post(self,request):
        
        
            list_obj=TodoListSerializer(data=request.data)
            if list_obj.is_valid():
                list_obj.save(user=request.user)
                return Response(list_obj.data,status=201)
            else:
                return Response({"error":list_obj.errors},status=400)
        
    def get(self,request):
        

            list_objs= ToDoList.objects.filter(user=request.user) ##how
            pagination=StandardCursorPagination()
            pagination_result=pagination.paginate_queryset(list_objs,request)
            prefetch_related_objects(pagination_result,"task_set")
            return pagination.get_paginated_response(TodoListNestedSerializer(pagination_result,many=True).data)
        
class ToDoListCreateTasksView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
         tasks=TaskBulkSerializer(data=request.data.get("tasks"),many=True)
         todo_list=TodoListSerializer(data=request.data.get("todo_list"))
         if todo_list.is_valid():
            todo_list=todo_list.save()
            if tasks.is_valid():
                tasks_set=[]
                for item in tasks.validated_data:
                     tasks_set.append(Task(
                        statement= item["statement"],
                        checked=item["checked"],
                        priority=item["priority"],
                        todo_list=todo_list
                     )
                          
                     )
                Task.objects.bulk_create(tasks_set,batch_size=500)
                return Response({},201)
            else :
                 return Response({},400)
              
         else:
               return Response({"Error":"Some Data Is Missing"},400)        
        
class TaskMarkerView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,request,list_id):
        list=ToDoList.objects.filter(id=list_id,user=request.user).first()
        tasks=TaskSerializer(data=request.data,many=True)
        if list:
             
            
                if tasks.is_valid():
                    tasks=tasks.validated_data
                    task_set=[]
                    for item in tasks:
                        task_set.append(item["id"])
                    tasks_real_objs=Task.objects.filter(id__in=task_set,todo_list=list)
                    for item in tasks_real_objs :
                        item.checked=True 


                    Task.objects.bulk_update(tasks_real_objs,fields=["checked"],batch_size=500)
                else:
                    return Response({"error":tasks.errors},400)
                     
              
        else :
            return Response({"error":"Object Not Found"},404)


class TaskView(APIView):
    permission_classes=[IsAuthenticated]
    

    
    def get(self,request,task_id):
        
            
            if task_id is not None:
                task_obj=Task.objects.filter(id=task_id,todo_list__user=request.user).first()
                    
                if task_obj: 
                    return Response(TaskSerializer(task_obj).data,status=200)
                else:
                    return Response({"error":"Task Not Found"},status=404)
              
            else :
                return Response({"error":"Missing Credentials"},status=400)
        
    def post(self,request):
      
            task_obj=TaskSerializer(data=request.data)

            if task_obj.is_valid():
                if ToDoList.objects.get(id=request.data.get("todo_list")).user == request.user: 
                    task_obj.save()
                    return Response(task_obj.data,status=201)
                else :
                    return Response({"error":"Forbidden Operation"},status=403)
                
            else :
                return Response({"error":task_obj.errors},status=400)
        
        
    def delete(self,request,task_id):
        
            if task_id is not None:
                
                task_obj=Task.objects.filter(id=task_id,todo_list__user=request.user).first()
                if task_obj:
                    task_obj.delete()
                    return Response({},status=204)
                else :
                    return Response({"error":"Task Not Found"},status=404)
                

            else:
                return Response({"error":"Missing Credentials "},status=400)
        
    def patch(self,request,task_id):
      
            if task_id is not None:
   
                old_task=Task.objects.filter(
                        id=task_id,
                        todo_list__user=request.user).first()
                if old_task :
                    task_obj=TaskSerializer(old_task,data=request.data,partial=True)
                    if task_obj.is_valid():
                        task_obj.save()
                        return Response(task_obj.data,status=200)
                    else :
                        return Response({"error":task_obj.errors},status=400)
                else :
                    return Response({"error":"Task Not Found "},status=404)
                     
                
            else : 
                return Response({"error":"Missing Credentials "},status=400)
        
        
        
    
# Create your views here.
