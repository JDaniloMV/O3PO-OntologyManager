from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from owlready2 import FunctionalProperty, get_ontology, Or, And, Not, Thing, ThingClass, ObjectPropertyClass, DataPropertyClass, AnnotationPropertyClass, DataProperty
from owlready2 import ObjectPropertyClass as ObjectProperty 
from django.conf import settings
from owlready2 import World
from owlready2 import *
import os
import traceback
import json
import types
import logging
logger = logging.getLogger(__name__)
from owlready2 import (
    get_ontology, Thing, types, ObjectPropertyClass, DataPropertyClass,
    AnnotationPropertyClass, FunctionalProperty, InverseFunctionalProperty,
    TransitiveProperty, SymmetricProperty, AsymmetricProperty,
    ReflexiveProperty, IrreflexiveProperty
)

world = World()

onto_path = ""
onto = None

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
                values = [values]
            properties_data[prop.name] = [process_value(v) for v in values]
        except AttributeError:
            properties_data[prop.name] = []
        except Exception:
            properties_data[prop.name] = ["ErroAoAcessar"]
    return {
        'name': ind.name,
        'type': [cls.name for cls in ind.is_a if hasattr(cls, 'name')],
        'properties': properties_data
    }


def serialize_property(prop):
    try:
        from owlready2 import And, Or, FunctionalProperty, TransitiveProperty, SymmetricProperty, ObjectProperty

        # Helper para extrair nomes de classes de expressões lógicas (And/Or)
        def extract_classes(item):
            if isinstance(item, (And, Or)):
                return [extract_classes(c) for c in item.Classes]
            elif hasattr(item, 'name'):
                return item.name
            else:
                return str(item)

        # Converter IRI para string e garantir valores padrão
        prop_data = {
            'name': getattr(prop, 'name', ''),
            'iri': str(getattr(prop, 'iri', '')),
            'domain': [],
            'range': [],
            'is_functional': False,
            'is_transitive': False,
            'is_symmetric': False,
            'error': None
        }

        # Verificar se é uma propriedade de objeto
        if not isinstance(prop, ObjectProperty):
            prop_data['error'] = 'Tipo de propriedade não suportado'
            return prop_data

        # Processar domínio
        domain = getattr(prop, 'domain', [])
        if not isinstance(domain, list):
            domain = [domain]
        prop_data['domain'] = [extract_classes(item) for item in domain]

        # Processar range
        prop_range = getattr(prop, 'range', [])
        if not isinstance(prop_range, list):
            prop_range = [prop_range]
        prop_data['range'] = [extract_classes(item) for item in prop_range]

        # Verificar características especiais
        prop_data['is_functional'] = isinstance(prop, FunctionalProperty)
        prop_data['is_transitive'] = isinstance(prop, TransitiveProperty)
        prop_data['is_symmetric'] = isinstance(prop, SymmetricProperty)

        return prop_data

    except Exception as e:
        # Log detalhado para debug
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro serializando propriedade {prop}: {str(e)}", exc_info=True)
        
        return {
            'name': getattr(prop, 'name', 'ErroDesconhecido'),
            'error': str(e)
        }
    

