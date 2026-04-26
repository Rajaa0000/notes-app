"""
from django.contrib import admin
from django.urls import path,include
from notes import urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('notes/',include("notes.urls"))
]
"""
from django.urls import path
from .views import PinnedNotesView,NoteView,NoteViewAll,TitleSearchedByView
urlpatterns=[
    path("notes/<int:note_id>/",NoteView.as_view(),name="notes-all"),
    path("notes/",NoteViewAll.as_view(),name="note-detail"),
    path("notes/pinned/",PinnedNotesView.as_view(),name="notes-pinned"),
    path("notes/search/",TitleSearchedByView.as_view(),name="filtered-notes")

    ]