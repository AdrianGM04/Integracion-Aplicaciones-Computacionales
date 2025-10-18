package com.microservice.gui.components;

import com.microservice.gui.services.MicroserviceClient;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;

/**
 * Panel para endpoints de autenticación
 * Equivalente Java de la pestaña de autenticación de Tkinter
 */
public class AuthPanel extends JPanel {
    
    private final MicroserviceClient microserviceClient;
    private final LogPanel logPanel;
    
    // Componentes de registro
    private JTextField registerUsernameField;
    private JTextField registerEmailField;
    private JPasswordField registerPasswordField;
    private JTextArea registerResponseArea;
    
    // Componentes de login
    private JTextField loginUsernameField;
    private JPasswordField loginPasswordField;
    private JTextArea loginResponseArea;
    private JTextArea authStatusArea;
    
    // Componentes de refresh
    private JTextArea refreshResponseArea;
    
    // Componentes de logout
    private JTextArea logoutResponseArea;
    
    public AuthPanel(MicroserviceClient microserviceClient, LogPanel logPanel) {
        this.microserviceClient = microserviceClient;
        this.logPanel = logPanel;
        initializeComponents();
        setupLayout();
    }
    
    private void initializeComponents() {
        // Campos de registro
        registerUsernameField = new JTextField(30);
        registerEmailField = new JTextField(30);
        registerPasswordField = new JPasswordField(30);
        registerResponseArea = createResponseTextArea();
        
        // Campos de login
        loginUsernameField = new JTextField(30);
        loginPasswordField = new JPasswordField(30);
        loginResponseArea = createResponseTextArea();
        
        // Área de estado de autenticación
        authStatusArea = new JTextArea(4, 50);
        authStatusArea.setEditable(false);
        authStatusArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        authStatusArea.setBackground(Color.LIGHT_GRAY);
        
        // Áreas de respuesta
        refreshResponseArea = createResponseTextArea();
        logoutResponseArea = createResponseTextArea();
    }
    
    private JTextArea createResponseTextArea() {
        JTextArea textArea = new JTextArea(8, 60);
        textArea.setEditable(false);
        textArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        textArea.setBackground(Color.BLACK);
        textArea.setForeground(Color.WHITE);
        return textArea;
    }
    
    private void setupLayout() {
        setLayout(new BorderLayout());
        setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Crear pestañas
        JTabbedPane tabbedPane = new JTabbedPane();
        
        // Pestaña de registro
        tabbedPane.addTab("Registro", createRegisterPanel());
        
        // Pestaña de login
        tabbedPane.addTab("Login", createLoginPanel());
        
        // Pestaña de refresh
        tabbedPane.addTab("Refresh Token", createRefreshPanel());
        
        // Pestaña de logout
        tabbedPane.addTab("Logout", createLogoutPanel());
        
        add(tabbedPane, BorderLayout.CENTER);
    }
    
    private JPanel createRegisterPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Formulario de registro
        JPanel formPanel = new JPanel();
        formPanel.setBorder(BorderFactory.createTitledBorder("Registrar Nuevo Usuario"));
        formPanel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.anchor = GridBagConstraints.WEST;
        