@csrf_exempt
def load_ontology_view(request):
    global world, onto, onto_path
    if request.method == 'POST':
        if 'ontology_file' not in request.FILES:
            return JsonResponse({'status': 'error', 'message': 'Nenhum arquivo enviado'}, status=400)
        try:
            logger.info(f"[LOAD] onto id: {id(onto)}, onto_path: {onto_path!r}")
            file = request.FILES['ontology_file']
            media_dir = settings.MEDIA_ROOT
            os.makedirs(media_dir, exist_ok=True)
            path = os.path.join(media_dir, file.name)
            with open(path, 'wb+') as dest:
                for chunk in file.chunks(): dest.write(chunk)

            onto_path = path
            onto = get_ontology(path).load()

            all_classes = list(onto.classes())
            roots = [c for c in onto.classes() if Thing in c.is_a] or all_classes

            datatypes = {rng.name for p in onto.data_properties() for rng in getattr(p, 'range', []) if hasattr(rng, 'name')}
            datatypes |= {'xsd:string','xsd:integer','xsd:float','xsd:boolean','xsd:dateTime'}

            data = {
                'classes': [build_entity_hierarchy(c) for c in roots],
                'classes_count': len(all_classes),
                'object_properties': [serialize_property(p) for p in onto.object_properties()],
                'data_properties': [serialize_property(p) for p in onto.data_properties()],
                'annotation_properties': [serialize_property(p) for p in onto.annotation_properties()],
                'individuals': [serialize_individual(i) for i in onto.individuals()],
                'datatypes': list(datatypes)
            }
            return JsonResponse({'status':'success','message':'Ontologia carregada!','ontology':data})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'status':'error','message':str(e)}, status=400)
    return JsonResponse({'status':'error','message':'Método não permitido'}, status=405)

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
def create_annotation_property_view(request):
    global onto
    if onto is None: return JsonResponse({'status':'error','message':'Nenhuma ontologia carregada'},status=400)
    if request.method!='POST': return JsonResponse({'status':'error','message':'Método não permitido'},status=405)
    try:
        data=json.loads(request.body)
        name, domains = data.get('name'), data.get('domain',[])
        if not name: return JsonResponse({'status':'error','message':'Nome é obrigatório'},status=400)
        with onto:
            New = types.new_class(name, (AnnotationPropertyClass,))
            New.namespace = onto
            if domains:
                New.domain = [d for d in domains if d]

            onto.save(file=onto_path, format="rdfxml")
            onto = get_ontology(onto_path).load()
        return JsonResponse({'status':'success','message':'AnnotationProperty criada','annotation_properties':[serialize_property(p) for p in onto.annotation_properties()]})
    except Exception as e:
        traceback.print_exc(); return JsonResponse({'status':'error','message':str(e)},status=500)

