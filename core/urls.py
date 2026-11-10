from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'stories', views.StoryViewSet)
router.register(r'characters', views.CharacterViewSet)
router.register(r'lore-entries', views.LoreEntryViewSet)

urlpatterns = [
    # Template views
    path('', views.story_setup_view, name='story-setup'),
    path('writer/<int:story_id>/', views.writer_view, name='writer'),
    path('writer/<int:story_id>/complete/', views.complete_story_view, name='complete-story'),
    path('writer/<int:story_id>/reopen/', views.reopen_story_view, name='reopen-story'),
    path('writer/<int:story_id>/download/', views.download_story_view, name='download-story'),
    path('tree/<int:story_id>/', views.tree_view, name='tree-view'),
    # API
    path('api/', include(router.urls)),
    path('api/scenes/generate/', views.SceneGenerateView.as_view(), name='scene-generate'),
]
