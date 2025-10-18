package com.microservice.gui.services;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

/**
 * Monitor de estado del microservicio
 * Equivalente Java del monitoreo automático de Python
 */
public class ServiceMonitor {
    
    private final MicroserviceClient microserviceClient;
    private final OkHttpClient httpClient;
    private Consumer<String> logListener;
    private Consumer<String> statusChangeListener;
    
    private volatile boolean monitoring = false;
    private volatile String currentStatus = "unknown";
    private Thread monitoringThread;
    
    public ServiceMonitor(MicroserviceClient microserviceClient) {
        this.microserviceClient = microserviceClient;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(5, TimeUnit.SECONDS)
                .readTimeout(5, TimeUnit.SECONDS)
                .build();
    }
    
    public void addLogListener(Consumer<String> logListener) {
        this.logListener = logListener;
    }
    
    public void addStatusChangeListener(Consumer<String> statusChangeListener) {
        this.statusChangeListener = statusChangeListener;
    }
    
    private void log(String message, String level) {
        if (logListener != null) {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
            logListener.accept("[" + timestamp + "] [" + level + "] " + message);
        }
    }
    
    public void startMonitoring() {
        if (monitoring) {
            return;
        }
        
        monitoring = true;
        monitoringThread = new Thread(this::monitorLoop);
        monitoringThread.setDaemon(true);
        monitoringThread.start();
        
        log("Monitoreo del servicio iniciado", "INFO");
    }
    
    public void stopMonitoring() {
        monitoring = false;
        if (monitoringThread != null) {
            monitoringThread.interrupt();
        }
        log("Monitoreo del servicio detenido", "INFO");
    }
    
    private void monitorLoop() {
        while (monitoring && !Thread.currentThread().isInterrupted()) {
            try {
                checkServiceStatus();
                Thread.sleep(30000); // Verificar cada 30 segundos
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                log("Error en monitoreo: " + e.getMessage(), "ERROR");
                try {
                    Thread.sleep(30000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
    }
    
    public void checkServiceStatus() {
        try {
            String baseURL = microserviceClient.configManager.getBaseURL();
            String healthURL = baseURL + "/health";
            
            log("Verificando estado del servicio: " + healthURL, "INFO");
            
            Request request = new Request.Builder()
                    .url(healthURL)
                    .build();
            
            try (Response response = httpClient.newCall(request).execute()) {
                String responseBody = response.body() != null ? response.body().string() : "";
                
                if (response.isSuccessful()) {
                    try {
                        JsonObject data = JsonParser.parseString(responseBody).getAsJsonObject();
                        String status = data.get("status").getAsString();
                        
                        if ("ok".equals(status)) {
                            updateStatus("healthy");
                            log("Servicio funcionando correctamente", "INFO");
                        } else {
                            updateStatus("degraded");
                            String error = data.has("error") ? data.get("error").getAsString() : "Error desconocido";
                            log("Servicio degradado: " + error, "WARNING");
                        }
                    } catch (Exception e) {
                        updateStatus("degraded");
                        log("Error al procesar respuesta del servicio: " + e.getMessage(), "WARNING");
                    }
                } else {
                    updateStatus("down");
                    log("Servicio no disponible. Código: " + response.code(), "ERROR");
                }
            }
            
        } catch (IOException e) {
            if (e.getMessage().contains("Connection refused") || e.getMessage().contains("ConnectException")) {
                updateStatus("down");
                log("No se puede conectar al servicio", "ERROR");
            } else if (e.getMessage().contains("timeout")) {
                updateStatus("down");
                log("Timeout al conectar al servicio", "ERROR");
            } else {
                updateStatus("unknown");
                log("Error al verificar servicio: " + e.getMessage(), "ERROR");
            }
        } catch (Exception e) {
            updateStatus("unknown");
            log("Error inesperado al verificar servicio: " + e.getMessage(), "ERROR");
        }
    }
    
    private void updateStatus(String newStatus) {
        if (!newStatus.equals(currentStatus)) {
            currentStatus = newStatus;
            if (statusChangeListener != null) {
                statusChangeListener.accept(newStatus);
            }
        }
    }
    
    public String getCurrentStatus() {
        return currentStatus;
    }
    
    public boolean isMonitoring() {
        return monitoring;
    }
}
