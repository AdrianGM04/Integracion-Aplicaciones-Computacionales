package com.microservice.gui.components;

import com.microservice.gui.services.MicroserviceClient;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;

/**
 * Panel para endpoint /health
 * Equivalente Java de la pestaña de health check de Tkinter
 */
public class HealthPanel extends JPanel {
    
    private final MicroserviceClient microserviceClient;
    private final LogPanel logPanel;
    private JTextArea responseTextArea;
    
    public HealthPanel(MicroserviceClient microserviceClient, LogPanel logPanel) {
        this.microserviceClient = microserviceClient;
        this.logPanel = logPanel;
        initializeComponents();
        setupLayout();
    }
    
    private void initializeComponents() {
        // Área de texto para respuesta
        responseTextArea = new JTextArea(10, 80);
        responseTextArea.setEditable(false);
        responseTextArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        responseTextArea.setBackground(Color.BLACK);
        responseTextArea.setForeground(Color.WHITE);
        
        // Scroll pane para el área de texto
        JScrollPane responseScrollPane = new JScrollPane(responseTextArea);
        responseScrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
        responseScrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);
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
        
        JLabel endpointLabel = new JLabel("Endpoint: /health");
        JLabel methodLabel = new JLabel("Método: GET");
        JLabel descriptionLabel = new JLabel("Descripción: Verifica el estado del microservicio y la base de datos");
        
        panel.add(endpointLabel);
        panel.add(methodLabel);
        panel.add(descriptionLabel);
        
        return panel;
    }
    
    private JPanel createTestPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        
        JButton testButton = new JButton("Verificar Estado del Servicio");
        testButton.addActionListener(this::testHealthEndpoint);
        
        panel.add(testButton);
        
        return panel;
    }
    
    private JPanel createResponsePanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder("Respuesta"));
        
        JTextArea responseTextArea = new JTextArea(10, 80);
        responseTextArea.setEditable(false);
        responseTextArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        responseTextArea.setBackground(Color.BLACK);
        responseTextArea.setForeground(Color.WHITE);
        
        JScrollPane responseScrollPane = new JScrollPane(responseTextArea);
        responseScrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
        responseScrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);
        
        panel.add(responseScrollPane, BorderLayout.CENTER);
        
        // Guardar referencia para uso posterior
        this.responseTextArea = responseTextArea;
        
        return panel;
    }
    
    private void testHealthEndpoint(ActionEvent e) {
        // Ejecutar en hilo separado para no bloquear la UI
        SwingUtilities.invokeLater(() -> {
            new Thread(() -> {
                try {
                    String response = microserviceClient.testHealthEndpoint();
                    
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
                    logPanel.logMessage("Error en /health: " + ex.getMessage(), "ERROR");
                }
            }).start();
        });
    }
}
