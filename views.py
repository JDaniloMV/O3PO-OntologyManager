from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from owlready2 import FunctionalProperty, get_ontology, Or, And, Not, Thing, ThingClass, ObjectProperty, DataProperty, AnnotationProperty, ObjectPropertyClass, DataPropertyClass, ThingClass, Or, And, Not
from django.conf import settings
from rdflib import URIRef, Literal
import os
import traceback
import json
import types

onto_path = ""

def build_entity_hierarchy(entity):
    def get_all_subclasses(entity):
        subs = []
        for sub in sorted(entity.subclasses(), key=lambda x: x.name or ""):
            subs.append({
                'name': sub.name,
                'children': get_all_subclasses(sub)
            })
        return subs
    return {
        'name': entity.name,
        'children': get_all_subclasses(entity)
    }

def serialize_entity(entity):
    return {
        'name': entity.name,
        'iri': entity.iri,
        'comment': entity.comment.first() if entity.comment else ''
    }

def serialize_individual(ind):
    def process_value(value):
        if hasattr(value, 'name'):
            return value.name
        elif isinstance(value, (Or, And, Not)):
            return str(value)
        return str(value)

    properties_data = {}
    for prop in ind.get_properties():
        try:
            values = getattr(ind, prop.name)
            if not isinstance(values, list):
                values = [values]  # Garante que seja sempre uma lista para processamento consistente
            properties_data[prop.name] = [process_value(v) for v in values]
        except AttributeError:
            # A propriedade pode não ter sido definida para este indivíduo
            properties_data[prop.name] = []
        except Exception as e:
            print(f"Erro ao acessar propriedade '{prop.name}' de '{ind.name}': {e}")
            properties_data[prop.name] = ["ErroAoAcessar"]
    return {
        'name': ind.name,
        'type': [cls.name for cls in ind.is_a if hasattr(cls, 'name')],
        'properties': properties_data
    }

def serialize_property(prop):
    def process_entities(entities):
        processed = []
        for entity in entities:
            try:
                if isinstance(entity, ThingClass):
                    processed.append(entity.name)
                elif isinstance(entity, Or):
                    if hasattr(entity, 'Classes'):
                        classes = [c.name for c in entity.Classes if hasattr(c, 'name')]
                        processed.append(f"UnionOf({', '.join(classes)})")
                    else:
                        processed.append("InvalidUnion")
                elif isinstance(entity, And):
                    if hasattr(entity, 'Classes'):
                        classes = [c.name for c in entity.Classes if hasattr(c, 'name')]
                        processed.append(f"IntersectionOf({', '.join(classes)})")
                    else:
                        processed.append("InvalidIntersection")
                elif isinstance(entity, Not):
                    if hasattr(entity, 'Class') and entity.Class:
                        processed.append(f"ComplementOf({entity.Class.name})")
                    else:
                        processed.append("InvalidComplement")
                else:
                    processed.append(str(entity))
            except Exception as e:
                print(f"Erro ao processar entidade: {str(e)}")
                processed.append("ErroDeSerializacao")
        return processed

    subproperties = prop.subproperties() if hasattr(prop, 'subproperties') else []
    return {
        'name': prop.name,
        'domain': process_entities(getattr(prop, 'domain', [])),
        'range': process_entities(getattr(prop, 'range', [])),
        'subproperties': [subp.name for subp in subproperties]
    }

@csrf_exempt
def load_ontology_view(request):
    if request.method == 'POST':
        if 'ontology_file' not in request.FILES:
            return JsonResponse({'status': 'error', 'message': 'Nenhum arquivo enviado'}, status=400)
        try:
            ontology_file = request.FILES['ontology_file']
            media_dir = settings.MEDIA_ROOT
            if not os.path.exists(media_dir):
                os.makedirs(media_dir)
            file_path = os.path.join(media_dir, ontology_file.name)
            print("file_path:", file_path)
            with open(file_path, 'wb+') as destination:
                for chunk in ontology_file.chunks():
                    destination.write(chunk)

            global onto_path, onto 
            onto_path = file_path
            onto = get_ontology(file_path).load()

            # Obter todas as classes para o contador total
            all_classes = list(onto.classes())

            # Usando a lógica que funcionava para a árvore: seleciona as classes que possuem Thing como pai.
            # Se não houver nenhuma, usa todas as classes.
            root_classes = [cls for cls in onto.classes() if Thing in cls.is_a]
            if not root_classes:
                root_classes = all_classes

            datatypes = set()
            for prop in onto.data_properties():
                for rng in getattr(prop, 'range', []):
                    if hasattr(rng, 'name'):
                        datatypes.add(rng.name)

            # Adiciona os padrões
            datatypes.update(['xsd:string', 'xsd:integer', 'xsd:float', 'xsd:boolean', 'xsd:dateTime'])

            ontology_data = {
                'classes': [build_entity_hierarchy(cls) for cls in root_classes],
                'classes_count': len(all_classes),
                'object_properties': [serialize_property(prop) for prop in onto.object_properties()],
                'data_properties': [serialize_property(prop) for prop in onto.data_properties()],
                'annotation_properties': [serialize_property(prop) for prop in onto.annotation_properties()],
                'individuals': [serialize_individual(ind) for ind in onto.individuals()],
                'datatypes': list(datatypes)
            }

            return JsonResponse({'status': 'success', 'message': 'Ontologia carregada!', 'ontology': ontology_data})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@csrf_exempt
