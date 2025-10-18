package com.microservice.gui.components;

import com.microservice.gui.services.MicroserviceClient;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;

/**
 * Panel para endpoint protegido
 * Equivalente Java de la pestaña de endpoint protegido de Tkinter
 */
public class ProtectedPanel extends JPanel {
    
    private final MicroserviceClient microserviceClient;
    private final LogPanel logPanel;
    private JTextArea responseTextArea;
    
    public ProtectedPanel(MicroserviceClient microserviceClient, LogPanel logPanel) {
        this.microserviceClient = microserviceClient;
        this.logPanel = logPanel;
        initializeComponents();
        setupLayout();
    }
    
    private void initializeComponents() {
        // Área de texto para respuesta
        responseTextArea = new JTextArea(15, 80);
        responseTextArea.setEditable(false);
        responseTextArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        responseTextArea.setBackground(Color.BLACK);
        responseTextArea.setForeground(Color.WHITE);
    }
    
    private void setupLayout() {
        setLayout(new BorderLayout());
        setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Panel de información
        JPanel infoPanel = createInfoPanel();
        add(infoPanel, BorderLayout.NORTH);
        
        // Panel de prueba
        JPanel testPanel = createTestPanel();
        add(testPanel, BorderLayout.CENTER);
        
        // Panel de respuesta
        JPanel responsePanel = createResponsePanel();
        add(responsePanel, BorderLayout.SOUTH);
    }
    
    private JPanel createInfoPanel() {
        JPanel panel = new JPanel();
        panel.setBorder(BorderFactory.createTitledBorder("Información del Endpoint"));
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        
        JLabel endpointLabel = new JLabel("Endpoint: /protected");
        JLabel methodLabel = new JLabel("Método: GET");
        JLabel descriptionLabel = new JLabel("Descripción: Endpoint protegido que requiere autenticación JWT");
        JLabel authLabel = new JLabel("Autenticación: Bearer Token (JWT)");
        
        panel.add(endpointLabel);
        panel.add(methodLabel);
        panel.add(descriptionLabel);
        panel.add(authLabel);
        
        return panel;
    }
    
    private JPanel createTestPanel() {
        JPanel panel = new JPanel();
        panel.setBorder(BorderFactory.createTitledBorder("Prueba del Endpoint"));
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        
        // Información sobre autenticación
        JPanel authInfoPanel = new JPanel();
        authInfoPanel.setLayout(new BoxLayout(authInfoPanel, BoxLayout.Y_AXIS));
        authInfoPanel.setBackground(new Color(255, 255, 200));
        authInfoPanel.setBorder(BorderFactory.createTitledBorder("Estado de Autenticación"));
        
        JLabel authStatusLabel = new JLabel("Estado: No verificado");
        JLabel tokenLabel = new JLabel("Token: No disponible");
        
        authInfoPanel.add(authStatusLabel);
        authInfoPanel.add(tokenLabel);
        
        // Botón de prueba
        JButton testButton = new JButton("Probar Endpoint Protegido");
        testButton.addActionListener(e -> testProtectedEndpoint(e, authStatusLabel, tokenLabel));
        
        panel.add(authInfoPanel);
        panel.add(Box.createVerticalStrut(10));
        panel.add(testButton);
        
        return panel;
    }
    
    private JPanel createResponsePanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder("Respuesta"));
        
        JScrollPane responseScrollPane = new JScrollPane(responseTextArea);
        responseScrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
        responseScrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);
        
        panel.add(responseScrollPane, BorderLayout.CENTER);
        
        return panel;
    }
    
    private void testProtectedEndpoint(ActionEvent e, JLabel authStatusLabel, JLabel tokenLabel) {
        // Verificar estado de autenticación
        if (!microserviceClient.isAuthenticated()) {
            JOptionPane.showMessageDialog(this, 
                "No hay access token disponible.\n" +
                "Por favor, use la pestaña 'Autenticación' para hacer login primero.", 
                "Error de Autenticación", 
                JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        // Actualizar información de autenticación
        authStatusLabel.setText("Estado: Autenticado");
        tokenLabel.setText("Token: " + microserviceClient.getAccessToken().substring(0, Math.min(30, microserviceClient.getAccessToken().length())) + "...");
        
        // Ejecutar en hilo separado para no bloquear la UI
        SwingUtilities.invokeLater(() -> {
            new Thread(() -> {
                try {
                    String response = microserviceClient.testProtectedEndpoint();
                    
                    // Actualizar UI en el hilo de eventos
                    SwingUtilities.invokeLater(() -> {
                        responseTextArea.setText(response);
                        responseTextArea.setCaretPosition(0); // Scroll al inicio
                    });
                    
                } catch (Exception ex) {
                    String errorMessage = "Error: " + ex.getMessage();
                    SwingUtilities.invokeLater(() -> {
                        responseTextArea.setText(errorMessage);
                        responseTextArea.setCaretPosition(0);
                    });
                    logPanel.logMessage("Error en /protected: " + ex.getMessage(), "ERROR");
                }
            }).start();
        });
    }
}
