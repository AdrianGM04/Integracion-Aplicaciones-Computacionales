package com.microservice.gui;

import com.microservice.gui.config.ConfigurationManager;
import com.microservice.gui.services.MicroserviceClient;
import com.microservice.gui.services.ServiceMonitor;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Scanner;

/**
 * Versión CLI de la aplicación para usar en Docker
 * Sin interfaz gráfica, solo línea de comandos
 */
public class MicroserviceCLI {
    
    private final ConfigurationManager configManager;
    private final MicroserviceClient microserviceClient;
    private final ServiceMonitor serviceMonitor;
    private final Scanner scanner;
    
    public MicroserviceCLI() {
        this.configManager = new ConfigurationManager();
        this.microserviceClient = new MicroserviceClient(configManager);
        this.serviceMonitor = new ServiceMonitor(microserviceClient);
        this.scanner = new Scanner(System.in);
        
        // Configurar logging
        microserviceClient.addLogListener(this::logMessage);
        serviceMonitor.addLogListener(this::logMessage);
    }
    
    private void logMessage(String message) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        System.out.println("[" + timestamp + "] " + message);
    }
    
    public void run() {
        printWelcome();
        
        // Configurar servicio
        configureService();
        
        // Iniciar monitoreo
        serviceMonitor.startMonitoring();
        
        // Menú principal
        boolean running = true;
        while (running) {
            printMenu();
            int choice = getIntInput("Selecciona una opción: ");
            
            switch (choice) {
                case 1:
                    testHealthEndpoint();
                    break;
                case 2:
                    testRegisterEndpoint();
                    break;
                case 3:
                    testLoginEndpoint();
                    break;
                case 4:
                    testProtectedEndpoint();
                    break;
                case 5:
                    testRefreshEndpoint();
                    break;
                case 6:
                    testLogoutEndpoint();
                    break;
                case 7:
                    testLogoutAllEndpoint();
                    break;
                case 8:
                    showServiceStatus();
                    break;
                case 9:
                    showConfiguration();
                    break;
                case 10:
                    updateConfiguration();
                    break;
                case 0:
                    running = false;
                    break;
                default:
                    System.out.println("Opción inválida. Intenta de nuevo.");
            }
            
            if (running) {
                System.out.println("\nPresiona Enter para continuar...");
                scanner.nextLine();
            }
        }
        
        serviceMonitor.stopMonitoring();
        System.out.println("¡Hasta luego!");
    }
    
    private void printWelcome() {
        System.out.println("========================================");
        System.out.println("Microservicio GUI - CLI (Ejercicio 9)");
        System.out.println("========================================");
        System.out.println("Versión CLI para Docker");
        System.out.println("========================================");
    }
    
    private void printMenu() {
        System.out.println("\n=== MENÚ PRINCIPAL ===");
        System.out.println("1. Health Check");
        System.out.println("2. Registrar Usuario");
        System.out.println("3. Login");
        System.out.println("4. Endpoint Protegido");
        System.out.println("5. Refresh Token");
        System.out.println("6. Logout");
        System.out.println("7. Logout All");
        System.out.println("8. Estado del Servicio");
        System.out.println("9. Ver Configuración");
        System.out.println("10. Actualizar Configuración");
        System.out.println("0. Salir");
        System.out.println("========================");
    }
    
    private void configureService() {
        System.out.println("\n=== CONFIGURACIÓN INICIAL ===");
        System.out.println("Configuración actual:");
        showConfiguration();
        
        String update = getStringInput("¿Deseas actualizar la configuración? (s/n): ");
        if ("s".equalsIgnoreCase(update) || "si".equalsIgnoreCase(update) || "y".equalsIgnoreCase(update)) {
            updateConfiguration();
        }
    }
    
    private void testHealthEndpoint() {
        System.out.println("\n=== HEALTH CHECK ===");
        String response = microserviceClient.testHealthEndpoint();
        System.out.println("Respuesta: " + response);
    }
    
    private void testRegisterEndpoint() {
        System.out.println("\n=== REGISTRAR USUARIO ===");
        String username = getStringInput("Username: ");
        String email = getStringInput("Email: ");
        String password = getStringInput("Password: ");
        
        String response = microserviceClient.testRegisterEndpoint(username, email, password);
        System.out.println("Respuesta: " + response);
    }
    
    private void testLoginEndpoint() {
        System.out.println("\n=== LOGIN ===");
        String username = getStringInput("Username: ");
        String password = getStringInput("Password: ");
        
        String response = microserviceClient.testLoginEndpoint(username, password);
        System.out.println("Respuesta: " + response);
        
        if (microserviceClient.isAuthenticated()) {
            System.out.println("✅ Login exitoso - tokens guardados");
        }
    }
    
    private void testProtectedEndpoint() {
        System.out.println("\n=== ENDPOINT PROTEGIDO ===");
        if (!microserviceClient.isAuthenticated()) {
            System.out.println("❌ No hay access token disponible. Haz login primero.");
            return;
        }
        
        String response = microserviceClient.testProtectedEndpoint();
        System.out.println("Respuesta: " + response);
    }
    
    private void testRefreshEndpoint() {
        System.out.println("\n=== REFRESH TOKEN ===");
        if (!microserviceClient.isAuthenticated()) {
            System.out.println("❌ No hay refresh token disponible. Haz login primero.");
            return;
        }
        
        String response = microserviceClient.testRefreshEndpoint();
        System.out.println("Respuesta: " + response);
    }
    
    private void testLogoutEndpoint() {
        System.out.println("\n=== LOGOUT ===");
        if (!microserviceClient.isAuthenticated()) {
            System.out.println("❌ No hay access token disponible. Haz login primero.");
            return;
        }
        
        String response = microserviceClient.testLogoutEndpoint();
        System.out.println("Respuesta: " + response);
    }
    
    private void testLogoutAllEndpoint() {
        System.out.println("\n=== LOGOUT ALL ===");
        if (!microserviceClient.isAuthenticated()) {
            System.out.println("❌ No hay access token disponible. Haz login primero.");
            return;
        }
        
        String response = microserviceClient.testLogoutAllEndpoint();
        System.out.println("Respuesta: " + response);
    }
    
    private void showServiceStatus() {
        System.out.println("\n=== ESTADO DEL SERVICIO ===");
        String status = serviceMonitor.getCurrentStatus();
        System.out.println("Estado actual: " + getStatusText(status));
        System.out.println("Monitoreo activo: " + (serviceMonitor.isMonitoring() ? "Sí" : "No"));
        
        // Verificar estado manualmente
        System.out.println("\nVerificando estado...");
        serviceMonitor.checkServiceStatus();
    }
    
    private void showConfiguration() {
        System.out.println("\n=== CONFIGURACIÓN ACTUAL ===");
        System.out.println("IP: " + configManager.getServiceIP());
        System.out.println("Puerto: " + configManager.getServicePort());
        System.out.println("URL Base: " + configManager.getBaseURL());
        System.out.println("\nEndpoints:");
        configManager.getAllEndpoints().forEach((name, path) -> 
            System.out.println("  " + name + ": " + path));
    }
    
    private void updateConfiguration() {
        System.out.println("\n=== ACTUALIZAR CONFIGURACIÓN ===");
        
        String ip = getStringInput("IP del servicio [" + configManager.getServiceIP() + "]: ");
        if (!ip.isEmpty()) {
            configManager.setServiceIP(ip);
        }
        
        String port = getStringInput("Puerto [" + configManager.getServicePort() + "]: ");
        if (!port.isEmpty()) {
            configManager.setServicePort(port);
        }
        
        configManager.updateBaseURL();
        configManager.saveConfiguration();
        
        System.out.println("✅ Configuración actualizada y guardada");
    }
    
    private String getStatusText(String status) {
        switch (status) {
            case "healthy":
                return "🟢 Servicio funcionando correctamente";
            case "degraded":
                return "🟠 Servicio degradado";
            case "down":
                return "🔴 Servicio no disponible";
            default:
                return "⚫ Estado desconocido";
        }
    }
    
    private String getStringInput(String prompt) {
        System.out.print(prompt);
        return scanner.nextLine().trim();
    }
    
    private int getIntInput(String prompt) {
        while (true) {
            try {
                System.out.print(prompt);
                return Integer.parseInt(scanner.nextLine().trim());
            } catch (NumberFormatException e) {
                System.out.println("Por favor ingresa un número válido.");
            }
        }
    }
    
    public static void main(String[] args) {
        try {
            new MicroserviceCLI().run();
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
