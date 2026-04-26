from rest_framework.pagination import CursorPagination 

class StandardCursorPagination(CursorPagination):
     page_size=2
     ordering = ('-created_at', '-id')