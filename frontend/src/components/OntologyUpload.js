
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiUpload, FiFile, FiFolder, FiChevronRight, FiChevronDown, FiSearch, FiGrid, FiList, FiTag, FiUser } from 'react-icons/fi';
import './OntologyTree.css';


const OntologyUpload = () => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [ontologyData, setOntologyData] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredHierarchy, setFilteredHierarchy] = useState([]);
  const [activeTab, setActiveTab] = useState('classes');
  const [showCreateClassForm, setShowCreateClassForm] = useState(false);
  const [newClassName, setNewClassName] = useState('');
  const [selectedParents, setSelectedParents] = useState([]);
  const [exportFileName, setExportFileName] = useState('ontology.owl');
  const [showCreateIndividualForm, setShowCreateIndividualForm] = useState(false);
  const [newIndividualName, setNewIndividualName] = useState('');
  const [selectedIndividualClasses, setSelectedIndividualClasses] = useState([]);
  const [individualProperties, setIndividualProperties] = useState([]);
  const [newObjPropName, setNewObjPropName] = useState('');
  const [objDomain, setObjDomain] = useState([]);
  const [objRange, setObjRange] = useState([]);
  const [showCreateAnnoPropForm, setShowCreateAnnoPropForm] = useState(false);
  const [newAnnoPropName, setNewAnnoPropName] = useState('');
  const [annoDomain, setAnnoDomain] = useState([]);
  const [individualAnnotations, setIndividualAnnotations] = useState([]);
  const [objCharacteristics, setObjCharacteristics] = useState([]);
  const [objInverseOf, setObjInverseOf] = useState('');
  const [objSubProperties, setObjSubProperties] = useState([]);
  const [objEquivalents, setObjEquivalents] = useState([]);
  const [objDisjoints, setObjDisjoints] = useState([]);
  // New state for object property form
  const [showObjectPropertyForm, setShowObjectPropertyForm] = useState(false);

  // States for DataProperty form
  const [showDataPropForm, setShowDataPropForm] = useState(false);
  const [newDataPropName, setNewDataPropName] = useState('');
  const [dataDomain, setDataDomain] = useState([]);
  const [dataRangeType, setDataRangeType] = useState('');
  const [dataCharacteristics, setDataCharacteristics] = useState([]);

  const handleExportOntology = () => {
    if (!ontologyData) {
      setMessage('❌ Nenhuma ontologia carregada!');
      return;
    }
  
    const fileName = exportFileName.endsWith('.owl') ? exportFileName : `${exportFileName}.owl`;
    const exportUrl = `http://localhost:8000/export-ontology/?filename=${encodeURIComponent(fileName)}`;
  
    window.open(exportUrl, '_blank');
    setMessage(`✅ Ontologia exportada como ${fileName}`);
    setTimeout(() => setMessage(''), 3000);
  };

  // Função para filtrar a hierarquia
  const filterHierarchy = (nodes, term) => {
    return nodes.map(node => {
      const isMatch = node.name.toLowerCase().includes(term.toLowerCase());
      const childrenMatches = node.children ? filterHierarchy(node.children, term) : [];
      
      return {
        ...node,
        isMatch,
        filteredChildren: childrenMatches,
        _show: isMatch || childrenMatches.length > 0
      };
    }).filter(node => node._show);
  };

    // Efeito para atualizar a hierarquia filtrada
    useEffect(() => {
      if (!ontologyData?.classes) return;
    
      if (searchTerm) {
        // Para cada raiz, filtra e depois junta os resultados em um único array.
        const filteredRoots = ontologyData.classes.map(root => filterHierarchy([root], searchTerm)).flat();
        setFilteredHierarchy(filteredRoots);
    
        // Expandir os pais dos nós filtrados:
        const expandParents = (nodes) => {
          nodes.forEach(node => {
            if (node.filteredChildren?.length > 0) {
              setExpandedNodes(prev => new Set(prev).add(node.name));
              // Aqui recorre nos filhos filtrados para expandir ainda mais
              expandParents(node.filteredChildren);
            }
          });
        };
        expandParents(filteredRoots);
      } else {
        setFilteredHierarchy(ontologyData.classes);
      }
    }, [searchTerm, ontologyData?.classes]);
    
  const toggleNode = (nodeName) => {
    const newExpanded = new Set(expandedNodes);
    newExpanded.has(nodeName) ? newExpanded.delete(nodeName) : newExpanded.add(nodeName);
    setExpandedNodes(newExpanded);
  };

  const handlePropertyChange = (index, field, value) => {
    const newProperties = [...individualProperties];
    newProperties[index][field] = value;
    setIndividualProperties(newProperties);
  };
  
  const removeProperty = (index) => {
    setIndividualProperties(individualProperties.filter((_, i) => i !== index));
  };
  
  const handleCreateIndividual = async () => {
    try {
        const propertiesDict = individualProperties.reduce((acc, prop) => {
          if (prop.name && prop.value) {
            if (!acc[prop.name]) acc[prop.name] = [];
            acc[prop.name].push({
              value: prop.value,
              lang: prop.lang || null,
              datatype: prop.datatype || null
            });
          }
          return acc;
        }, {});
  
        const response = await axios.post('http://localhost:8000/create-individual/', {
          name: newIndividualName,
          classes: selectedIndividualClasses,
          properties: propertiesDict,
          annotations: individualAnnotations.reduce((acc, a) => {
            if (!acc[a.name]) acc[a.name] = [];
            acc[a.name].push(a.value);
            return acc;
          }, {}),
          object_properties: {}   
        });
  
      if (response.data.status === 'success') {
        setOntologyData(prev => ({
          ...prev,
          individuals: response.data.ontology.individuals
        }));
        setShowCreateIndividualForm(false);
        setMessage(`✅ ${response.data.message}`);
      }
    } catch (error) {
      setMessage(`❌ Erro: ${error.response?.data?.message || error.message}`);
    }
  };

  const renderNode = (currentNode, currentLevel = 0) => {
    // Variáveis calculadas corretamente a partir do nó atual
    const hasChildren = (currentNode.children?.length || 0) > 0;
    const isExpanded = expandedNodes.has(currentNode.name);
    const isMatch = currentNode.name.toLowerCase().includes(searchTerm.toLowerCase());
    
    return (
      <li key={currentNode.name} className="tree-node">
        <div
          className={`node-content ${hasChildren ? 'has-children' : ''} ${isMatch ? 'search-match' : ''}`}
          style={{ marginLeft: `${currentLevel * 20}px` }}
          onClick={() => hasChildren && toggleNode(currentNode.name)}
        >
          <div className="node-icons">
            {hasChildren && (
              <span className="toggle-icon">
                {isExpanded ? <FiChevronDown /> : <FiChevronRight />}
              </span>
            )}
            {hasChildren ? (
              <FiFolder className="node-icon" />
            ) : (
              <FiFile className="node-icon" />
            )}
          </div>
          <span className="node-label">
            {searchTerm && isMatch ? (
              <mark>{currentNode.name}</mark>
            ) : (
              currentNode.name
            )}
          </span>
        </div>
        
        {hasChildren && isExpanded && (
          <ul>
            {(searchTerm ? currentNode.filteredChildren : currentNode.children)?.map(childNode => (
              renderNode(childNode, currentLevel + 1) // Passagem correta de parâmetros
            ))}
          </ul>
        )}
      </li>
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setMessage('Selecione um arquivo .owl primeiro!');
      return;
    }

    const formData = new FormData();
    formData.append('ontology_file', file);

    try {
      const response = await axios.post('http://localhost:8000/load-ontology/', formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-Requested-With': 'XMLHttpRequest',
        }
      });
      
      setMessage(`✅ ${response.data.message}`);
      setOntologyData(response.data.ontology);
      setExpandedNodes(new Set());
    } catch (error) {
      setMessage(`❌ Erro: ${error.response?.data?.message || error.message}`);
    }
  };

  const flattenClasses = (nodes) => {
    let flatList = [];
    nodes.forEach(node => {
      flatList.push({ name: node.name });
      if (node.children && node.children.length > 0) {
        flatList = flatList.concat(flattenClasses(node.children));
      }
    });
    return flatList;
  };

  const handleCreateClass = async () => {
    if (!newClassName) {
      alert('Informe o nome da nova classe!');
      return;
    }

    try {
      const response = await axios.post('http://localhost:8000/create-class/', {
        name: newClassName,
        parents: selectedParents
      }, {
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.data.status === 'success') {
        setOntologyData(prev => ({
          ...prev,
          classes: response.data.ontology.classes,
          classes_count: response.data.ontology.classes_count
        }));
        setShowCreateClassForm(false);
        setNewClassName('');
        setSelectedParents([]);
        setExpandedNodes(new Set()); 
        setMessage(`✅ ${response.data.message}`);
      } else {
        alert(response.data.message);
      }
    } catch (error) {
      alert(`Erro ao criar classe: ${error.response?.data?.message || error.message}`);
    }
  };

  const handleManageRelationship = async (subject, objectProperty, target, action, replaceWith = null) => {
    try {
      const response = await axios.post('http://localhost:8000/relationship-manager/', { subject, object_property: objectProperty, target, action, replace_with: replaceWith });
      if (response.data.status === 'success') setOntologyData(prev=>({ ...prev, individuals: response.data.ontology.individuals }));
      setMessage(response.data.status==='success'?`✅ ${response.data.message}`:`❌ ${response.data.message}`);
    } catch (error) { setMessage(`❌ Erro: ${error.response?.data?.message || error.message}`); }
  };

  // Updated PropertiesList
  const PropertiesList = ({ properties, type }) => (
    <div className="properties-container">
      {properties?.length > 0 ? (
        properties.map(prop => (
          <div key={prop.name} className="property-card">
            <h4>{prop.label || prop.name}</h4>
            <div className="property-meta">
              <span><strong>Nome:</strong> {prop.name}</span>
              <span><strong>IRI:</strong> {prop.iri || '-'}</span>
  
              {(type === 'object' || type === 'data') && (
                <>
                  <span><strong>Domain:</strong> {Array.isArray(prop.domain) ? prop.domain.join(', ') : (prop.domain || 'any')}</span>
                  <span><strong>Range:</strong> {Array.isArray(prop.range) ? prop.range.join(', ') : (prop.range || 'any')}</span>
                </>
              )}
  
              {type === 'annotation' && (
                <span><strong>Domain:</strong> {Array.isArray(prop.domain) ? prop.domain.join(', ') : (prop.domain || 'any')}</span>
              )}
  
              {typeof prop.is_functional === 'boolean' && (
                <span><strong>Funcional:</strong> {prop.is_functional ? 'Sim' : 'Não'}</span>
              )}
            </div>
          </div>
        ))
      ) : (
        <p>Nenhuma propriedade encontrada.</p>
      )}
    </div>
  );  

  const handleCreateObjectProperty = async () => {
    if (!newObjPropName || !objDomain[0] || !objRange[0]) {
      alert("Todos os campos são obrigatórios.");
      return;
    }
  

    // Normaliza nomes (ex: "b" → "B")
    const normalizedDomain = objDomain[0].trim().replace(/ /g, '');
    const normalizedRange = objRange[0].trim().replace(/ /g, '');
  
    try {
      const response = await fetch('/create_object_property/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          property_name: newObjPropName,
          domain: [normalizedDomain], // Array com valor normalizado
          range: [normalizedRange]    // Array com valor normalizado
        })
      });
  
      const result = await response.json();
      if (result.status === 'success') {
        alert("Propriedade criada com sucesso!");
        setOntologyData(prev => ({
          ...prev,
          object_properties: result.object_properties
        }));
        setShowObjectPropertyForm(false);
        setNewObjPropName('');
        setObjDomain(['']);
        setObjRange(['']);
      } else {
        alert("Erro: " + result.message);
      }
    } catch (error) {
      console.error("Erro ao criar propriedade:", error);
      alert("Erro de rede ou servidor.");
    }
  };
  

  const handleCreateDataProperty = async () => {
    if (!newDataPropName || !dataRangeType) {
      alert('Nome e tipo de dado são obrigatórios.');
      return;
    }
    try {
      const payload = {
        property_name: newDataPropName.trim(),
        domain: dataDomain,
        range: dataRangeType,
        characteristics: dataCharacteristics
      };
      const response = await axios.post(
        '/create_data_property/',   
        payload,
        { headers: { 'Content-Type': 'application/json' } }
      );
      if (response.data.status === 'success') {
        setOntologyData(prev => ({
          ...prev,
          data_properties: response.data.data_properties
        }));
        setShowDataPropForm(false);
        setNewDataPropName('');
        setDataDomain([]);
        setDataRangeType('');
        setDataCharacteristics([]);
        setMessage(`✅ ${response.data.message}`);
      } else {
        alert('Erro: ' + response.data.message);
      }
    } catch (error) {
      console.error(error);
      alert('Erro ao criar DataProperty: ' + (error.response?.data?.message || error.message));
    }
  };


  const handleCreateAnnotationProperty = async () => {
    if (!newAnnoPropName) return alert('Informe o nome da AnnotationProperty');
    try {
      const res = await axios.post('http://localhost:8000/create-annotation-property/', {
        name: newAnnoPropName,
        domain: annoDomain
      });
      if(res.data.status==='success'){
        setOntologyData(prev=>({ ...prev, annotation_properties: res.data.annotation_properties }));
        setShowCreateAnnoPropForm(false);
        setNewAnnoPropName(''); setAnnoDomain([]);
        setMessage(`✅ ${res.data.message}`);
      } else alert(res.data.message);
    } catch(e){ alert(`Erro: ${e.response?.data?.message||e.message}`); }
  };

  // Object Property Form Component
