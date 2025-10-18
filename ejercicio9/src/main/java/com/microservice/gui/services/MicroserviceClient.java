package com.microservice.gui.services;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.microservice.gui.config.ConfigurationManager;
import okhttp3.*;

import java.io.IOException;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

/**
 * Cliente HTTP para consumir endpoints del microservicio
 * Equivalente Java de requests en Python
 */
public class MicroserviceClient {
    
    public final ConfigurationManager configManager;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private Consumer<String> logListener;
    
    // Tokens de autenticación
    private String accessToken;
    private String refreshToken;
    private String sessionId;
    
    public MicroserviceClient(ConfigurationManager configManager) {
        this.configManager = configManager;
        this.gson = new Gson();
        
        // Configurar cliente HTTP con timeouts
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .writeTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .build();
    }
    
    public void addLogListener(Consumer<String> logListener) {
        this.logListener = logListener;
    }
    
    private void log(String message, String level) {
        if (logListener != null) {
            logListener.accept("[" + level + "] " + message);
        }
    }
    
    // Método genérico para hacer peticiones HTTP
    private String makeRequest(String method, String url, String jsonBody, String authToken) throws IOException {
        Request.Builder requestBuilder = new Request.Builder().url(url);
        
        // Configurar método HTTP
        if ("GET".equals(method)) {
            requestBuilder.get();
        } else if ("POST".equals(method)) {
            RequestBody body = RequestBody.create(
                jsonBody != null ? jsonBody : "", 
                MediaType.get("application/json; charset=utf-8")
            );
            requestBuilder.post(body);
        }
        
        // Agregar headers
        requestBuilder.addHeader("Content-Type", "application/json");
        if (authToken != null && !authToken.isEmpty()) {
            requestBuilder.addHeader("Authorization", "Bearer " + authToken);
        }
        
        Request request = requestBuilder.build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            log("Status Code: " + response.code(), "INFO");
            log("Response: " + responseBody, "INFO");
            
            return responseBody;
        }
    }
    
    // Health Check
    public String testHealthEndpoint() {
        try {
            String url = configManager.getFullEndpointURL("health");
            log("Probando endpoint /health: " + url, "INFO");
            
            String response = makeRequest("GET", url, null, null);
            log("Respuesta de /health exitosa", "INFO");
            return response;
            
        } catch (IOException e) {
            log("Error en /health: " + e.getMessage(), "ERROR");
            return "Error: " + e.getMessage();
        }
    }
    
    // Register
    public String testRegisterEndpoint(String username, String email, String password) {
        try {
            String url = configManager.getFullEndpointURL("register");
            
            JsonObject data = new JsonObject();
            data.addProperty("username", username);
            data.addProperty("email", email);
            data.addProperty("password", password);
            
            String jsonBody = gson.toJson(data);
            
            log("Probando endpoint /register: " + url, "INFO");
            log("Datos enviados: " + jsonBody, "INFO");
            
            String response = makeRequest("POST", url, jsonBody, null);
            log("Respuesta de /register: " + response, "INFO");
            
            return response;
            
        } catch (IOException e) {
            log("Error en /register: " + e.getMessage(), "ERROR");
            return "Error: " + e.getMessage();
        }
    }
    
    // Login
    public String testLoginEndpoint(String username, String password) {
        try {
            String url = configManager.getFullEndpointURL("login");
            
            JsonObject data = new JsonObject();
            data.addProperty("username", username);
            data.addProperty("password", password);
            
            String jsonBody = gson.toJson(data);
            
            log("Probando endpoint /login: " + url, "INFO");
            log("Datos enviados: " + jsonBody, "INFO");
            
            String response = makeRequest("POST", url, jsonBody, null);
            
            // Procesar respuesta para extraer tokens
            try {
                JsonObject responseJson = JsonParser.parseString(response).getAsJsonObject();
                if (responseJson.has("access_token")) {
                    accessToken = responseJson.get("access_token").getAsString();
                    refreshToken = responseJson.get("refresh_token").getAsString();
                    sessionId = responseJson.get("session_id").getAsString();
                    
                    log("Login exitoso - tokens guardados", "INFO");
                    log("Session ID: " + sessionId, "INFO");
                    log("Access Token: " + accessToken.substring(0, Math.min(50, accessToken.length())) + "...", "INFO");
                    log("Refresh Token: " + refreshToken.substring(0, Math.min(50, refreshToken.length())) + "...", "INFO");
                }
            } catch (Exception e) {
                log("Error al procesar respuesta de login: " + e.getMessage(), "WARNING");
            }
            
            log("Respuesta de /login: " + response, "INFO");
            return response;
            
        } catch (IOException e) {
            log("Error en /login: " + e.getMessage(), "ERROR");
            return "Error: " + e.getMessage();
        }
    }
    
    // Refresh Token
    public String testRefreshEndpoint() {
        if (refreshToken == null || refreshToken.isEmpty()) {
            log("No hay refresh token disponible. Haga login primero.", "ERROR");
            return "Error: No hay refresh token disponible";
        }
        
        try {
            String url = configManager.getFullEndpointURL("refresh");
            log("Probando endpoint /refresh: " + url, "INFO");
            
            String response = makeRequest("POST", url, null, refreshToken);
            
            // Procesar respuesta para extraer nuevo access token
            try {
                JsonObject responseJson = JsonParser.parseString(response).getAsJsonObject();
                if (responseJson.has("access_token")) {
                    accessToken = responseJson.get("access_token").getAsString();
                    log("Access token renovado", "INFO");
                }
            } catch (Exception e) {
                log("Error al procesar respuesta de refresh: " + e.getMessage(), "WARNING");
            }
            
            log("Respuesta de /refresh: " + response, "INFO");
            return response;
            
        } catch (IOException e) {
            log("Error en /refresh: " + e.getMessage(), "ERROR");
            return "Error: " + e.getMessage();
        }
    }
    
    // Logout
    public String testLogoutEndpoint() {
        if (accessToken == null || accessToken.isEmpty()) {
            log("No hay access token disponible. Haga login primero.", "ERROR");
            return "Error: No hay access token disponible";
        }
        
        try {
            String url = configManager.getFullEndpointURL("logout");
            log("Probando endpoint /logout: " + url, "INFO");
            
            String response = makeRequest("POST", url, null, accessToken);
            
            // Limpiar tokens
            accessToken = null;
            log("Logout exitoso - access token revocado", "INFO");
            
            log("Respuesta de /logout: " + response, "INFO");
            return response;
            
        } catch (IOException e) {
            log("Error en /logout: " + e.getMessage(), "ERROR");
            return "Error: " + e.getMessage();
        }
    }
    
    // Logout All
    public String testLogoutAllEndpoint() {
        if (accessToken == null || accessToken.isEmpty()) {
            log("No hay access token disponible. Haga login primero.", "ERROR");
            return "Error: No hay access token disponible";
        }
        
        try {
            String url = configManager.getFullEndpointURL("logout_all");
            log("Probando endpoint /logout_all: " + url, "INFO");
            
            String response = makeRequest("POST", url, null, accessToken);
            
            // Limpiar todos los tokens
            accessToken = null;
            refreshToken = null;
            sessionId = null;
            log("Logout all exitoso - todos los tokens revocados", "INFO");
            
            log("Respuesta de /logout_all: " + response, "INFO");
            return response;
            
        } catch (IOException e) {
            log("Error en /logout_all: " + e.getMessage(), "ERROR");
            return "Error: " + e.getMessage();
        }
    }
    
    // Protected Endpoint
    public String testProtectedEndpoint() {
        if (accessToken == null || accessToken.isEmpty()) {
            log("No hay access token disponible. Haga login primero.", "ERROR");
            return "Error: No hay access token disponible";
        }
        
        try {
            String url = configManager.getFullEndpointURL("protected");
            log("Probando endpoint /protected: " + url, "INFO");
            
            String response = makeRequest("GET", url, null, accessToken);
            log("Acceso a endpoint protegido exitoso", "INFO");
            
            log("Respuesta de /protected: " + response, "INFO");
            return response;
            
        } catch (IOException e) {
            log("Error en /protected: " + e.getMessage(), "ERROR");
            return "Error: " + e.getMessage();
        }
    }
    
    // Getters para tokens
    public String getAccessToken() {
        return accessToken;
    }
    
    public String getRefreshToken() {
        return refreshToken;
    }
    
    public String getSessionId() {
        return sessionId;
    }
    
    public boolean isAuthenticated() {
        return accessToken != null && !accessToken.isEmpty();
    }
}
