import re
from typing import Dict, List, Tuple

class CloudModelClassifier:
    """
    Clasificador de modelos de servicios en la nube (IaaS, PaaS, SaaS, FaaS)
    basado en reglas y palabras clave.
    """
    
    def __init__(self):
        # Definir palabras clave para cada modelo de servicio en la nube
        self.keywords = {
            'IaaS': {
                'español': [
                    'infraestructura', 'servidores', 'almacenamiento', 'redes', 'virtualización',
                    'máquinas virtuales', 'vm', 'instancias', 'bloques de almacenamiento',
                    'balanceadores de carga', 'firewalls', 'vpc', 'subredes', 'gateways',
                    'discos duros', 'cpu', 'ram', 'memoria', 'procesamiento', 'escalabilidad',
                    'auto-scaling', 'monitoreo', 'backup', 'disaster recovery', 'seguridad',
                    'acceso directo', 'control total', 'configuración', 'administración',
                    'ec2', 'azure vm', 'google compute engine', 'bare metal', 'hosting',
                    'datacenter', 'centro de datos', 'provisioning', 'infrastructure as a service'
                ],
                'ingles': [
                    'infrastructure', 'servers', 'storage', 'networking', 'virtualization',
                    'virtual machines', 'vm', 'instances', 'storage blocks', 'load balancers',
                    'firewalls', 'vpc', 'subnets', 'gateways', 'hard drives', 'cpu', 'ram',
                    'memory', 'processing', 'scalability', 'auto-scaling', 'monitoring',
                    'backup', 'disaster recovery', 'security', 'direct access', 'full control',
                    'configuration', 'administration', 'compute', 'network', 'storage',
                    'ec2', 'azure vm', 'google compute engine', 'bare metal', 'hosting',
                    'datacenter', 'data center', 'provisioning', 'infrastructure as a service'
                ]
            },
            'PaaS': {
                'español': [
                    'plataforma', 'desarrollo', 'aplicaciones', 'frameworks', 'runtime',
                    'middleware', 'bases de datos', 'servicios web', 'apis', 'deployment',
                    'despliegue', 'entorno de desarrollo', 'herramientas de desarrollo',
                    'lenguajes de programación', 'contenedores', 'orquestación', 'kubernetes',
                    'docker', 'microservicios', 'arquitectura', 'escalabilidad automática',
                    'monitoreo de aplicaciones', 'logs', 'debugging', 'testing',
                    'heroku', 'google app engine', 'azure app service', 'openshift',
                    'platform as a service', 'build', 'deploy', 'manage applications'
                ],
                'ingles': [
                    'platform', 'development', 'applications', 'frameworks', 'runtime',
                    'middleware', 'databases', 'web services', 'apis', 'deployment',
                    'development environment', 'development tools', 'programming languages',
                    'containers', 'orchestration', 'kubernetes', 'docker', 'microservices',
                    'architecture', 'auto-scaling', 'application monitoring', 'logs',
                    'debugging', 'testing', 'build', 'deploy', 'manage',
                    'heroku', 'google app engine', 'azure app service', 'openshift',
                    'platform as a service', 'build', 'deploy', 'manage applications'
                ]
            },
            'SaaS': {
                'español': [
                    'software', 'aplicación', 'servicio', 'usuario final', 'interfaz web',
                    'navegador', 'acceso remoto', 'suscripción', 'licencias', 'actualizaciones',
                    'mantenimiento', 'soporte', 'colaboración', 'productividad', 'crm',
                    'erp', 'office', 'email', 'calendario', 'almacenamiento en la nube',
                    'compartir archivos', 'videoconferencia', 'chat', 'mensajería',
                    'análisis', 'reportes', 'dashboard', 'personalización',
                    'salesforce', 'dropbox', 'google workspace', 'microsoft 365',
                    'software as a service', 'end-user', 'subscription-based'
                ],
                'ingles': [
                    'software', 'application', 'service', 'end user', 'web interface',
                    'browser', 'remote access', 'subscription', 'licenses', 'updates',
                    'maintenance', 'support', 'collaboration', 'productivity', 'crm',
                    'erp', 'office', 'email', 'calendar', 'cloud storage',
                    'file sharing', 'video conferencing', 'chat', 'messaging',
                    'analytics', 'reports', 'dashboard', 'customization', 'user-friendly',
                    'salesforce', 'dropbox', 'google workspace', 'microsoft 365',
                    'software as a service', 'end-user', 'subscription-based'
                ]
            },
            'FaaS': {
                'español': [
                    'funciones', 'serverless', 'sin servidor', 'eventos', 'triggers',
                    'ejecución bajo demanda', 'pago por uso', 'microservicios',
                    'apis', 'webhooks', 'cron', 'scheduled', 'timeout', 'memory',
                    'cold start', 'warm start', 'invocaciones', 'latencia',
                    'escalabilidad automática', 'código', 'lógica de negocio',
                    'procesamiento', 'transformación', 'integración',
                    'aws lambda', 'azure functions', 'google cloud functions',
                    'function as a service', 'event-driven', 'stateless'
                ],
                'ingles': [
                    'functions', 'serverless', 'serverless computing', 'events', 'triggers',
                    'on-demand execution', 'pay-per-use', 'microservices', 'apis',
                    'webhooks', 'cron', 'scheduled', 'timeout', 'memory', 'cold start',
                    'warm start', 'invocations', 'latency', 'auto-scaling', 'code',
                    'business logic', 'processing', 'transformation', 'integration',
                    'lambda', 'azure functions', 'google cloud functions',
                    'function as a service', 'event-driven', 'stateless'
                ]
            }
        }
        
        # Pesos para diferentes tipos de coincidencias
        self.weights = {
            'exact_match': 5.0,  # Aumentado para dar más peso a coincidencias exactas
            'partial_match': 1.0,  # Reducido para evitar falsos positivos
            'word_boundary': 3.0   # Aumentado para palabras completas
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocesa el texto para normalizarlo.
        """
        # Convertir a minúsculas y eliminar caracteres especiales
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def calculate_score(self, text: str, keywords: List[str]) -> float:
        """
        Calcula el puntaje para un conjunto de palabras clave.
        """
        score = 0.0
        text_words = set(text.split())
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Coincidencia exacta (mayor peso)
            if keyword_lower in text_lower:
                score += self.weights['exact_match']
                
                # Bonus para palabras clave específicas de servicios
                if keyword_lower in ['ec2', 'lambda', 'heroku', 'salesforce', 'dropbox', 'azure functions']:
                    score += 10.0  # Bonus significativo para servicios específicos
            
            # Coincidencia de palabra completa
            elif keyword_lower in text_words:
                score += self.weights['word_boundary']
                
                # Bonus para términos técnicos específicos
                if keyword_lower in ['serverless', 'infrastructure', 'platform', 'software']:
                    score += 5.0
            
            # Coincidencia parcial (menor peso)
            elif any(keyword_lower in word or word in keyword_lower for word in text_words):
                score += self.weights['partial_match']
        
        return score
    
    def classify(self, text: str) -> Tuple[str, Dict[str, float]]:
        """
        Clasifica el texto en uno de los modelos de servicio en la nube.
        
        Args:
            text (str): Texto a clasificar
            
        Returns:
            Tuple[str, Dict[str, float]]: (Modelo clasificado, Puntajes de todos los modelos)
        """
        # Validar entrada usando la nueva función de validación
        is_valid, error_message = self.validate_input(text)
        if not is_valid:
            return "Error de validación", {}
        
        # Preprocesar el texto
        processed_text = self.preprocess_text(text)
        
        # Calcular puntajes para cada modelo
        scores = {}
        
        for model, languages in self.keywords.items():
            total_score = 0.0
            
            for language, keywords in languages.items():
                score = self.calculate_score(processed_text, keywords)
                total_score += score
            
            scores[model] = total_score
        
        # Encontrar el modelo con mayor puntaje
        if not scores or all(score == 0 for score in scores.values()):
            return "No clasificable", scores
        
        best_model = max(scores, key=scores.get)
        max_score = scores[best_model]
        
        # Si el puntaje es muy bajo, considerar como no clasificable
        if max_score < 2.0:
            return "No clasificable", scores
        
        # Verificar si hay un segundo lugar muy cercano (diferencia < 20%)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1:
            second_score = sorted_scores[1][1]
            if second_score > 0 and (max_score - second_score) / max_score < 0.2:
                # Si la diferencia es menor al 20%, usar reglas adicionales
                return self._resolve_tie(processed_text, scores)
        
        return best_model, scores
    
    def _resolve_tie(self, text: str, scores: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
        """
        Resuelve empates usando reglas adicionales.
        """
        # Reglas específicas para resolver empates
        text_lower = text.lower()
        
        # Si contiene palabras específicas de FaaS
        if any(word in text_lower for word in ['lambda', 'serverless', 'functions', 'event-driven']):
            return 'FaaS', scores
        
        # Si contiene palabras específicas de IaaS
        if any(word in text_lower for word in ['ec2', 'infrastructure', 'virtual machines', 'servers']):
            return 'IaaS', scores
        
        # Si contiene palabras específicas de PaaS
        if any(word in text_lower for word in ['heroku', 'platform', 'deployment', 'development']):
            return 'PaaS', scores
        
        # Si contiene palabras específicas de SaaS
        if any(word in text_lower for word in ['salesforce', 'software', 'application', 'subscription']):
            return 'SaaS', scores
        
        # Si no se puede resolver, devolver el de mayor puntaje
        return max(scores, key=scores.get), scores
    
    def classify_with_confidence(self, text: str) -> Dict[str, any]:
        """
        Clasifica el texto y retorna información detallada incluyendo confianza.
        
        Args:
            text (str): Texto a clasificar
            
        Returns:
            Dict[str, any]: Información detallada de la clasificación
        """
        # Validar entrada usando la nueva función de validación
        is_valid, error_message = self.validate_input(text)
        if not is_valid:
            return {
                'model': 'Error de validación',
                'confidence': 0.0,
                'scores': {},
                'explanation': f"Error de validación: {error_message}",
                'found_keywords': []
            }
        
        model, scores = self.classify(text)
        
        if model == "No clasificable":
            return {
                'model': model,
                'confidence': 0.0,
                'scores': scores,
                'explanation': 'No se encontraron palabras clave suficientes para clasificar el texto.'
            }
        
        # Calcular confianza basada en el puntaje máximo y la diferencia con otros
        max_score = scores[model]
        total_score = sum(scores.values())
        
        if total_score == 0:
            confidence = 0.0
        else:
            confidence = min(1.0, max_score / total_score * 2)  # Factor de 2 para normalizar
        
        # Generar explicación
        explanation = f"Clasificado como {model} con {confidence:.2%} de confianza. "
        explanation += f"Puntaje: {max_score:.2f}. "
        
        # Agregar palabras clave encontradas
        found_keywords = []
        for lang_keywords in self.keywords[model].values():
            for keyword in lang_keywords:
                if keyword.lower() in text.lower():
                    found_keywords.append(keyword)
        
        if found_keywords:
            explanation += f"Palabras clave encontradas: {', '.join(set(found_keywords[:5]))}"
        
        return {
            'model': model,
            'confidence': confidence,
            'scores': scores,
            'explanation': explanation,
            'found_keywords': list(set(found_keywords))
        }

    def validate_input(self, text) -> Tuple[bool, str]:
        """
        Valida la entrada del texto.
        
        Args:
            text: Texto a validar
            
        Returns:
            Tuple[bool, str]: (Es válido, Mensaje de error)
        """
        if text is None:
            return False, "El texto no puede ser None."
        
        if not isinstance(text, str):
            return False, f"El texto debe ser una cadena de caracteres, no {type(text).__name__}."
        
        if not text:
            return False, "El texto no puede estar vacío."
        
        if len(text.strip()) < 3:
            return False, "El texto debe tener al menos 3 caracteres."
        
        if len(text) > 10000:
            return False, "El texto es demasiado largo (máximo 10,000 caracteres)."
        
        # Verificar si contiene solo espacios en blanco
        if not text.strip():
            return False, "El texto no puede contener solo espacios en blanco."
        
        return True, ""

    def classify_iaas(self, text: str) -> Dict[str, any]:
        """
        Clasifica específicamente para IaaS (Infrastructure as a Service).
        
        Args:
            text (str): Texto a clasificar
            
        Returns:
            Dict[str, any]: Información detallada de la clasificación IaaS
        """
        # Validar entrada
        is_valid, error_message = self.validate_input(text)
        if not is_valid:
            return {
                'model': 'Error',
                'confidence': 0.0,
                'scores': {},
                'explanation': f"Error de validación: {error_message}",
                'found_keywords': []
            }
        
        # Obtener puntaje específico para IaaS
        processed_text = self.preprocess_text(text)
        iaas_score = 0.0
        
        for language, keywords in self.keywords['IaaS'].items():
            iaas_score += self.calculate_score(processed_text, keywords)
        
        # Calcular confianza específica para IaaS
        total_possible_score = len(self.keywords['IaaS']['español']) + len(self.keywords['IaaS']['ingles'])
        confidence = min(1.0, iaas_score / (total_possible_score * 5.0))  # Normalizar por puntaje máximo posible
        
        # Determinar si es IaaS (umbral mínimo)
        is_iaas = iaas_score >= 5.0  # Umbral mínimo para considerar IaaS
        
        found_keywords = []
        for lang_keywords in self.keywords['IaaS'].values():
            for keyword in lang_keywords:
                if keyword.lower() in text.lower():
                    found_keywords.append(keyword)
        
        explanation = f"Análisis específico para IaaS. Puntaje: {iaas_score:.2f}. "
        if is_iaas:
            explanation += f"Clasificado como IaaS con {confidence:.2%} de confianza. "
        else:
            explanation += "No cumple los criterios mínimos para IaaS. "
        
        if found_keywords:
            explanation += f"Palabras clave IaaS encontradas: {', '.join(set(found_keywords[:5]))}"
        
        return {
            'model': 'IaaS' if is_iaas else 'No IaaS',
            'confidence': confidence,
            'scores': {'IaaS': iaas_score},
            'explanation': explanation,
            'found_keywords': list(set(found_keywords))
        }

    def classify_paas(self, text: str) -> Dict[str, any]:
        """
        Clasifica específicamente para PaaS (Platform as a Service).
        
        Args:
            text (str): Texto a clasificar
            
        Returns:
            Dict[str, any]: Información detallada de la clasificación PaaS
        """
        # Validar entrada
        is_valid, error_message = self.validate_input(text)
        if not is_valid:
            return {
                'model': 'Error',
                'confidence': 0.0,
                'scores': {},
                'explanation': f"Error de validación: {error_message}",
                'found_keywords': []
            }
        
        # Obtener puntaje específico para PaaS
        processed_text = self.preprocess_text(text)
        paas_score = 0.0
        
        for language, keywords in self.keywords['PaaS'].items():
            paas_score += self.calculate_score(processed_text, keywords)
        
        # Calcular confianza específica para PaaS
        total_possible_score = len(self.keywords['PaaS']['español']) + len(self.keywords['PaaS']['ingles'])
        confidence = min(1.0, paas_score / (total_possible_score * 5.0))
        
        # Determinar si es PaaS (umbral mínimo)
        is_paas = paas_score >= 5.0
        
        found_keywords = []
        for lang_keywords in self.keywords['PaaS'].values():
            for keyword in lang_keywords:
                if keyword.lower() in text.lower():
                    found_keywords.append(keyword)
        
        explanation = f"Análisis específico para PaaS. Puntaje: {paas_score:.2f}. "
        if is_paas:
            explanation += f"Clasificado como PaaS con {confidence:.2%} de confianza. "
        else:
            explanation += "No cumple los criterios mínimos para PaaS. "
        
        if found_keywords:
            explanation += f"Palabras clave PaaS encontradas: {', '.join(set(found_keywords[:5]))}"
        
        return {
            'model': 'PaaS' if is_paas else 'No PaaS',
            'confidence': confidence,
            'scores': {'PaaS': paas_score},
            'explanation': explanation,
            'found_keywords': list(set(found_keywords))
        }

    def classify_saas(self, text: str) -> Dict[str, any]:
        """
        Clasifica específicamente para SaaS (Software as a Service).
        
        Args:
            text (str): Texto a clasificar
            
        Returns:
            Dict[str, any]: Información detallada de la clasificación SaaS
        """
        # Validar entrada
        is_valid, error_message = self.validate_input(text)
        if not is_valid:
            return {
                'model': 'Error',
                'confidence': 0.0,
                'scores': {},
                'explanation': f"Error de validación: {error_message}",
                'found_keywords': []
            }
        
        # Obtener puntaje específico para SaaS
        processed_text = self.preprocess_text(text)
        saas_score = 0.0
        
        for language, keywords in self.keywords['SaaS'].items():
            saas_score += self.calculate_score(processed_text, keywords)
        
        # Calcular confianza específica para SaaS
        total_possible_score = len(self.keywords['SaaS']['español']) + len(self.keywords['SaaS']['ingles'])
        confidence = min(1.0, saas_score / (total_possible_score * 5.0))
        
        # Determinar si es SaaS (umbral mínimo)
        is_saas = saas_score >= 5.0
        
        found_keywords = []
        for lang_keywords in self.keywords['SaaS'].values():
            for keyword in lang_keywords:
                if keyword.lower() in text.lower():
                    found_keywords.append(keyword)
        
        explanation = f"Análisis específico para SaaS. Puntaje: {saas_score:.2f}. "
        if is_saas:
            explanation += f"Clasificado como SaaS con {confidence:.2%} de confianza. "
        else:
            explanation += "No cumple los criterios mínimos para SaaS. "
        
        if found_keywords:
            explanation += f"Palabras clave SaaS encontradas: {', '.join(set(found_keywords[:5]))}"
        
        return {
            'model': 'SaaS' if is_saas else 'No SaaS',
            'confidence': confidence,
            'scores': {'SaaS': saas_score},
            'explanation': explanation,
            'found_keywords': list(set(found_keywords))
        }

    def classify_faas(self, text: str) -> Dict[str, any]:
        """
        Clasifica específicamente para FaaS (Function as a Service).
        
        Args:
            text (str): Texto a clasificar
            
        Returns:
            Dict[str, any]: Información detallada de la clasificación FaaS
        """
        # Validar entrada
        is_valid, error_message = self.validate_input(text)
        if not is_valid:
            return {
                'model': 'Error',
                'confidence': 0.0,
                'scores': {},
                'explanation': f"Error de validación: {error_message}",
                'found_keywords': []
            }
        
        # Obtener puntaje específico para FaaS
        processed_text = self.preprocess_text(text)
        faas_score = 0.0
        
        for language, keywords in self.keywords['FaaS'].items():
            faas_score += self.calculate_score(processed_text, keywords)
        
        # Calcular confianza específica para FaaS
        total_possible_score = len(self.keywords['FaaS']['español']) + len(self.keywords['FaaS']['ingles'])
        confidence = min(1.0, faas_score / (total_possible_score * 5.0))
        
        # Determinar si es FaaS (umbral mínimo)
        is_faas = faas_score >= 5.0
        
        found_keywords = []
        for lang_keywords in self.keywords['FaaS'].values():
            for keyword in lang_keywords:
                if keyword.lower() in text.lower():
                    found_keywords.append(keyword)
        
        explanation = f"Análisis específico para FaaS. Puntaje: {faas_score:.2f}. "
        if is_faas:
            explanation += f"Clasificado como FaaS con {confidence:.2%} de confianza. "
        else:
            explanation += "No cumple los criterios mínimos para FaaS. "
        
        if found_keywords:
            explanation += f"Palabras clave FaaS encontradas: {', '.join(set(found_keywords[:5]))}"
        
        return {
            'model': 'FaaS' if is_faas else 'No FaaS',
            'confidence': confidence,
            'scores': {'FaaS': faas_score},
            'explanation': explanation,
            'found_keywords': list(set(found_keywords))
        }


def main():
    """
    Función principal para demostrar el uso del clasificador.
    """
    classifier = CloudModelClassifier()
    
    # Ejemplos de texto para clasificar
    examples = [
        "Amazon EC2 proporciona capacidad de computación escalable en la nube con instancias virtuales",
        "Heroku es una plataforma que permite desplegar aplicaciones web fácilmente",
        "Salesforce CRM es una aplicación de software que se accede a través del navegador",
        "AWS Lambda ejecuta código en respuesta a eventos sin gestionar servidores",
        "Microsoft Azure ofrece servicios de infraestructura como máquinas virtuales y almacenamiento",
        "Google App Engine es una plataforma para desarrollar y alojar aplicaciones web",
        "Dropbox es un servicio de almacenamiento en la nube para compartir archivos",
        "Azure Functions permite ejecutar código serverless basado en eventos",
        "Este es un texto que no tiene relación con servicios en la nube"
    ]
    
    print("=== Clasificador de Modelos de Servicios en la Nube ===\n")
    
    # Demostrar clasificación general
    print("=== Clasificación General ===")
    for i, example in enumerate(examples, 1):
        print(f"Ejemplo {i}:")
        print(f"Texto: {example}")
        
        result = classifier.classify_with_confidence(example)
        
        print(f"Clasificación: {result['model']}")
        print(f"Confianza: {result['confidence']:.2%}")
        print(f"Explicación: {result['explanation']}")
        print(f"Puntajes: {result['scores']}")
        print("-" * 80)
    
    # Demostrar clasificaciones específicas
    print("\n=== Clasificaciones Específicas ===")
    test_text = "Amazon EC2 proporciona capacidad de computación escalable en la nube"
    print(f"Texto de prueba: {test_text}")
    print()
    
    # Clasificación específica IaaS
    iaas_result = classifier.classify_iaas(test_text)
    print(f"IaaS: {iaas_result['model']} (Confianza: {iaas_result['confidence']:.2%})")
    print(f"  Explicación: {iaas_result['explanation']}")
    
    # Clasificación específica PaaS
    paas_result = classifier.classify_paas(test_text)
    print(f"PaaS: {paas_result['model']} (Confianza: {paas_result['confidence']:.2%})")
    print(f"  Explicación: {paas_result['explanation']}")
    
    # Clasificación específica SaaS
    saas_result = classifier.classify_saas(test_text)
    print(f"SaaS: {saas_result['model']} (Confianza: {saas_result['confidence']:.2%})")
    print(f"  Explicación: {saas_result['explanation']}")
    
    # Clasificación específica FaaS
    faas_result = classifier.classify_faas(test_text)
    print(f"FaaS: {faas_result['model']} (Confianza: {faas_result['confidence']:.2%})")
    print(f"  Explicación: {faas_result['explanation']}")
    
    # Demostrar validación de entrada
    print("\n=== Validación de Entrada ===")
    invalid_inputs = [
        "",  # Texto vacío
        "ab",  # Texto muy corto
        "   ",  # Solo espacios
        123,  # No es string
        "x" * 10001  # Texto muy largo
    ]
    
    for invalid_input in invalid_inputs:
        print(f"Probando: {repr(invalid_input)}")
        is_valid, error_message = classifier.validate_input(invalid_input)
        print(f"  Válido: {is_valid}")
        if not is_valid:
            print(f"  Error: {error_message}")
        print()
    
    # Interfaz interactiva
    print("\n=== Modo Interactivo ===")
    print("Escribe 'salir' para terminar.")
    print("Comandos especiales:")
    print("  'iaas <texto>' - Clasificación específica IaaS")
    print("  'paas <texto>' - Clasificación específica PaaS")
    print("  'saas <texto>' - Clasificación específica SaaS")
    print("  'faas <texto>' - Clasificación específica FaaS")
    
    while True:
        user_input = input("\nIngresa un texto para clasificar: ").strip()
        
        if user_input.lower() in ['salir', 'exit', 'quit']:
            print("¡Hasta luego!")
            break
        
        if not user_input:
            print("Por favor, ingresa algún texto.")
            continue
        
        # Verificar si es un comando específico
        if user_input.lower().startswith(('iaas ', 'paas ', 'saas ', 'faas ')):
            parts = user_input.split(' ', 1)
            if len(parts) == 2:
                command, text = parts
                command = command.lower()
                
                if command == 'iaas':
                    result = classifier.classify_iaas(text)
                elif command == 'paas':
                    result = classifier.classify_paas(text)
                elif command == 'saas':
                    result = classifier.classify_saas(text)
                elif command == 'faas':
                    result = classifier.classify_faas(text)
                
                print(f"\nResultado ({command.upper()}): {result['model']}")
                print(f"Confianza: {result['confidence']:.2%}")
                print(f"Explicación: {result['explanation']}")
            else:
                print("Formato incorrecto. Usa: 'iaas <texto>', 'paas <texto>', etc.")
        else:
            # Clasificación general
            result = classifier.classify_with_confidence(user_input)
            
            print(f"\nResultado: {result['model']}")
            print(f"Confianza: {result['confidence']:.2%}")
            print(f"Explicación: {result['explanation']}")


if __name__ == "__main__":
    main()
