package com.microservice.gui.components;

import com.microservice.gui.services.ServiceMonitor;

import javax.swing.*;
import java.awt.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Indicador visual del estado del microservicio (semáforo)
 * Equivalente Java del semáforo de Tkinter
 */
public class StatusIndicator extends JPanel {
    
    private final ServiceMonitor serviceMonitor;
    private JLabel statusLabel;
    private JLabel lastCheckLabel;
    private JButton checkButton;
    private StatusCircle statusCircle;
    
    public StatusIndicator(ServiceMonitor serviceMonitor) {
        this.serviceMonitor = serviceMonitor;
        initializeComponents();
        setupLayout();
        updateStatus("unknown");
    }
    
    private void initializeComponents() {
        // Círculo de estado
        statusCircle = new StatusCircle();
        
        // Etiquetas de texto
        statusLabel = new JLabel("Verificando...");
        statusLabel.setFont(new Font("Arial", Font.BOLD, 12));
        
        lastCheckLabel = new JLabel("");
        lastCheckLabel.setFont(new Font("Arial", Font.PLAIN, 10));
        lastCheckLabel.setForeground(Color.GRAY);
        
        // Botón de verificación manual
        checkButton = new JButton("Verificar Ahora");
        checkButton.addActionListener(e -> {
            new Thread(() -> {
                serviceMonitor.checkServiceStatus();
                SwingUtilities.invokeLater(() -> {
                    lastCheckLabel.setText("Última verificación: " + 
                        LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")));
                });
            }).start();
        });
    }
    
    private void setupLayout() {
        setLayout(new FlowLayout(FlowLayout.LEFT, 10, 5));
        setBorder(BorderFactory.createTitledBorder("Estado del Microservicio"));
        
        add(statusCircle);
        add(statusLabel);
        add(Box.createHorizontalStrut(20));
        add(lastCheckLabel);
        add(Box.createHorizontalStrut(20));
        add(checkButton);
    }
    
    public void updateStatus(String status) {
        SwingUtilities.invokeLater(() -> {
            statusCircle.setStatus(status);
            statusLabel.setText(getStatusText(status));
            lastCheckLabel.setText("Última verificación: " + 
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")));
            repaint();
        });
    }
    
    private String getStatusText(String status) {
        switch (status) {
            case "healthy":
                return "Servicio Funcionando";
            case "degraded":
                return "Servicio Degradado";
            case "down":
                return "Servicio No Disponible";
            default:
                return "Estado Desconocido";
        }
    }
    
    /**
     * Componente personalizado para dibujar el círculo de estado
     */
    private static class StatusCircle extends JComponent {
        private String status = "unknown";
        private static final int SIZE = 30;
        
        public void setStatus(String status) {
            this.status = status;
            repaint();
        }
        
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g.create();
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            
            // Determinar color basado en el estado
            Color color = getStatusColor(status);
            
            // Dibujar círculo
            g2d.setColor(color);
            g2d.fillOval(5, 5, SIZE, SIZE);
            
            // Dibujar borde
            g2d.setColor(Color.BLACK);
            g2d.setStroke(new BasicStroke(2));
            g2d.drawOval(5, 5, SIZE, SIZE);
            
            g2d.dispose();
        }
        
        private Color getStatusColor(String status) {
            switch (status) {
                case "healthy":
                    return new Color(0, 255, 0);    // Verde
                case "degraded":
                    return new Color(255, 136, 0);   // Naranja
                case "down":
                    return new Color(255, 0, 0);     // Rojo
                default:
                    return new Color(136, 136, 136); // Gris
            }
        }
        
        @Override
        public Dimension getPreferredSize() {
            return new Dimension(SIZE + 10, SIZE + 10);
        }
    }
}
