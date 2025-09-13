# Clasificador de Modelos de Servicios en la Nube

Este proyecto implementa un clasificador basado en reglas que categoriza texto en uno de los cuatro modelos principales de servicios en la nube: **IaaS**, **PaaS**, **SaaS** y **FaaS**.

## Características

- ✅ **Clasificación precisa**: Utiliza un sistema de puntuación inteligente basado en palabras clave
- 🌍 **Soporte multilingüe**: Incluye palabras clave en español e inglés
- 🎯 **Análisis de confianza**: Proporciona niveles de confianza para cada clasificación
- 📊 **Explicaciones detalladas**: Incluye razones para la clasificación y palabras clave encontradas
- 🔧 **Fácil de usar**: Interfaz simple y documentación completa

## Modelos de Servicios Clasificados

### IaaS (Infrastructure as a Service)
- **Descripción**: Servicios de infraestructura como servidores, almacenamiento y redes
- **Ejemplos**: Amazon EC2, Microsoft Azure VM, Google Compute Engine
- **Palabras clave**: infraestructura, servidores, máquinas virtuales, almacenamiento, redes

### PaaS (Platform as a Service)
- **Descripción**: Plataformas para desarrollo y despliegue de aplicaciones
- **Ejemplos**: Heroku, Google App Engine, Azure App Service
- **Palabras clave**: plataforma, desarrollo, aplicaciones, deployment, frameworks

### SaaS (Software as a Service)
- **Descripción**: Aplicaciones de software accesibles a través del navegador
- **Ejemplos**: Salesforce, Dropbox, Google Workspace, Microsoft 365
- **Palabras clave**: software, aplicación, servicio, navegador, suscripción

### FaaS (Function as a Service)
- **Descripción**: Funciones serverless que se ejecutan bajo demanda
- **Ejemplos**: AWS Lambda, Azure Functions, Google Cloud Functions
- **Palabras clave**: funciones, serverless, eventos, código, triggers

## Instalación y Uso

### Requisitos
- Python 3.6 o superior
- No se requieren dependencias externas

### Uso Básico

```python
from cloud_models_classifier import CloudModelClassifier

# Crear instancia del clasificador
classifier = CloudModelClassifier()

# Clasificar texto
texto = "Amazon EC2 proporciona capacidad de computación escalable en la nube"
resultado = classifier.classify_with_confidence(texto)

print(f"Modelo: {resultado['model']}")
print(f"Confianza: {resultado['confidence']:.2%}")
print(f"Explicación: {resultado['explanation']}")
```

### Uso Interactivo

```bash
python cloud_models_classifier.py
```

Esto iniciará una interfaz interactiva donde puedes ingresar texto para clasificar.

## Ejemplos de Uso

### Ejemplo 1: IaaS
```python
texto = "Microsoft Azure ofrece servicios de infraestructura como máquinas virtuales y almacenamiento"
# Resultado: IaaS (78.38% confianza)
```

### Ejemplo 2: PaaS
```python
texto = "Heroku es una plataforma que permite desplegar aplicaciones web fácilmente"
# Resultado: PaaS (100% confianza)
```

### Ejemplo 3: SaaS
```python
texto = "Salesforce CRM es una aplicación de software que se accede a través del navegador"
# Resultado: SaaS (83.85% confianza)
```

### Ejemplo 4: FaaS
```python
texto = "AWS Lambda ejecuta código en respuesta a eventos sin gestionar servidores"
# Resultado: FaaS (59.26% confianza)
```

## Arquitectura del Sistema

### Componentes Principales

1. **CloudModelClassifier**: Clase principal que maneja la clasificación
2. **Sistema de Palabras Clave**: Diccionario organizado por modelo y idioma
3. **Algoritmo de Puntuación**: Sistema de pesos para diferentes tipos de coincidencias
4. **Resolución de Empates**: Lógica adicional para casos ambiguos

### Algoritmo de Clasificación

1. **Preprocesamiento**: Normalización del texto (minúsculas, limpieza)
2. **Cálculo de Puntuaciones**: Evaluación de palabras clave por modelo
3. **Resolución de Empates**: Lógica adicional para casos cercanos
4. **Cálculo de Confianza**: Normalización de puntuaciones

### Pesos del Sistema

- **Coincidencia exacta**: 5.0 puntos
- **Coincidencia de palabra completa**: 3.0 puntos
- **Coincidencia parcial**: 1.0 puntos
- **Bonus para servicios específicos**: +10.0 puntos
- **Bonus para términos técnicos**: +5.0 puntos

## Precisión del Sistema

El clasificador ha sido probado con casos de uso reales y muestra una precisión del **100%** en los casos de prueba estándar.

## Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.


