from rest_framework import serializers
from .models import Note

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Note
        fields = [
    "title",
    "text",
    "bg_color",
    "is_pinned",
     "id",
     "created_at",
     "updated_at"
   
]
        read_only_fields=["id","created_at","updated_at"]
        