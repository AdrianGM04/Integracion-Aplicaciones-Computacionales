package com.microservice.gui.components;

import com.microservice.gui.config.ConfigurationManager;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.util.Map;

/**
 * Panel de configuración del servicio
 * Equivalente Java de la pestaña de configuración de Tkinter
 */
public class ConfigPanel extends JPanel {
    
    private final ConfigurationManager configManager;
    private final LogPanel logPanel;
    
    private JTextField ipField;
    private JTextField portField;
    private JTextField baseUrlField;
    private JTable endpointsTable;
    private DefaultTableModel tableModel;
    
    public ConfigPanel(ConfigurationManager configManager, LogPanel logPanel) {
        this.configManager = configManager;
        this.logPanel = logPanel;
        initializeComponents();
        setupLayout();
        loadCurrentConfig();
    }
    
    private void initializeComponents() {
        // Campos de configuración del servicio
        ipField = new JTextField(20);
        portField = new JTextField(20);
        baseUrlField = new JTextField(40);
        
        // Botones de configuración
        JButton updateUrlButton = new JButton("Actualizar URL");
        updateUrlButton.addActionListener(this::updateBaseUrl);
        
        JButton saveConfigButton = new JButton("Guardar Configuración");
        saveConfigButton.addActionListener(this::saveServiceConfig);
        
        JButton loadConfigButton = new JButton("Cargar Configuración");
        loadConfigButton.addActionListener(this::loadServiceConfig);
        
        // Tabla de endpoints
        String[] columnNames = {"Endpoint", "Ruta", "Método"};
        tableModel = new DefaultTableModel(columnNames, 0) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return column == 1; // Solo permitir editar la ruta
            }
        };
        endpointsTable = new JTable(tableModel);
        endpointsTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        
        // Botones para endpoints
        JButton saveEndpointsButton = new JButton("Guardar Endpoints");
        saveEndpointsButton.addActionListener(this::saveEndpointsConfig);
        
        JButton restoreDefaultsButton = new JButton("Restaurar Defaults");
        restoreDefaultsButton.addActionListener(this::restoreDefaultEndpoints);
    }
    
    private void setupLayout() {
        setLayout(new BorderLayout());
        setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Panel principal con scroll
        JScrollPane scrollPane = new JScrollPane();
        JPanel mainPanel = new JPanel();
        mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
        
        // Sección de configuración del servicio
        JPanel serviceConfigPanel = createServiceConfigPanel();
        mainPanel.add(serviceConfigPanel);
        mainPanel.add(Box.createVerticalStrut(20));
        
        // Sección de configuración de endpoints
        JPanel endpointsConfigPanel = createEndpointsConfigPanel();
        mainPanel.add(endpointsConfigPanel);
        
        scrollPane.setViewportView(mainPanel);
        add(scrollPane, BorderLayout.CENTER);
    }
    
    private JPanel createServiceConfigPanel() {
        JPanel panel = new JPanel();
        panel.setBorder(BorderFactory.createTitledBorder("Configuración del Servicio"));
        panel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.anchor = GridBagConstraints.WEST;
        
        // IP
        gbc.gridx = 0; gbc.gridy = 0;
        panel.add(new JLabel("IP del Servicio:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.weightx = 1.0;
        panel.add(ipField, gbc);
        
        // Puerto
        gbc.gridx = 0; gbc.gridy = 1; gbc.fill = GridBagConstraints.NONE; gbc.weightx = 0;
        panel.add(new JLabel("Puerto:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.weightx = 1.0;
        panel.add(portField, gbc);
        
        // URL Base
        gbc.gridx = 0; gbc.gridy = 2; gbc.fill = GridBagConstraints.NONE; gbc.weightx = 0;
        panel.add(new JLabel("URL Base:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.weightx = 1.0;
        panel.add(baseUrlField, gbc);
        
        // Botones
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton updateUrlButton = new JButton("Actualizar URL");
        updateUrlButton.addActionListener(this::updateBaseUrl);
        JButton saveConfigButton = new JButton("Guardar Configuración");
        saveConfigButton.addActionListener(this::saveServiceConfig);
        JButton loadConfigButton = new JButton("Cargar Configuración");
        loadConfigButton.addActionListener(this::loadServiceConfig);
        
        buttonPanel.add(updateUrlButton);
        buttonPanel.add(saveConfigButton);
        buttonPanel.add(loadConfigButton);
        
        gbc.gridx = 0; gbc.gridy = 3; gbc.gridwidth = 2; gbc.fill = GridBagConstraints.NONE; gbc.weightx = 0;
        panel.add(buttonPanel, gbc);
        
        return panel;
    }
    
    private JPanel createEndpointsConfigPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder("Configuración de Endpoints"));
        
        // Tabla de endpoints
        JScrollPane tableScrollPane = new JScrollPane(endpointsTable);
        tableScrollPane.setPreferredSize(new Dimension(600, 200));
        panel.add(tableScrollPane, BorderLayout.CENTER);
        
        // Botones para endpoints
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton saveEndpointsButton = new JButton("Guardar Endpoints");
        saveEndpointsButton.addActionListener(this::saveEndpointsConfig);
        JButton restoreDefaultsButton = new JButton("Restaurar Defaults");
        restoreDefaultsButton.addActionListener(this::restoreDefaultEndpoints);
        
        buttonPanel.add(saveEndpointsButton);
        buttonPanel.add(restoreDefaultsButton);
        panel.add(buttonPanel, BorderLayout.SOUTH);
        
        return panel;
    }
    
    private void loadCurrentConfig() {
        // Cargar configuración del servicio
        ipField.setText(configManager.getServiceIP());
        portField.setText(configManager.getServicePort());
        baseUrlField.setText(configManager.getBaseURL());
        
        // Cargar endpoints
        loadEndpointsToTable();
    }
    
    private void loadEndpointsToTable() {
        tableModel.setRowCount(0); // Limpiar tabla
        
        Map<String, String> endpoints = configManager.getAllEndpoints();
        String[] methods = {"GET", "POST", "POST", "GET", "POST", "POST", "POST"};
        String[] endpointNames = {"health", "register", "login", "protected", "refresh", "logout", "logout_all"};
        
        for (int i = 0; i < endpointNames.length; i++) {
            String endpointName = endpointNames[i];
            String path = endpoints.get(endpointName);
            String method = methods[i];
            tableModel.addRow(new Object[]{endpointName, path, method});
        }
    }
    
    private void updateBaseUrl(ActionEvent e) {
        String ip = ipField.getText().trim();
        String port = portField.getText().trim();
        
        if (ip.isEmpty() || port.isEmpty()) {
            JOptionPane.showMessageDialog(this, "IP y Puerto son requeridos", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        String baseUrl = "http://" + ip + ":" + port;
        baseUrlField.setText(baseUrl);
        logPanel.logMessage("URL base actualizada: " + baseUrl, "INFO");
    }
    
    private void saveServiceConfig(ActionEvent e) {
        configManager.setServiceIP(ipField.getText());
        configManager.setServicePort(portField.getText());
        configManager.setBaseURL(baseUrlField.getText());
        configManager.saveConfiguration();
        
        logPanel.logMessage("Configuración del servicio guardada", "INFO");
        JOptionPane.showMessageDialog(this, "Configuración guardada correctamente", "Éxito", JOptionPane.INFORMATION_MESSAGE);
    }
    
    private void loadServiceConfig(ActionEvent e) {
        loadCurrentConfig();
        logPanel.logMessage("Configuración del servicio cargada", "INFO");
    }
    
    private void saveEndpointsConfig(ActionEvent e) {
        // Guardar endpoints desde la tabla
        for (int i = 0; i < tableModel.getRowCount(); i++) {
            String endpointName = (String) tableModel.getValueAt(i, 0);
            String endpointPath = (String) tableModel.getValueAt(i, 1);
            configManager.setEndpoint(endpointName, endpointPath);
        }
        
        configManager.saveConfiguration();
        logPanel.logMessage("Configuración de endpoints guardada", "INFO");
        JOptionPane.showMessageDialog(this, "Endpoints guardados correctamente", "Éxito", JOptionPane.INFORMATION_MESSAGE);
    }
    
    private void restoreDefaultEndpoints(ActionEvent e) {
        configManager.restoreDefaultEndpoints();
        loadEndpointsToTable();
        logPanel.logMessage("Endpoints restaurados a valores por defecto", "INFO");
    }
}