@csrf_exempt
def create_individual_view(request):
    global onto
    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)
    try:
        data = json.loads(request.body)
        individual_name = data.get('name')
        class_names = data.get('classes', [])
        properties = data.get('properties', {})
        annotations = data.get('annotations', {})
        obj_props = data.get('object_properties', {})
        description = data.get('description', {})
        same_as = data.get('same_as', [])
        different_from = data.get('different_from', [])

        if not individual_name:
            return JsonResponse({'status': 'error', 'message': 'Nome do indivíduo é obrigatório'}, status=400)
        if not class_names:
            return JsonResponse({'status': 'error', 'message': 'Pelo menos uma classe deve ser especificada'}, status=400)

        with onto:
            # instantiate classes
            classes = []
            for cls_name in class_names:
                ontology_class = onto.search_one(iri=f"*{cls_name}") or onto.search_one(label=cls_name)
                if not ontology_class:
                    return JsonResponse({'status': 'error', 'message': f'Classe "{cls_name}" não encontrada'}, status=400)
                classes.append(ontology_class)

            # create individual
            new_individual = classes[0](individual_name)
            if len(classes) > 1:
                new_individual.is_a.extend(classes[1:])

            # data properties
            for prop_name, values in properties.items():
                prop = onto.search_one(iri=f"*{prop_name}") or onto.search_one(label=prop_name)
                if not prop or not isinstance(prop, DataPropertyClass):
                    continue
                # Process values into Python native types instead of rdflib Literals
                processed = []
                for item in values:
                    val = item.get('value')
                    lang = item.get('lang')
                    dt_uri = item.get('datatype')
                    if val is None:
                        continue
                    # Convert to Python type based on datatype
                    if dt_uri and dt_uri.startswith('xsd:'):
                        t = dt_uri[4:]
                        try:
                            if t in ('integer', 'int'):
                                py_val = int(val)
                            elif t in ('float', 'double', 'decimal'):
                                py_val = float(val)
                            elif t in ('boolean',):
                                py_val = val.lower() in ('true', '1')
                            else:
                                py_val = val
                        except Exception:
                            py_val = val
                    else:
                        py_val = val
                    processed.append(py_val)
                # Assign to the individual
                if isinstance(prop, FunctionalProperty) and processed:
                    setattr(new_individual, prop.name, processed[0])
                else:
                    for v in processed:
                        getattr(new_individual, prop.name).append(v)

            # object properties
            for prop_name, targets in obj_props.items():
                prop = onto.search_one(iri=f"*{prop_name}") or onto.search_one(label=prop_name)
                if not prop or not isinstance(prop, ObjectPropertyClass):
                    continue
                for t in targets:
                    target_ind = onto.search_one(iri=f"*{t}") or onto.search_one(label=t)
                    if target_ind:
                        getattr(new_individual, prop.name).append(target_ind)

            # annotations
            for anno_name, values in annotations.items():
                prop = onto.search_one(iri=f"*{anno_name}") or onto.search_one(label=anno_name)
                if not prop or not isinstance(prop, AnnotationPropertyClass):
                    continue
                for v in values:
                    prop[new_individual].append(v)

            # description, same_as, different_from
            for extra in description.get('types', []):
                cls = onto.search_one(iri=f"*{extra}") or onto.search_one(label=extra)
                if cls:
                    new_individual.is_a.append(cls)
            for same in same_as:
                other = onto.search_one(iri=f"*{same}") or onto.search_one(label=same)
                if other:
                    new_individual.same_as.append(other)
            for diff in different_from:
                other = onto.search_one(iri=f"*{diff}") or onto.search_one(label=diff)
                if other:
                    new_individual.different_from.append(other)

            onto.save(file=onto_path, format="rdfxml")

        return JsonResponse({
            'status': 'success',
            'message': 'Indivíduo criado!',
            'ontology': {'individuals': [serialize_individual(i) for i in onto.individuals()]}
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

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
def list_object_properties_view(request):
    """
    GET: retorna todas as ObjectProperties definidas na ontologia,
         com domínio e range (se houver).
    """
    global onto
    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)

    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

    try:
        props = []
        for prop in onto.object_properties():
            # domínio e range podem ser listas vazias
            domains = [cls.name for cls in getattr(prop, "domain", [])]
            ranges  = [cls.name for cls in getattr(prop, "range",  [])]
            props.append({
                'name':       prop.name,
                'iri':        prop.iri,
                'label':      prop.label.first() or None,
                'domain':     domains,
                'range':      ranges,
                'is_functional': isinstance(prop, ObjectPropertyClass) and prop.is_functional,
            })

        return JsonResponse({
            'status':            'success',
            'object_properties': props
        })

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


import json
import traceback
import types
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from owlready2 import And, ObjectProperty, FunctionalProperty, TransitiveProperty, SymmetricProperty
from types import new_class

@csrf_exempt
def create_object_property_view(request):
    global onto, onto_path

    if onto is None and onto_path:
        onto = get_ontology(onto_path).load()

    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)

    try:
        data = json.loads(request.body)
        name = data.get('property_name')
        domain_names = data.get('domain', [])
        range_names = data.get('range', [])
        characteristics = data.get('characteristics', [])

        if not name:
            return JsonResponse({'status': 'error', 'message': 'Nome é obrigatório'}, status=400)

        # Busca por classes de domínio
        domains = []
        for domain_name in domain_names:
            cls = onto.search_one(iri=f"*{domain_name}") or onto.search_one(label=domain_name)
            if not cls:
                return JsonResponse({'status': 'error', 'message': f'Domínio "{domain_name}" não encontrado'}, status=400)
            domains.append(cls)

        # Busca por classes de range
        ranges = []
        for range_name in range_names:
            cls = onto.search_one(iri=f"*{range_name}") or onto.search_one(label=range_name)
            if not cls:
                return JsonResponse({'status': 'error', 'message': f'Range "{range_name}" não encontrado'}, status=400)
            ranges.append(cls)

        with onto:
            # Criação da nova propriedade seguindo padrão Owlready2
            NewProperty = new_class(name, (ObjectProperty,))
            NewProperty.namespace = onto

            # Define domínio
            if domains:
                NewProperty.domain = domains if len(domains) == 1 else [And(domains)]

            # Define range
            if ranges:
                NewProperty.range = ranges if len(ranges) == 1 else [And(ranges)]

            # Define características
            if 'functional' in [c.lower() for c in characteristics]:
                NewProperty.is_a.append(FunctionalProperty)
            if 'transitive' in [c.lower() for c in characteristics]:
                NewProperty.is_a.append(TransitiveProperty)
            if 'symmetric' in [c.lower() for c in characteristics]:
                NewProperty.is_a.append(SymmetricProperty)

            # Salva a ontologia atualizada
            onto.save(file=onto_path, format="rdfxml")

        # Retorna a lista atualizada
        object_properties = [serialize_property(p) for p in onto.object_properties()]
        return JsonResponse({
            'status': 'success',
            'message': 'Propriedade criada com sucesso',
            'object_properties': object_properties
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

import json
import datetime
import traceback
import types
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from owlready2 import get_ontology, DataProperty, FunctionalProperty, And, normstr, locstr

@csrf_exempt
def create_data_property_view(request):
    global onto, onto_path

    # Carrega ontologia se ainda não estiver em memória
    if onto is None and onto_path:
        onto = get_ontology(onto_path).load()

    if onto is None:
        return JsonResponse({'status': 'error', 'message': 'Nenhuma ontologia carregada'}, status=400)

    try:
        data = json.loads(request.body)
        name = data.get('property_name')
        domain_names = data.get('domain', [])
        data_type_str = data.get('range')  # ex: "str", "int", "xsd:float", etc.
        characteristics = data.get('characteristics', [])

        if not name:
            return JsonResponse({'status': 'error', 'message': 'Nome é obrigatório'}, status=400)
        if not data_type_str:
            return JsonResponse({'status': 'error', 'message': 'Tipo de dado (range) é obrigatório'}, status=400)

        # Mapeamento dos tipos de dados para OwlReady2 (tipos Python nativos)
        type_map = {
            'str': str,
            'normstr': normstr,
            'locstr': locstr,
            'int': int,
            'float': float,
            'bool': bool,
            'date': datetime.date,
            'time': datetime.time,
            'datetime': datetime.datetime,
        }

        # Normaliza chave, removendo prefixo xsd: se presente
        key = data_type_str.lower()
        if key.startswith('xsd:'):
            key = key.split(':', 1)[1]

        data_type = type_map.get(key)
        if data_type is None:
            return JsonResponse({'status': 'error', 'message': f'Tipo de dado "{data_type_str}" não suportado'}, status=400)

        # Busca por classes de domínio
        domains = []
        for domain_name in domain_names:
            cls = onto.search_one(iri=f"*{domain_name}") or onto.search_one(label=domain_name)
            if not cls:
                return JsonResponse({'status': 'error', 'message': f'Domínio "{domain_name}" não encontrado'}, status=400)
            domains.append(cls)

        with onto:
            # Criação da nova propriedade usando types.new_class
            NewDataProp = types.new_class(name, (DataProperty,))
            NewDataProp.namespace = onto

            # Define domínio
            if domains:
                NewDataProp.domain = domains if len(domains) == 1 else [And(domains)]

            # Define range como tipo primitivo
            NewDataProp.range = [data_type]

            # Define características (functional)
            if any(c.lower() == 'functional' for c in characteristics):
                NewDataProp.is_a.append(FunctionalProperty)

            # Salva a ontologia atualizada
            onto.save(file=onto_path, format='rdfxml')

        return JsonResponse({'status': 'success', 'message': 'Propriedade de dados criada com sucesso'})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
