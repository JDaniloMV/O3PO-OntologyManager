from django.urls import path
from .views import (
    load_ontology_view,
    create_class_view,
    export_ontology_view,
    create_individual_view,
    relationship_manager_view, 
)

urlpatterns = [
    path('load-ontology/', load_ontology_view, name='load_ontology'),
    path('create-class/', create_class_view, name='create_class'),
    path('export-ontology/', export_ontology_view, name='export_ontology'),
    path('create-individual/', create_individual_view, name='create_individual'),
    path('relationship-manager/', relationship_manager_view, name='relationship_manager'),  
]