        // Username
        gbc.gridx = 0; gbc.gridy = 0;
        formPanel.add(new JLabel("Username:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.weightx = 1.0;
        formPanel.add(registerUsernameField, gbc);
        
        // Email
        gbc.gridx = 0; gbc.gridy = 1; gbc.fill = GridBagConstraints.NONE; gbc.weightx = 0;
        formPanel.add(new JLabel("Email:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.weightx = 1.0;
        formPanel.add(registerEmailField, gbc);
        
        // Password
        gbc.gridx = 0; gbc.gridy = 2; gbc.fill = GridBagConstraints.NONE; gbc.weightx = 0;
        formPanel.add(new JLabel("Password:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.weightx = 1.0;
        formPanel.add(registerPasswordField, gbc);
        
        // Botón de registro
        JButton registerButton = new JButton("Registrar Usuario");
        registerButton.addActionListener(this::testRegisterEndpoint);
        gbc.gridx = 0; gbc.gridy = 3; gbc.gridwidth = 2; gbc.fill = GridBagConstraints.NONE; gbc.weightx = 0;
        formPanel.add(registerButton, gbc);
        
        panel.add(formPanel, BorderLayout.NORTH);
        
        // Área de respuesta
        JPanel responsePanel = new JPanel(new BorderLayout());
        responsePanel.setBorder(BorderFactory.createTitledBorder("Respuesta"));
        responsePanel.add(new JScrollPane(registerResponseArea), BorderLayout.CENTER);
        panel.add(responsePanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createLoginPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Formulario de login
        JPanel formPanel = new JPanel();
        formPanel.setBorder(BorderFactory.createTitledBorder("Iniciar Sesión"));
        formPanel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.anchor = GridBagConstraints.WEST;
        
        // Username
        gbc.gridx = 0; gbc.gridy = 0;
        formPanel.add(new JLabel("Username:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.weightx = 1.0;
        formPanel.add(loginUsernameField, gbc);
        
        // Password
        gbc.gridx = 0; gbc.gridy = 1; gbc.fill = GridBagConstraints.NONE; gbc.weightx = 0;
        formPanel.add(new JLabel("Password:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL; gbc.weightx = 1.0;
        formPanel.add(loginPasswordField, gbc);
        
        // Botón de login
        JButton loginButton = new JButton("Iniciar Sesión");
        loginButton.addActionListener(this::testLoginEndpoint);
        gbc.gridx = 0; gbc.gridy = 2; gbc.gridwidth = 2; gbc.fill = GridBagConstraints.NONE; gbc.weightx = 0;
        formPanel.add(loginButton, gbc);
        
        panel.add(formPanel, BorderLayout.NORTH);
        
        // Estado de autenticación
        JPanel authStatusPanel = new JPanel(new BorderLayout());
        authStatusPanel.setBorder(BorderFactory.createTitledBorder("Estado de Autenticación"));
        authStatusPanel.add(new JScrollPane(authStatusArea), BorderLayout.CENTER);
        panel.add(authStatusPanel, BorderLayout.CENTER);
        
        // Área de respuesta
        JPanel responsePanel = new JPanel(new BorderLayout());
        responsePanel.setBorder(BorderFactory.createTitledBorder("Respuesta"));
        responsePanel.add(new JScrollPane(loginResponseArea), BorderLayout.CENTER);
        panel.add(responsePanel, BorderLayout.SOUTH);
        
        return panel;
    }
    
    private JPanel createRefreshPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Información
        JPanel infoPanel = new JPanel();
        infoPanel.setBorder(BorderFactory.createTitledBorder("Información"));
        infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));
        
        JLabel info1 = new JLabel("Este endpoint renueva el access token usando el refresh token");
        JLabel info2 = new JLabel("Requiere estar autenticado con refresh token");
        
        infoPanel.add(info1);
        infoPanel.add(info2);
        
        panel.add(infoPanel, BorderLayout.NORTH);
        
        // Botón de prueba
        JPanel testPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton refreshButton = new JButton("Renovar Access Token");
        refreshButton.addActionListener(this::testRefreshEndpoint);
        testPanel.add(refreshButton);
        
        panel.add(testPanel, BorderLayout.CENTER);
        
        // Área de respuesta
        JPanel responsePanel = new JPanel(new BorderLayout());
        responsePanel.setBorder(BorderFactory.createTitledBorder("Respuesta"));
        responsePanel.add(new JScrollPane(refreshResponseArea), BorderLayout.CENTER);
        panel.add(responsePanel, BorderLayout.SOUTH);
        
        return panel;
    }
    
    private JPanel createLogoutPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Información
        JPanel infoPanel = new JPanel();
        infoPanel.setBorder(BorderFactory.createTitledBorder("Opciones de Logout"));
        infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));
        
        JLabel info1 = new JLabel("Logout: Revoca el token actual");
        JLabel info2 = new JLabel("Logout All: Revoca todos los tokens de la sesión");
        
        infoPanel.add(info1);
        infoPanel.add(info2);
        
        panel.add(infoPanel, BorderLayout.NORTH);
        
        // Botones
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton logoutButton = new JButton("Logout (Token Actual)");
        logoutButton.addActionListener(this::testLogoutEndpoint);
        JButton logoutAllButton = new JButton("Logout All (Sesión)");
        logoutAllButton.addActionListener(this::testLogoutAllEndpoint);
        
        buttonPanel.add(logoutButton);
        buttonPanel.add(logoutAllButton);
        
        panel.add(buttonPanel, BorderLayout.CENTER);
        
        // Área de respuesta
        JPanel responsePanel = new JPanel(new BorderLayout());
        responsePanel.setBorder(BorderFactory.createTitledBorder("Respuesta"));
        responsePanel.add(new JScrollPane(logoutResponseArea), BorderLayout.CENTER);
        panel.add(responsePanel, BorderLayout.SOUTH);
        
        return panel;
    }
    
    private void testRegisterEndpoint(ActionEvent e) {
        String username = registerUsernameField.getText().trim();
        String email = registerEmailField.getText().trim();
        String password = new String(registerPasswordField.getPassword());
        
        if (username.isEmpty() || email.isEmpty() || password.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Todos los campos son requeridos", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        new Thread(() -> {
            try {
                String response = microserviceClient.testRegisterEndpoint(username, email, password);
                SwingUtilities.invokeLater(() -> {
                    registerResponseArea.setText(response);
                    registerResponseArea.setCaretPosition(0);
                });
            } catch (Exception ex) {
                String errorMessage = "Error: " + ex.getMessage();
                SwingUtilities.invokeLater(() -> {
                    registerResponseArea.setText(errorMessage);
                    registerResponseArea.setCaretPosition(0);
                });
            }
        }).start();
    }
    
    private void testLoginEndpoint(ActionEvent e) {
        String username = loginUsernameField.getText().trim();
        String password = new String(loginPasswordField.getPassword());
        
        if (username.isEmpty() || password.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Username y password son requeridos", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        new Thread(() -> {
            try {
                String response = microserviceClient.testLoginEndpoint(username, password);
                SwingUtilities.invokeLater(() -> {
                    loginResponseArea.setText(response);
                    loginResponseArea.setCaretPosition(0);
                    
                    // Actualizar estado de autenticación
                    updateAuthStatus();
                });
            } catch (Exception ex) {
                String errorMessage = "Error: " + ex.getMessage();
                SwingUtilities.invokeLater(() -> {
                    loginResponseArea.setText(errorMessage);
                    loginResponseArea.setCaretPosition(0);
                });
            }
        }).start();
    }
    
    private void testRefreshEndpoint(ActionEvent e) {
        if (!microserviceClient.isAuthenticated()) {
            JOptionPane.showMessageDialog(this, "No hay refresh token disponible. Haga login primero.", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        new Thread(() -> {
            try {
                String response = microserviceClient.testRefreshEndpoint();
                SwingUtilities.invokeLater(() -> {
                    refreshResponseArea.setText(response);
                    refreshResponseArea.setCaretPosition(0);
                });
            } catch (Exception ex) {
                String errorMessage = "Error: " + ex.getMessage();
                SwingUtilities.invokeLater(() -> {
                    refreshResponseArea.setText(errorMessage);
                    refreshResponseArea.setCaretPosition(0);
                });
            }
        }).start();
    }
    
    private void testLogoutEndpoint(ActionEvent e) {
        if (!microserviceClient.isAuthenticated()) {
            JOptionPane.showMessageDialog(this, "No hay access token disponible. Haga login primero.", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        new Thread(() -> {
            try {
                String response = microserviceClient.testLogoutEndpoint();
                SwingUtilities.invokeLater(() -> {
                    logoutResponseArea.setText(response);
                    logoutResponseArea.setCaretPosition(0);
                    updateAuthStatus();
                });
            } catch (Exception ex) {
                String errorMessage = "Error: " + ex.getMessage();
                SwingUtilities.invokeLater(() -> {
                    logoutResponseArea.setText(errorMessage);
                    logoutResponseArea.setCaretPosition(0);
                });
            }
        }).start();
    }
    
    private void testLogoutAllEndpoint(ActionEvent e) {
        if (!microserviceClient.isAuthenticated()) {
            JOptionPane.showMessageDialog(this, "No hay access token disponible. Haga login primero.", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        new Thread(() -> {
            try {
                String response = microserviceClient.testLogoutAllEndpoint();
                SwingUtilities.invokeLater(() -> {
                    logoutResponseArea.setText(response);
                    logoutResponseArea.setCaretPosition(0);
                    updateAuthStatus();
                });
            } catch (Exception ex) {
                String errorMessage = "Error: " + ex.getMessage();
                SwingUtilities.invokeLater(() -> {
                    logoutResponseArea.setText(errorMessage);
                    logoutResponseArea.setCaretPosition(0);
                });
            }
        }).start();
    }
    
    private void updateAuthStatus() {
        if (microserviceClient.isAuthenticated()) {
            String status = "Autenticado: " + loginUsernameField.getText() + "\n";
            status += "Session ID: " + microserviceClient.getSessionId() + "\n";
            status += "Access Token: " + microserviceClient.getAccessToken().substring(0, Math.min(50, microserviceClient.getAccessToken().length())) + "...\n";
            status += "Refresh Token: " + microserviceClient.getRefreshToken().substring(0, Math.min(50, microserviceClient.getRefreshToken().length())) + "...";
            authStatusArea.setText(status);
        } else {
            authStatusArea.setText("No autenticado\nUse la pestaña Login para iniciar sesión");
        }
    }
}
