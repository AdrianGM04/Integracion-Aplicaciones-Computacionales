package com.microservice.gui.components;

import javax.swing.*;
import javax.swing.text.DefaultCaret;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Panel de logs de actividad
 * Equivalente Java del área de logs de Tkinter
 */
public class LogPanel extends JPanel {
    
    private JTextArea logTextArea;
    private JScrollPane scrollPane;
    private JButton clearButton;
    private JButton exportButton;
    private JButton saveButton;
    
    public LogPanel() {
        initializeComponents();
        setupLayout();
    }
    
    private void initializeComponents() {
        // Área de texto para logs
        logTextArea = new JTextArea(25, 100);
        logTextArea.setEditable(false);
        logTextArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        logTextArea.setBackground(Color.BLACK);
        logTextArea.setForeground(Color.GREEN);
        
        // Configurar auto-scroll
        DefaultCaret caret = (DefaultCaret) logTextArea.getCaret();
        caret.setUpdatePolicy(DefaultCaret.ALWAYS_UPDATE);
        
        // Scroll pane
        scrollPane = new JScrollPane(logTextArea);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
        scrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);
        
        // Botones
        clearButton = new JButton("Limpiar Logs");
        clearButton.addActionListener(this::clearLogs);
        
        exportButton = new JButton("Exportar Logs");
        exportButton.addActionListener(this::exportLogs);
        
        saveButton = new JButton("Guardar Logs");
        saveButton.addActionListener(this::saveLogs);
    }
    
    private void setupLayout() {
        setLayout(new BorderLayout());
        
        // Panel de botones
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        buttonPanel.add(clearButton);
        buttonPanel.add(exportButton);
        buttonPanel.add(saveButton);
        
        // Agregar componentes
        add(scrollPane, BorderLayout.CENTER);
        add(buttonPanel, BorderLayout.SOUTH);
        
        // Log inicial
        logMessage("Sistema iniciado - Java", "INFO");
    }
    
    public void logMessage(String message, String level) {
        SwingUtilities.invokeLater(() -> {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
            String logEntry = String.format("[%s] [%s] %s%n", timestamp, level, message);
            
            logTextArea.append(logEntry);
            
            // También imprimir en consola
            System.out.print(logEntry);
        });
    }
    
    private void clearLogs(ActionEvent e) {
        logTextArea.setText("");
        logMessage("Logs limpiados", "INFO");
    }
    
    private void exportLogs(ActionEvent e) {
        JFileChooser fileChooser = new JFileChooser();
        fileChooser.setDialogTitle("Exportar Logs");
        fileChooser.setSelectedFile(new java.io.File("microservice_logs.txt"));
        
        int result = fileChooser.showSaveDialog(this);
        if (result == JFileChooser.APPROVE_OPTION) {
            try (FileWriter writer = new FileWriter(fileChooser.getSelectedFile())) {
                writer.write(logTextArea.getText());
                logMessage("Logs exportados a: " + fileChooser.getSelectedFile().getAbsolutePath(), "INFO");
                JOptionPane.showMessageDialog(this, 
                    "Logs exportados exitosamente", 
                    "Éxito", 
                    JOptionPane.INFORMATION_MESSAGE);
            } catch (IOException ex) {
                logMessage("Error al exportar logs: " + ex.getMessage(), "ERROR");
                JOptionPane.showMessageDialog(this, 
                    "Error al exportar logs: " + ex.getMessage(), 
                    "Error", 
                    JOptionPane.ERROR_MESSAGE);
            }
        }
    }
    
    private void saveLogs(ActionEvent e) {
        exportLogs(e); // Alias para exportar
    }
}
