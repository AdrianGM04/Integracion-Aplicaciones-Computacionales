package com.microservice.gui;

import com.microservice.gui.components.*;
import com.microservice.gui.config.ConfigurationManager;
import com.microservice.gui.services.MicroserviceClient;
import com.microservice.gui.services.ServiceMonitor;

import javax.swing.*;
import java.awt.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

/**
 * Aplicación principal con GUI para consumir endpoints del microservicio
 * Equivalente Java del ejercicio 8 en Python
 */
public class MicroserviceGUI extends JFrame {
    
    private ConfigurationManager configManager;
    private MicroserviceClient microserviceClient;
    private ServiceMonitor serviceMonitor;
    
    // Componentes principales
    private StatusIndicator statusIndicator;
    private LogPanel logPanel;
    private ConfigPanel configPanel;
    private HealthPanel healthPanel;
    private AuthPanel authPanel;
    private ProtectedPanel protectedPanel;
    
    public MicroserviceGUI() {
        initializeComponents();
        setupGUI();
        startServiceMonitoring();
    }
    
    private void initializeComponents() {
        // Inicializar servicios
        configManager = new ConfigurationManager();
        microserviceClient = new MicroserviceClient(configManager);
        serviceMonitor = new ServiceMonitor(microserviceClient);
        
        // Inicializar componentes
        statusIndicator = new StatusIndicator(serviceMonitor);
        logPanel = new LogPanel();
        configPanel = new ConfigPanel(configManager, logPanel);
        healthPanel = new HealthPanel(microserviceClient, logPanel);
        authPanel = new AuthPanel(microserviceClient, logPanel);
        protectedPanel = new ProtectedPanel(microserviceClient, logPanel);
        
        // Configurar callbacks
        setupCallbacks();
    }
    
    private void setupGUI() {
        setTitle("Microservicio GUI - Consumidor de Endpoints (Java)");
        setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
        setSize(1200, 800);
        setLocationRelativeTo(null);
        
        // Configurar cierre de ventana
        addWindowListener(new WindowAdapter() {
            @Override
            public void windowClosing(WindowEvent e) {
                logPanel.logMessage("Aplicación cerrada", "INFO");
                dispose();
                System.exit(0);
            }
        });
        
        // Layout principal
        setLayout(new BorderLayout());
        
        // Panel superior con título y semáforo
        JPanel topPanel = createTopPanel();
        add(topPanel, BorderLayout.NORTH);
        
        // Panel principal con pestañas
        JTabbedPane tabbedPane = createTabbedPane();
        add(tabbedPane, BorderLayout.CENTER);
        
        // Aplicar Look and Feel moderno
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            SwingUtilities.updateComponentTreeUI(this);
        } catch (Exception e) {
            logPanel.logMessage("Error al aplicar Look and Feel: " + e.getMessage(), "WARNING");
        }
    }
    
    private JPanel createTopPanel() {
        JPanel topPanel = new JPanel(new BorderLayout());
        topPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        topPanel.setBackground(new Color(240, 240, 240));
        
        // Título
        JLabel titleLabel = new JLabel("Microservicio GUI - Consumidor de Endpoints (Java)");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 16));
        titleLabel.setHorizontalAlignment(SwingConstants.CENTER);
        topPanel.add(titleLabel, BorderLayout.NORTH);
        
        // Semáforo de estado
        topPanel.add(statusIndicator, BorderLayout.CENTER);
        
        return topPanel;
    }
    
    private JTabbedPane createTabbedPane() {
        JTabbedPane tabbedPane = new JTabbedPane();
        
        // Pestaña de configuración
        tabbedPane.addTab("Configuración", configPanel);
        
        // Pestaña de logs
        tabbedPane.addTab("Logs de Actividad", logPanel);
        
        // Pestaña de health check
        tabbedPane.addTab("Health Check", healthPanel);
        
        // Pestaña de autenticación
        tabbedPane.addTab("Autenticación", authPanel);
        
        // Pestaña de endpoint protegido
        tabbedPane.addTab("Endpoint Protegido", protectedPanel);
        
        return tabbedPane;
    }
    
    private void setupCallbacks() {
        // Configurar callbacks para actualización de estado
        serviceMonitor.addStatusChangeListener(statusIndicator::updateStatus);
        
        // Configurar callbacks para logs
        microserviceClient.addLogListener(message -> logPanel.logMessage(message, "INFO"));
        serviceMonitor.addLogListener(message -> logPanel.logMessage(message, "INFO"));
    }
    
    private void startServiceMonitoring() {
        // Iniciar monitoreo del servicio en hilo separado
        Thread monitorThread = new Thread(() -> {
            serviceMonitor.startMonitoring();
        });
        monitorThread.setDaemon(true);
        monitorThread.start();
        
        logPanel.logMessage("Sistema iniciado - Java", "INFO");
    }
    
    public static void main(String[] args) {
        // Configurar Look and Feel
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            System.err.println("Error al configurar Look and Feel: " + e.getMessage());
        }
        
        // Ejecutar en Event Dispatch Thread
        SwingUtilities.invokeLater(() -> {
            try {
                new MicroserviceGUI().setVisible(true);
            } catch (Exception e) {
                JOptionPane.showMessageDialog(null, 
                    "Error al iniciar la aplicación: " + e.getMessage(),
                    "Error", 
                    JOptionPane.ERROR_MESSAGE);
                e.printStackTrace();
            }
        });
    }
}
