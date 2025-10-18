package com.microservice.gui.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

/**
 * Gestor de configuración persistente
 * Equivalente Java del configparser de Python
 */
public class ConfigurationManager {
    
    private static final String CONFIG_FILE = "microservice_config.json";
    private final Gson gson;
    private JsonObject config;
    
    public ConfigurationManager() {
        this.gson = new GsonBuilder().setPrettyPrinting().create();
        loadConfiguration();
    }
    
    private void loadConfiguration() {
        Path configPath = Paths.get(CONFIG_FILE);
        
        if (Files.exists(configPath)) {
            try (Reader reader = Files.newBufferedReader(configPath)) {
                config = JsonParser.parseReader(reader).getAsJsonObject();
            } catch (IOException e) {
                System.err.println("Error al cargar configuración: " + e.getMessage());
                createDefaultConfiguration();
            }
        } else {
            createDefaultConfiguration();
        }
    }
    
    private void createDefaultConfiguration() {
        config = new JsonObject();
        
        // Configuración del servicio
        JsonObject serviceConfig = new JsonObject();
        serviceConfig.addProperty("ip", "127.0.0.1");
        serviceConfig.addProperty("port", "5000");
        serviceConfig.addProperty("base_url", "http://127.0.0.1:5000");
        config.add("service", serviceConfig);
        
        // Configuración de endpoints
        JsonObject endpointsConfig = new JsonObject();
        endpointsConfig.addProperty("health", "/health");
        endpointsConfig.addProperty("register", "/register");
        endpointsConfig.addProperty("login", "/login");
        endpointsConfig.addProperty("protected", "/protected");
        endpointsConfig.addProperty("refresh", "/refresh");
        endpointsConfig.addProperty("logout", "/logout");
        endpointsConfig.addProperty("logout_all", "/logout_all");
        config.add("endpoints", endpointsConfig);
        
        saveConfiguration();
    }
    
    public void saveConfiguration() {
        try (Writer writer = Files.newBufferedWriter(Paths.get(CONFIG_FILE))) {
            gson.toJson(config, writer);
        } catch (IOException e) {
            System.err.println("Error al guardar configuración: " + e.getMessage());
        }
    }
    
    // Métodos para obtener configuración del servicio
    public String getServiceIP() {
        return config.getAsJsonObject("service").get("ip").getAsString();
    }
    
    public String getServicePort() {
        return config.getAsJsonObject("service").get("port").getAsString();
    }
    
    public String getBaseURL() {
        return config.getAsJsonObject("service").get("base_url").getAsString();
    }
    
    // Métodos para establecer configuración del servicio
    public void setServiceIP(String ip) {
        config.getAsJsonObject("service").addProperty("ip", ip);
    }
    
    public void setServicePort(String port) {
        config.getAsJsonObject("service").addProperty("port", port);
    }
    
    public void setBaseURL(String baseURL) {
        config.getAsJsonObject("service").addProperty("base_url", baseURL);
    }
    
    // Métodos para endpoints
    public String getEndpoint(String endpointName) {
        return config.getAsJsonObject("endpoints").get(endpointName).getAsString();
    }
    
    public void setEndpoint(String endpointName, String endpointPath) {
        config.getAsJsonObject("endpoints").addProperty(endpointName, endpointPath);
    }
    
    // Método para obtener URL completa de un endpoint
    public String getFullEndpointURL(String endpointName) {
        String baseURL = getBaseURL();
        String endpoint = getEndpoint(endpointName);
        return baseURL + endpoint;
    }
    
    // Método para actualizar URL base basada en IP y puerto
    public void updateBaseURL() {
        String ip = getServiceIP();
        String port = getServicePort();
        String baseURL = "http://" + ip + ":" + port;
        setBaseURL(baseURL);
    }
    
    // Método para obtener todos los endpoints como mapa
    public Map<String, String> getAllEndpoints() {
        Map<String, String> endpoints = new HashMap<>();
        JsonObject endpointsObj = config.getAsJsonObject("endpoints");
        
        for (String key : endpointsObj.keySet()) {
            endpoints.put(key, endpointsObj.get(key).getAsString());
        }
        
        return endpoints;
    }
    
    // Método para restaurar configuración por defecto
    public void restoreDefaultEndpoints() {
        JsonObject endpointsConfig = new JsonObject();
        endpointsConfig.addProperty("health", "/health");
        endpointsConfig.addProperty("register", "/register");
        endpointsConfig.addProperty("login", "/login");
        endpointsConfig.addProperty("protected", "/protected");
        endpointsConfig.addProperty("refresh", "/refresh");
        endpointsConfig.addProperty("logout", "/logout");
        endpointsConfig.addProperty("logout_all", "/logout_all");
        config.add("endpoints", endpointsConfig);
    }
}
