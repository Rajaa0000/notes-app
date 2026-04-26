from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated 
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializer import NoteSerializer
from .models import Note
from notes.pagination import StandardCursorPagination


class PinnedNotesView(APIView):
    permission_classes=[IsAuthenticated ]
    def get(self,request):
       
            user_notes=Note.objects.filter(user=request.user,is_pinned=True,is_deleted=False)
            pagination=StandardCursorPagination()
            result_page=pagination.paginate_queryset(user_notes,request)
            if result_page is not None :
                return pagination.get_paginated_response(NoteSerializer(result_page,many=True).data)
            else : 
                return Response({"error":"Page Was Not Found "},status=404) 
        
class TitleSearchedByView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        search_term=request.GET.get("term")
        user_notes=Note.objects.filter(user=request.user,is_deleted=False)
        if search_term :
            user_notes=user_notes.filter(title__icontains=search_term)
            pagination=StandardCursorPagination()
            paginated_result=pagination.paginate_queryset(user_notes,request)
            serializer=NoteSerializer(paginated_result,many=True)
            return pagination.get_paginated_response(serializer.data)
        else :
             return Response({"error":"No Term Sent"},400)

class NoteViewAll(APIView):
    permission_classes=[IsAuthenticated ]
    def get(self,request):

       
            user_notes=Note.objects.filter(user=request.user,is_deleted=False,is_pinned=False)
            pagination=StandardCursorPagination()
            result_page=pagination.paginate_queryset(user_notes,request)
            if result_page :
                return pagination.get_paginated_response(NoteSerializer(result_page,many=True).data)
            else : 
                return Response({"error":"Page Was Not Found "},status=404) 
       
        
    def post(self,request):
           
           
                serializer=NoteSerializer(data=request.data)
                
                if  serializer.is_valid():

                    serializer.save(user=request.user)
                    return Response(serializer.data,status=201)
                else:
                    return Response({"error": serializer.errors},status=400)

class NoteView(APIView):
    permission_classes=[IsAuthenticated ]

        
    def get(self,request,note_id):
       
       
            
            if note_id is not None:
                    note_obj=Note.objects.filter(id=note_id,is_deleted=False).first()
                    if note_obj :
                        if note_obj.user==request.user :
                    
                            note_obj=NoteSerializer(note_obj)
                
                            return Response(note_obj.data,status=200)
                        else:
                              return Response({"error":" Operation Forbidden"},status=403)
                        
                    else :
                         return Response({"errors":" Note Not Found "},status=404)
                         
            else :
                    return Response({"errors":"Missing Credentials"},status=400)

       
            
        
        
    def delete(self,request,note_id):
       
            
            if note_id is not None :
                    note_obj=Note.objects.filter(id=note_id,is_deleted=False).first()
                    if note_obj :
                        if note_obj.user==request.user :
                            note_obj.is_deleted=True
                            note_obj.save()
                            return Response({},status=204)
                        else :
                            return Response({"errors":"Operation Forbidden "},status=403)        
                    
                    else :
                         return Response({"errors":"Note Does not exist "},status=404)
            else :
                    return Response({"errors":"Missing Credentials or Note Not Found "},status=400)

       
            
        

    def patch(self, request,note_id):
       
            
            
            if note_id is not None:
                
                old_note = Note.objects.filter(id=note_id,is_deleted=False).first()
                
                if old_note:
                    if old_note.user==request.user :
                        serializer = NoteSerializer(old_note, data=request.data, partial=True)
                        if  serializer.is_valid():
                            serializer.save()
                            # Return 200 for updates
                            return Response(serializer.data,status=200)
                        else:
                            # Tell the user WHY it failed (e.g. title too long)
                            return Response( {"error":serializer.errors}, status=400)
                        
                        
                    else :
                        return Response({"errors":"Operation Forbidden"},status=403)
                else:
                    return Response({"error": "Note not found"}, status=404)
            else:
                return Response({"error": "Missing Credentials"}, status=400)
                
       
            