// Object Property Form Component
const ObjectPropertyForm = () => (
  <div className="create-property-form" style={{ 
    padding: '1rem',
    margin: '1rem 0',
    border: '1px solid #ddd',
    borderRadius: '5px',
    backgroundColor: '#f9f9f9'
  }}>
    <h3>Criar Nova Object Property</h3>
    
    <div className="form-group" style={{ marginBottom: '1rem' }}>
      <label style={{ display: 'block', marginBottom: '0.5rem' }}>Nome da Propriedade:</label>
      <input
        type="text"
        value={newObjPropName}
        onChange={(e) => setNewObjPropName(e.target.value)}
        placeholder="Nome da propriedade"
        className="form-input"
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
      />
    </div>
    
    <div className="form-group" style={{ marginBottom: '1rem' }}>
      <label style={{ display: 'block', marginBottom: '0.5rem' }}>Domínio: (Escolha uma classe)</label>
      <select
        value={objDomain[0] || ''}
        onChange={(e) => setObjDomain([e.target.value])}
        className="form-select"
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
      >
        <option value="">Selecione uma classe</option>
        {flattenClasses(ontologyData.classes).map(cls => (
          <option key={cls.name} value={cls.name}>{cls.name}</option>
        ))}
      </select>
      <small style={{ color: '#666', fontSize: '0.8rem' }}>O backend aceita apenas uma classe de domínio.</small>
    </div>
    
    <div className="form-group" style={{ marginBottom: '1rem' }}>
      <label style={{ display: 'block', marginBottom: '0.5rem' }}>Range: (Escolha uma classe)</label>
      <select
        value={objRange[0] || ''}
        onChange={(e) => setObjRange([e.target.value])}
        className="form-select"
        style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
      >
        <option value="">Selecione uma classe</option>
        {flattenClasses(ontologyData.classes).map(cls => (
          <option key={cls.name} value={cls.name}>{cls.name}</option>
        ))}
      </select>
      <small style={{ color: '#666', fontSize: '0.8rem' }}>O backend aceita apenas uma classe de range.</small>
    </div>
    
    <div className="form-actions" style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
      <button 
        onClick={handleCreateObjectProperty} 
        className="submit-btn"
        style={{ padding: '8px 16px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
      >
        Criar Propriedade
      </button>
      <button 
        onClick={() => setShowObjectPropertyForm(false)} 
        className="cancel-btn"
        style={{ padding: '8px 16px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
      >
        Cancelar
      </button>
    </div>
  </div>
);


return (
  <div className="ontology-upload">
    <div className="upload-form">
      <h2>Ontology Loader</h2>
      <form onSubmit={handleSubmit}>
        <div className="file-input-wrapper">
          <input
            type="file"
            accept=".owl"
            onChange={(e) => setFile(e.target.files[0])}
            className="file-input"
            id="ontology-file"
          />
          <label htmlFor="ontology-file" className="upload-button">
            <FiUpload style={{ marginRight: '8px' }} />
            {file ? file.name : 'Choose OWL File'}
          </label>
        </div>
        <button type="submit" className="upload-button">
          Load Ontology
        </button>
      </form>

      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
    </div>

    {ontologyData && (
      <div className="ontology-view">
        <div className="ontology-tabs">
          <button
            className={`tab-btn ${activeTab === 'classes' ? 'active' : ''}`}
            onClick={() => setActiveTab('classes')}
          >
            <FiGrid /> Classes ({ontologyData.classes_count})
          </button>
          <button
            className={`tab-btn ${activeTab === 'individuals' ? 'active' : ''}`}
            onClick={() => setActiveTab('individuals')}
          >
            <FiUser /> Indivíduos ({ontologyData.individuals.length})
          </button>
          <button
            className={`tab-btn ${activeTab === 'object_properties' ? 'active' : ''}`}
            onClick={() => setActiveTab('object_properties')}
          >
            <FiList /> Object Properties ({ontologyData.object_properties ? ontologyData.object_properties.length : 0})
          </button>
          <button
            className={`tab-btn ${activeTab === 'data_properties' ? 'active' : ''}`}
            onClick={() => setActiveTab('data_properties')}
          >
            <FiTag /> Data Properties ({ontologyData.data_properties.length})
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'classes' && (
            <div className="ontology-tree">
              <div className="search-box">
                <FiSearch className="search-icon" />
                <input
                  type="text"
                  placeholder="Search classes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
              </div>
              <h3>Class Hierarchy</h3>
              <div className="create-class-actions">
                <button
                  className="create-class-btn"
                  onClick={() => setShowCreateClassForm(!showCreateClassForm)}
                >
                  + Nova Classe
                </button>
              </div>

              {showCreateClassForm && (
                <div className="create-class-form">
                  <input
                    type="text"
                    placeholder="Nome da nova classe"
                    value={newClassName}
                    onChange={(e) => setNewClassName(e.target.value)}
                    className="class-input"
                  />
                  <select
                    multiple
                    value={selectedParents}
                    onChange={(e) => {
                      const options = Array.from(e.target.selectedOptions, option => option.value);
                      setSelectedParents(options);
                    }}
                    className="class-select"
                  >
                    {flattenClasses(ontologyData.classes).map(cls => (
                      <option key={cls.name} value={cls.name}>{cls.name}</option>
                    ))}
                  </select>

                  <div className="form-actions">
                    <button onClick={handleCreateClass} className="submit-btn">Criar</button>
                    <button onClick={() => setShowCreateClassForm(false)} className="cancel-btn">Cancelar</button>
                  </div>
                </div>
              )}

              <ul>
                {(filteredHierarchy || ontologyData.classes).map(root => (
                  renderNode(root)
                ))}
              </ul>
            </div>
          )}

          {activeTab === 'individuals' && (
            <div className="individuals-section">
              <div className="section-header">
                <h3>Indivíduos Existentes</h3>
                <button
                  className="create-individual-btn"
                  onClick={() => {
                    setNewIndividualName('');
                    setSelectedIndividualClasses([]);
                    setIndividualProperties([]);
                    setIndividualAnnotations([]);
                    setShowCreateIndividualForm(true);
                  }}
                >
                  + Novo Indivíduo
                </button>
              </div>

              {showCreateIndividualForm && (
                <div className="create-individual-form">
                  <input
                    type="text"
                    placeholder="Nome do indivíduo"
                    value={newIndividualName}
                    onChange={(e) => setNewIndividualName(e.target.value)}
                  />
                  <select
                    multiple
                    value={selectedIndividualClasses}
                    onChange={(e) => setSelectedIndividualClasses(Array.from(e.target.selectedOptions, opt => opt.value))}
                  >
                    {flattenClasses(ontologyData.classes).map(cls => (
                      <option key={cls.name} value={cls.name}>{cls.name}</option>
                    ))}
                  </select>

                  <div className="properties-inputs">
                    {individualProperties.map((prop, index) => (
                      <div key={index} className="property-row">
                        <select
                          value={prop.name}
                          onChange={(e) => handlePropertyChange(index, 'name', e.target.value)}
                        >
                          <option value="">Selecione uma Data Property</option>
                          {ontologyData.data_properties.map(p => (
                            <option key={p.name} value={p.name}>{p.name}</option>
                          ))}
                        </select>  
                        <input
                          type="text"
                          placeholder="Valor"
                          value={prop.value}
                          onChange={(e) => handlePropertyChange(index, 'value', e.target.value)}
                        />
                        <input
                          type="text"
                          placeholder="Language tag (opcional)"
                          value={prop.lang}
                          onChange={(e) => handlePropertyChange(index, 'lang', e.target.value)}
                        />
                        <select
                          value={prop.datatype}
                          onChange={(e) => handlePropertyChange(index, 'datatype', e.target.value)}
                          disabled={!ontologyData?.datatypes}
                        >
                          <option value="">Selecione um datatype</option>
                          {ontologyData?.datatypes?.map(dt => (
                            <option key={dt} value={dt}>{dt}</option>
                          ))}
                        </select>
                        <button
                          className="remove-property-btn"
                          onClick={() => removeProperty(index)}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                    <button
                      className="add-property-btn"
                      onClick={() => setIndividualProperties([...individualProperties, { name: '', values: '' }])}
                    >
                      + Adicionar Propriedade
                    </button>
                  </div>

                  <div className="annotations-inputs">
                    <h5>Anotações</h5>
                    {individualAnnotations.map((anno, idx) => (
                      <div key={idx} className="annotation-row">
                        <select
                          value={anno.name}
                          onChange={e => {
                            const a = [...individualAnnotations];
                            a[idx].name = e.target.value;
                            setIndividualAnnotations(a);
                          }}
                        >
                          <option value="">Selecione uma AnnotationProperty</option>
                          {ontologyData.annotation_properties.map(p => (
                            <option key={p.name} value={p.name}>{p.name}</option>
                          ))}
                        </select>
                        <input
                          type="text"
                          placeholder="Valor da anotação"
                          value={anno.value}
                          onChange={e => {
                            const a = [...individualAnnotations];
                            a[idx].value = e.target.value;
                            setIndividualAnnotations(a);
                          }}
                        />
                        <button onClick={() => {
                          setIndividualAnnotations(individualAnnotations.filter((_,i) => i!==idx));
                        }}>×</button>
                      </div>
                    ))}
                    <button onClick={() => setIndividualAnnotations([...individualAnnotations, { name:'', value:'' }])}>
                      + Adicionar Anotação
                    </button>
                  </div>

                  <div className="form-actions">
                    <button className="submit-btn" onClick={handleCreateIndividual}>Criar</button>
                    <button className="cancel-btn" onClick={() => setShowCreateIndividualForm(false)}>Cancelar</button>
                  </div>
                </div>
              )}

              <div className="individuals-list">
                {ontologyData.individuals.map(ind => (
                  <div key={ind.name} className="individual-card">
                    <h4 className="text-lg font-bold mb-2">{ind.name}</h4>
                    {ind.type && ind.type.length > 0 && (
                      <p><strong>Tipo(s):</strong> {ind.type.join(', ')}</p>
                    )}
                    {ind.properties && Object.keys(ind.properties).length > 0 && (
                      <div className="mt-2">
                        <h5 className="font-semibold">Propriedades:</h5>
                        {Object.entries(ind.properties).map(([prop, values]) => (
                          <div key={prop} className="property">
                            <span className="prop-name">{prop}:</span> {values.join(', ')}
                          </div>
                        ))}
                      </div>
                    )}
                    {ind.annotations && Object.keys(ind.annotations).length > 0 && (
                      <div className="mt-2">
                        <h5 className="font-semibold">Anotações:</h5>
                        {Object.entries(ind.annotations).map(([anno, values]) => (
                          <div key={anno} className="annotation">
                            <span className="annotation-name">{anno}:</span> {values.join(', ')}
                          </div>
                        ))}
                      </div>
                    )}
                    {ind.description && ind.description.types && ind.description.types.length > 0 && (
                      <div className="mt-2">
                        <h5 className="font-semibold">Descrição (Tipos adicionais):</h5>
                        {ind.description.types.map((descType, idx) => (
                          <div key={idx}>{descType}</div>
                        ))}
                      </div>
                    )}
                    {ind.same_as && ind.same_as.length > 0 && (
                      <div className="mt-2">
                        <h5 className="font-semibold">Mesmo que:</h5>
                        {ind.same_as.map((same, idx) => (
                          <div key={idx}>{same}</div>
                        ))}
                      </div>
                    )}
                    {ind.different_from && ind.different_from.length > 0 && (
                      <div className="mt-2">
                        <h5 className="font-semibold">Diferente de:</h5>
                        {ind.different_from.map((diff, idx) => (
                          <div key={idx}>{diff}</div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'object_properties' && (
            <div className="object-properties-section">
              <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>Object Properties</h3>
                <button
                  className="create-property-btn"
                  style={{ 
                    padding: '8px 16px', 
                    backgroundColor: '#4CAF50', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                  onClick={() => setShowObjectPropertyForm(!showObjectPropertyForm)}
                >
                  + Nova Object Property
                </button>
              </div>
              
              {showObjectPropertyForm && <ObjectPropertyForm />}
              
              <PropertiesList
                properties={ontologyData.object_properties}
                type="object"
              />

              <div className="relationship-form">
                <h4>Gerenciar Relacionamento</h4>
                <select id="rel-subject">
                  {ontologyData.individuals.map(ind => (
                    <option key={ind.name} value={ind.name}>{ind.name}</option>
                  ))}
                </select>
                <select id="rel-property">
                  {ontologyData.object_properties && Array.isArray(ontologyData.object_properties) && ontologyData.object_properties.map(prop => (
                    <option key={prop.name} value={prop.name}>{prop.name}</option>
                  ))}
                </select>
                <select id="rel-target">
                  {ontologyData.individuals.map(ind => (
                    <option key={ind.name} value={ind.name}>{ind.name}</option>
                  ))}
                </select>
                <select id="rel-action">
                  <option value="add">Adicionar</option>
                  <option value="remove">Remover</option>
                  <option value="replace">Substituir</option>
                </select>
                <input
                  id="rel-replace-with"
                  type="text"
                  placeholder="Novo alvo (para substituir)"
                />
                <button
                  onClick={() => {
                    const subject = document.getElementById('rel-subject').value;
                    const prop = document.getElementById('rel-property').value;
                    const target = document.getElementById('rel-target').value;
                    const action = document.getElementById('rel-action').value;
                    const replaceWith =
                      document.getElementById('rel-replace-with').value || null;
                    handleManageRelationship(
                      subject,
                      prop,
                      target,
                      action,
                      replaceWith
                    );
                  }}
                >
                  Executar
                </button>
              </div>
            </div>
          )}

          {activeTab === 'data_properties' && (
            <div className="data-properties-section">
              <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3>Data Properties</h3>
                <button 
                  onClick={() => setShowDataPropForm(!showDataPropForm)} 
                  style={{ 
                    padding: '8px 16px', 
                    backgroundColor: '#4CAF50', 
                    color: '#fff', 
                    border: 'none', 
                    borderRadius: '4px', 
                    cursor: 'pointer' 
                  }}
                >
                  + Nova Data Property
                </button>
              </div>

              {showDataPropForm && (
                <div className="create-prop-form">
                  <input 
                    placeholder="Nome da DataProperty" 
                    value={newDataPropName} 
                    onChange={e => setNewDataPropName(e.target.value)} 
                  />
                  <label>Domínio (classes):</label>
                  <select 
                    multiple 
                    value={dataDomain} 
                    onChange={e => setDataDomain(Array.from(e.target.selectedOptions, opt => opt.value))}
                  >
                    {flattenClasses(ontologyData.classes).map(c => (
                      <option key={c.name} value={c.name}>{c.name}</option>
                    ))}
                  </select>
                  <label>Range (tipo de dado):</label>
                  <select 
                    value={dataRangeType} 
                    onChange={e => setDataRangeType(e.target.value)}
                  >
                    <option value="">Selecione tipo</option>
                    {ontologyData.datatypes.map(dt => (
                      <option key={dt} value={dt}>{dt}</option>
                    ))}
                  </select>
                  <label>Características:</label>
                  <select
                    multiple
                    value={dataCharacteristics}
                    onChange={e => setDataCharacteristics(Array.from(e.target.selectedOptions, opt => opt.value))}
                  >
                    <option value="functional">Functional</option>
                  </select>
                  <div style={{ marginTop: '8px' }}>
                    <button onClick={handleCreateDataProperty}>Criar</button>
                    <button onClick={() => setShowDataPropForm(false)}>Cancelar</button>
                  </div>
                </div>
              )}

              <PropertiesList properties={ontologyData.data_properties} type="data" />
            </div>
          )}

          <div className="export-section">
            <input
              type="text"
              value={exportFileName}
              onChange={(e) => setExportFileName(e.target.value)}
              className="export-input"
              placeholder="Nome do arquivo .owl"
            />
            <button
              className="export-button"
              onClick={handleExportOntology}
            >
              Exportar Ontologia
            </button>
          </div>
        </div>
      </div>
    )}
  </div>
 );
}
  
export default OntologyUpload;