def create_class_view(request):
    global onto
    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            class_name = data.get('name')
            parent_names = data.get('parents', [])
            

            if not class_name:
                return JsonResponse({'status': 'error', 'message': 'Nome da classe é obrigatório'}, status=400)

            with onto:
                # Definindo classes-pai
                if parent_names:
                    parents = []
                    for parent_name in parent_names:
                        parent_cls = onto.search_one(iri="*" + parent_name)
                        if not parent_cls:
                            return JsonResponse({'status': 'error', 'message': f'Classe pai "{parent_name}" não encontrada'}, status=400)
                        parents.append(parent_cls)
                else:
                    parents = [Thing]

                # Criando a nova classe
                NewClass = types.new_class(class_name, tuple(parents))

            # Atualizar a árvore de classes
            all_classes = list(onto.classes())
            root_classes = [cls for cls in onto.classes() if Thing in cls.is_a]
            if not root_classes:
                root_classes = all_classes

            ontology_data = {
                'classes': [build_entity_hierarchy(cls) for cls in root_classes],
                'classes_count': len(all_classes)
            }

            return JsonResponse({'status': 'success', 'message': 'Classe criada com sucesso', 'ontology': ontology_data})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


@csrf_exempt
def export_ontology_view(request):
    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)

    try:
        filename = request.GET.get('filename', 'ontology.owl')
        if not filename.endswith('.owl'):
            filename += '.owl'

        export_path = os.path.join(settings.MEDIA_ROOT, filename)
        onto.save(file=export_path, format="rdfxml")

        return FileResponse(open(export_path, 'rb'), as_attachment=True, filename=filename)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def create_individual_view(request):
    global onto
    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            individual_name = data.get('name')
            class_names = data.get('classes', [])
            properties = data.get('properties', {})
            annotations = data.get('annotations', {})
            description = data.get('description', {})
            same_as = data.get('same_as', [])
            different_from = data.get('different_from', [])

            if not individual_name:
                return JsonResponse({'status': 'error', 'message': 'Nome do indivíduo é obrigatório'}, status=400)
            if not class_names:
                return JsonResponse({'status': 'error', 'message': 'Pelo menos uma classe deve ser especificada'}, status=400)

            with onto:
                # Busca e instancia classes
                classes = []
                for cls_name in class_names:
                    ontology_class = onto.search_one(iri=f"*{cls_name}") or onto.search_one(label=cls_name)
                    if not ontology_class:
                        return JsonResponse({'status': 'error', 'message': f'Classe "{cls_name}" não encontrada'}, status=400)
                    classes.append(ontology_class)

                # Cria novo indivíduo
                new_individual = classes[0](individual_name)
                if len(classes) > 1:
                    new_individual.is_a.extend(classes[1:])

                # Trata propriedades
                for prop_name, values in properties.items():
                    prop = onto.search_one(iri=f"*{prop_name}") or onto.search_one(label=prop_name)
                    if not prop:
                        print(f">>> Propriedade '{prop_name}' não encontrada!")
                        continue

                    if not isinstance(prop, DataPropertyClass):
                        return JsonResponse({'status': 'error', 'message': f'Propriedade \"{prop_name}\" não é uma DataProperty'}, status=400)

                    processed_values = []
                    for item in values:
                        value = item.get('value')
                        lang = item.get('lang')
                        datatype_uri = item.get('datatype')

                        if not value:
                            continue

                        # Define o datatype como URIRef se for fornecido
                        datatype = None
                        if datatype_uri:
                            if datatype_uri.startswith("xsd:"):
                                datatype = URIRef(f"http://www.w3.org/2001/XMLSchema#{datatype_uri[4:]}")
                            else:
                                datatype_entity = onto.search_one(iri=f"*{datatype_uri}") or onto.search_one(label=datatype_uri)
                                if datatype_entity:
                                    datatype = URIRef(datatype_entity.iri)

                        # Cria o Literal com valor, idioma e datatype
                        lit = Literal(value, lang=lang, datatype=datatype)
                        processed_values.append(str(lit))  # ou manter como lit se quiser salvar Literal puro

                    if not processed_values:
                        continue

                if isinstance(prop, FunctionalProperty):
                    setattr(new_individual, prop.name, processed_values[0])
                else:
                    current = getattr(new_individual, prop.name, None)
                    if current is None:
                        setattr(new_individual, prop.name, processed_values)
                    elif isinstance(current, list):
                        current.extend(processed_values)
                    else:
                        setattr(new_individual, prop.name, [current] + processed_values)


                # Anotações
                for anno_prop, values in annotations.items():
                    prop = onto.search_one(iri=f"*{anno_prop}") or onto.search_one(label=anno_prop)
                    if not prop:
                        print(f">>> Annotation property '{anno_prop}' não encontrada!")
                        continue
                    for value in values:
                        new_individual.annotate(prop, value)

                # Descrição extra
                for extra_type in description.get('types', []):
                    cls = onto.search_one(iri=f"*{extra_type}") or onto.search_one(label=extra_type)
                    if cls:
                        new_individual.is_a.append(cls)

                # SameAs e DifferentFrom
                for same in same_as:
                    other_ind = onto.search_one(iri=f"*{same}") or onto.search_one(label=same)
                    if other_ind:
                        new_individual.same_as.append(other_ind)

                for diff in different_from:
                    other_ind = onto.search_one(iri=f"*{diff}") or onto.search_one(label=diff)
                    if other_ind:
                        new_individual.different_from.append(other_ind)

                # Salva alterações
                onto.save(file=onto_path, format="rdfxml")

            # Serializa resposta
            return JsonResponse({
                'status': 'success',
                'message': 'Indivíduo criado!',
                'ontology': {
                    'individuals': [serialize_individual(ind) for ind in onto.individuals()]
                }
            })

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@csrf_exempt
def list_data_properties_view(request):
    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)

    try:
        data_properties = [
            serialize_property(prop) for prop in onto.data_properties()
        ]
        return JsonResponse({'status': 'success', 'data_properties': data_properties})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def relationship_manager_view(request):
    global onto
    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        subject_name = data.get('subject')
        object_property_name = data.get('object_property')
        target_name = data.get('target')
        action = data.get('action')
        replace_with_name = data.get('replace_with')

        if not subject_name or not object_property_name or not action:
            return JsonResponse({'status': 'error', 'message': 'Parâmetros obrigatórios ausentes'}, status=400)

        with onto:
            # Localiza indivíduos e propriedade
            subject = onto.search_one(iri=f"*{subject_name}") or onto.search_one(label=subject_name)
            if not subject:
                return JsonResponse({'status': 'error', 'message': f'Indivíduo sujeito "{subject_name}" não encontrado'}, status=404)

            obj_prop = onto.search_one(iri=f"*{object_property_name}") or onto.search_one(label=object_property_name)
            if not obj_prop or not isinstance(obj_prop, ObjectPropertyClass):
                return JsonResponse({'status': 'error', 'message': f'Propriedade "{object_property_name}" não encontrada ou não é uma ObjectProperty'}, status=400)

            if action == 'add':
                target = onto.search_one(iri=f"*{target_name}") or onto.search_one(label=target_name)
                if not target:
                    return JsonResponse({'status': 'error', 'message': f'Indivíduo destino "{target_name}" não encontrado'}, status=404)
                getattr(subject, obj_prop.name).append(target)

            elif action == 'remove':
                target = onto.search_one(iri=f"*{target_name}") or onto.search_one(label=target_name)
                if not target:
                    return JsonResponse({'status': 'error', 'message': f'Indivíduo destino "{target_name}" não encontrado'}, status=404)
                current_values = getattr(subject, obj_prop.name)
                if target in current_values:
                    current_values.remove(target)
                else:
                    return JsonResponse({'status': 'error', 'message': f'Relação não encontrada entre "{subject_name}" e "{target_name}" via "{object_property_name}"'}, status=404)

            elif action == 'replace':
                if not replace_with_name:
                    return JsonResponse({'status': 'error', 'message': 'Parâmetro "replace_with" obrigatório para ação replace'}, status=400)
                old_target = onto.search_one(iri=f"*{target_name}") or onto.search_one(label=target_name)
                new_target = onto.search_one(iri=f"*{replace_with_name}") or onto.search_one(label=replace_with_name)
                if not old_target or not new_target:
                    return JsonResponse({'status': 'error', 'message': 'Indivíduos de origem ou destino não encontrados'}, status=404)
                current_values = getattr(subject, obj_prop.name)
                if old_target in current_values:
                    current_values.remove(old_target)
                    current_values.append(new_target)
                else:
                    return JsonResponse({'status': 'error', 'message': f'Relação original não encontrada entre "{subject_name}" e "{target_name}"'}, status=404)

            else:
                return JsonResponse({'status': 'error', 'message': 'Ação inválida. Use "add", "remove" ou "replace"'}, status=400)

            # Salva alterações
            onto.save(file=onto_path, format="rdfxml")

        # Atualiza lista de indivíduos na resposta
        updated_individuals = [serialize_individual(ind) for ind in onto.individuals()]

        return JsonResponse({'status': 'success', 'message': 'Relacionamento atualizado com sucesso!', 'ontology': {'individuals': updated_individuals}})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
