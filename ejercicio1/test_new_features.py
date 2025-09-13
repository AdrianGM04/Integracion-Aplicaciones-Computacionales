from cloud_models_classifier import CloudModelClassifier

def test_new_features():
    classifier = CloudModelClassifier()
    
    print("=== Prueba de Nuevas Funcionalidades ===\n")
    
    # 1. Probar validación de entrada
    print("1. Validación de Entrada:")
    test_cases = [
        ("", "Texto vacío"),
        ("ab", "Texto muy corto"),
        ("   ", "Solo espacios"),
        (123, "Número"),
        ("x" * 10001, "Texto muy largo"),
        ("Texto válido", "Texto válido")
    ]
    
    for test_input, description in test_cases:
        is_valid, error_message = classifier.validate_input(test_input)
        print(f"  {description}: {is_valid} {f'({error_message})' if not is_valid else ''}")
    
    print()
    
    # 2. Probar clasificaciones específicas
    print("2. Clasificaciones Específicas:")
    test_text = "Amazon EC2 proporciona capacidad de computación escalable en la nube"
    print(f"Texto de prueba: {test_text}")
    print()
    
    # IaaS
    iaas_result = classifier.classify_iaas(test_text)
    print(f"IaaS: {iaas_result['model']} (Confianza: {iaas_result['confidence']:.2%})")
    print(f"  Explicación: {iaas_result['explanation']}")
    
    # PaaS
    paas_result = classifier.classify_paas(test_text)
    print(f"PaaS: {paas_result['model']} (Confianza: {paas_result['confidence']:.2%})")
    print(f"  Explicación: {paas_result['explanation']}")
    
    # SaaS
    saas_result = classifier.classify_saas(test_text)
    print(f"SaaS: {saas_result['model']} (Confianza: {saas_result['confidence']:.2%})")
    print(f"  Explicación: {saas_result['explanation']}")
    
    # FaaS
    faas_result = classifier.classify_faas(test_text)
    print(f"FaaS: {faas_result['model']} (Confianza: {faas_result['confidence']:.2%})")
    print(f"  Explicación: {faas_result['explanation']}")
    
    print()
    
    # 3. Probar casos de error
    print("3. Casos de Error:")
    error_cases = ["", "ab", 123]
    
    for error_input in error_cases:
        print(f"  Probando: {repr(error_input)}")
        result = classifier.classify_with_confidence(error_input)
        print(f"    Resultado: {result['model']}")
        print(f"    Explicación: {result['explanation']}")
        print()

if __name__ == "__main__":
    test_new_features()


