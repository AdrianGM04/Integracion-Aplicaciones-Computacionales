import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import json
import threading
import time
from datetime import datetime
import os
import configparser
from typing import Dict, Any, Optional

class MicroserviceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Microservicio GUI - Consumidor de Endpoints")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variables de configuración
        self.config = configparser.ConfigParser()
        self.config_file = 'microservice_config.ini'
        self.load_config()
        
        # Variables de estado
        self.access_token = None
        self.refresh_token = None
        self.session_id = None
        self.service_status = "unknown"  # unknown, healthy, degraded, down
        
        # Configurar el estilo
        self.setup_styles()
        
        # Crear la interfaz
        self.create_widgets()
        
        # Iniciar monitoreo del servicio
        self.start_service_monitoring()
        
    def setup_styles(self):
        """Configurar estilos para la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores personalizados
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        style.configure('Subtitle.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        style.configure('Status.TLabel', font=('Arial', 10, 'bold'))
        
    def load_config(self):
        """Cargar configuración desde archivo"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            # Configuración por defecto
            self.config['SERVICE'] = {
                'ip': '127.0.0.1',
                'port': '5000',
                'base_url': 'http://127.0.0.1:5000'
            }
            self.config['ENDPOINTS'] = {
                'health': '/health',
                'register': '/register',
                'login': '/login',
                'protected': '/protected',
                'refresh': '/refresh',
                'logout': '/logout',
                'logout_all': '/logout_all'
            }
            self.save_config()
    
    def save_config(self):
        """Guardar configuración en archivo"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Microservicio GUI - Consumidor de Endpoints", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Semáforo de estado (siempre visible)
        self.create_status_indicator(main_frame, row=1)
        
        # Notebook para las diferentes secciones
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(2, weight=1)
        
        # Crear las pestañas
        self.create_config_tab()
        self.create_logs_tab()
        self.create_health_tab()
        self.create_auth_tab()
        self.create_protected_tab()
        
    def create_status_indicator(self, parent, row):
        """Crear el semáforo de estado del servicio"""
        status_frame = ttk.LabelFrame(parent, text="Estado del Microservicio", padding="10")
        status_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Indicador visual
        self.status_canvas = tk.Canvas(status_frame, width=30, height=30, bg='#f0f0f0', highlightthickness=0)
        self.status_canvas.grid(row=0, column=0, padx=(0, 10))
        
        # Texto de estado
        self.status_label = ttk.Label(status_frame, text="Verificando...", style='Status.TLabel')
        self.status_label.grid(row=0, column=1)
        
        # Última verificación
        self.last_check_label = ttk.Label(status_frame, text="", style='Status.TLabel')
        self.last_check_label.grid(row=0, column=2, padx=(20, 0))
        
        # Botón de verificación manual
        check_btn = ttk.Button(status_frame, text="Verificar Ahora", command=self.check_service_status)
        check_btn.grid(row=0, column=3, padx=(20, 0))
        
        # Dibujar el semáforo inicial
        self.update_status_indicator()
    
    def update_status_indicator(self):
        """Actualizar el indicador visual del semáforo"""
        self.status_canvas.delete("all")
        
        # Colores del semáforo
        colors = {
            "healthy": "#00ff00",    # Verde
            "degraded": "#ff8800",   # Naranja
            "down": "#ff0000",       # Rojo
            "unknown": "#888888"     # Gris
        }
        
        color = colors.get(self.service_status, "#888888")
        
        # Dibujar círculo
        self.status_canvas.create_oval(5, 5, 25, 25, fill=color, outline="black", width=2)
        
        # Actualizar texto
        status_texts = {
            "healthy": "Servicio Funcionando",
            "degraded": "Servicio Degradado",
            "down": "Servicio No Disponible",
            "unknown": "Estado Desconocido"
        }
        
        self.status_label.config(text=status_texts.get(self.service_status, "Estado Desconocido"))
        self.last_check_label.config(text=f"Última verificación: {datetime.now().strftime('%H:%M:%S')}")
    
    def create_config_tab(self):
        """Crear pestaña de configuración"""
        config_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(config_frame, text="Configuración")
        
        # Configuración del servicio
        service_frame = ttk.LabelFrame(config_frame, text="Configuración del Servicio", padding="10")
        service_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        service_frame.columnconfigure(1, weight=1)
        
        # IP
        ttk.Label(service_frame, text="IP del Servicio:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ip_var = tk.StringVar(value=self.config.get('SERVICE', 'ip', fallback='127.0.0.1'))
        ip_entry = ttk.Entry(service_frame, textvariable=self.ip_var, width=20)
        ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Puerto
        ttk.Label(service_frame, text="Puerto:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.port_var = tk.StringVar(value=self.config.get('SERVICE', 'port', fallback='5000'))
        port_entry = ttk.Entry(service_frame, textvariable=self.port_var, width=20)
        port_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # URL Base
        ttk.Label(service_frame, text="URL Base:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.base_url_var = tk.StringVar(value=self.config.get('SERVICE', 'base_url', fallback='http://127.0.0.1:5000'))
        base_url_entry = ttk.Entry(service_frame, textvariable=self.base_url_var, width=40)
        base_url_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Botones de configuración
        button_frame = ttk.Frame(service_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Actualizar URL", command=self.update_base_url).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Guardar Configuración", command=self.save_service_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cargar Configuración", command=self.load_service_config).pack(side=tk.LEFT)
        
        # Configuración de endpoints
        endpoints_frame = ttk.LabelFrame(config_frame, text="Configuración de Endpoints", padding="10")
        endpoints_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        config_frame.rowconfigure(1, weight=1)
        endpoints_frame.columnconfigure(1, weight=1)
        
        # Treeview para endpoints
        columns = ('Endpoint', 'Ruta', 'Método')
        self.endpoints_tree = ttk.Treeview(endpoints_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.endpoints_tree.heading(col, text=col)
            self.endpoints_tree.column(col, width=150)
        
        # Scrollbar para el treeview
        scrollbar = ttk.Scrollbar(endpoints_frame, orient=tk.VERTICAL, command=self.endpoints_tree.yview)
        self.endpoints_tree.configure(yscrollcommand=scrollbar.set)
        
        self.endpoints_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Cargar endpoints
        self.load_endpoints_to_tree()
        
        # Botones para endpoints
        endpoints_btn_frame = ttk.Frame(endpoints_frame)
        endpoints_btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(endpoints_btn_frame, text="Guardar Endpoints", command=self.save_endpoints_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(endpoints_btn_frame, text="Restaurar Defaults", command=self.restore_default_endpoints).pack(side=tk.LEFT)
    
    def create_logs_tab(self):
        """Crear pestaña de logs"""
        logs_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(logs_frame, text="Logs de Actividad")
        
        # Área de logs
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=25, width=100, wrap=tk.WORD)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        # Botones de logs
        logs_btn_frame = ttk.Frame(logs_frame)
        logs_btn_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(logs_btn_frame, text="Limpiar Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(logs_btn_frame, text="Exportar Logs", command=self.export_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(logs_btn_frame, text="Guardar Logs", command=self.save_logs).pack(side=tk.LEFT)
        
        # Log inicial
        self.log_message("Sistema iniciado", "INFO")
    
    def create_health_tab(self):
        """Crear pestaña para endpoint /health"""
        health_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(health_frame, text="Health Check")
        
        # Información del endpoint
        info_frame = ttk.LabelFrame(health_frame, text="Información del Endpoint", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(info_frame, text="Endpoint: /health").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Método: GET").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Descripción: Verifica el estado del microservicio y la base de datos").grid(row=2, column=0, sticky=tk.W)
        
        # Botón de prueba
        test_frame = ttk.Frame(health_frame)
        test_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(test_frame, text="Verificar Estado del Servicio", 
                  command=self.test_health_endpoint).grid(row=0, column=0)
        
        # Área de respuesta
        response_frame = ttk.LabelFrame(health_frame, text="Respuesta", padding="10")
        response_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        health_frame.rowconfigure(2, weight=1)
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        
        self.health_response_text = scrolledtext.ScrolledText(response_frame, height=10, wrap=tk.WORD)
        self.health_response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_auth_tab(self):
        """Crear pestaña para endpoints de autenticación"""
        auth_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(auth_frame, text="Autenticación")
        
        # Notebook para sub-pestañas de auth
        auth_notebook = ttk.Notebook(auth_frame)
        auth_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        auth_frame.rowconfigure(0, weight=1)
        auth_frame.columnconfigure(0, weight=1)
        
        # Pestaña de registro
        self.create_register_tab(auth_notebook)
        
        # Pestaña de login
        self.create_login_tab(auth_notebook)
        
        # Pestaña de refresh
        self.create_refresh_tab(auth_notebook)
        
        # Pestaña de logout
        self.create_logout_tab(auth_notebook)
    
    def create_register_tab(self, parent):
        """Crear pestaña de registro"""
        register_frame = ttk.Frame(parent, padding="10")
        parent.add(register_frame, text="Registro")
        
        # Formulario de registro
        form_frame = ttk.LabelFrame(register_frame, text="Registrar Nuevo Usuario", padding="10")
        form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        form_frame.columnconfigure(1, weight=1)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.register_username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.register_username_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.register_email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.register_email_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.register_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.register_password_var, show="*", width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Botón de registro
        ttk.Button(form_frame, text="Registrar Usuario", command=self.test_register_endpoint).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Área de respuesta
        response_frame = ttk.LabelFrame(register_frame, text="Respuesta", padding="10")
        response_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        register_frame.rowconfigure(1, weight=1)
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        
        self.register_response_text = scrolledtext.ScrolledText(response_frame, height=8, wrap=tk.WORD)
        self.register_response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_login_tab(self, parent):
        """Crear pestaña de login"""
        login_frame = ttk.Frame(parent, padding="10")
        parent.add(login_frame, text="Login")
        
        # Formulario de login
        form_frame = ttk.LabelFrame(login_frame, text="Iniciar Sesión", padding="10")
        form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        form_frame.columnconfigure(1, weight=1)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.login_username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.login_username_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.login_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.login_password_var, show="*", width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Botón de login
        ttk.Button(form_frame, text="Iniciar Sesión", command=self.test_login_endpoint).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Estado de autenticación
        auth_status_frame = ttk.LabelFrame(login_frame, text="Estado de Autenticación", padding="10")
        auth_status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.auth_status_text = tk.Text(auth_status_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.auth_status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        auth_status_frame.columnconfigure(0, weight=1)
        
        # Área de respuesta
        response_frame = ttk.LabelFrame(login_frame, text="Respuesta", padding="10")
        response_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        login_frame.rowconfigure(2, weight=1)
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        
        self.login_response_text = scrolledtext.ScrolledText(response_frame, height=6, wrap=tk.WORD)
        self.login_response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_refresh_tab(self, parent):
        """Crear pestaña de refresh token"""
        refresh_frame = ttk.Frame(parent, padding="10")
        parent.add(refresh_frame, text="Refresh Token")
        
        # Información
        info_frame = ttk.LabelFrame(refresh_frame, text="Información", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(info_frame, text="Este endpoint renueva el access token usando el refresh token").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Requiere estar autenticado con refresh token").grid(row=1, column=0, sticky=tk.W)
        
        # Botón de prueba
        test_btn = ttk.Button(refresh_frame, text="Renovar Access Token", 
                  command=self.test_refresh_endpoint)
        test_btn.grid(row=1, column=0, pady=10)
        
        # Área de respuesta
        response_frame = ttk.LabelFrame(refresh_frame, text="Respuesta", padding="10")
        response_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        refresh_frame.rowconfigure(2, weight=1)
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        
        self.refresh_response_text = scrolledtext.ScrolledText(response_frame, height=8, wrap=tk.WORD)
        self.refresh_response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_logout_tab(self, parent):
        """Crear pestaña de logout"""
        logout_frame = ttk.Frame(parent, padding="10")
        parent.add(logout_frame, text="Logout")
        
        # Información
        info_frame = ttk.LabelFrame(logout_frame, text="Opciones de Logout", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(info_frame, text="Logout: Revoca el token actual").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Logout All: Revoca todos los tokens de la sesión").grid(row=1, column=0, sticky=tk.W)
        
        # Botones
        button_frame = ttk.Frame(logout_frame)
        button_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(button_frame, text="Logout (Token Actual)", 
                  command=self.test_logout_endpoint).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Logout All (Sesión)", 
                  command=self.test_logout_all_endpoint).pack(side=tk.LEFT)
        
        # Área de respuesta
        response_frame = ttk.LabelFrame(logout_frame, text="Respuesta", padding="10")
        response_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        logout_frame.rowconfigure(2, weight=1)
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        
        self.logout_response_text = scrolledtext.ScrolledText(response_frame, height=8, wrap=tk.WORD)
        self.logout_response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_protected_tab(self):
        """Crear pestaña para endpoint protegido"""
        protected_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(protected_frame, text="Endpoint Protegido")
        
        # Información
        info_frame = ttk.LabelFrame(protected_frame, text="Información del Endpoint", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(info_frame, text="Endpoint: /protected").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Método: GET").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Descripción: Endpoint que requiere autenticación JWT").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Requiere: Access Token válido").grid(row=3, column=0, sticky=tk.W)
        
        # Botón de prueba
        ttk.Button(protected_frame, text="Acceder a Endpoint Protegido", 
                  command=self.test_protected_endpoint).grid(row=1, column=0, pady=10)
        
        # Área de respuesta
        response_frame = ttk.LabelFrame(protected_frame, text="Respuesta", padding="10")
        response_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        protected_frame.rowconfigure(2, weight=1)
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        
        self.protected_response_text = scrolledtext.ScrolledText(response_frame, height=10, wrap=tk.WORD)
        self.protected_response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # Métodos de configuración
    def update_base_url(self):
        """Actualizar la URL base basada en IP y puerto"""
        ip = self.ip_var.get().strip()
        port = self.port_var.get().strip()
        
        if ip and port:
            base_url = f"http://{ip}:{port}"
            self.base_url_var.set(base_url)
            self.log_message(f"URL base actualizada: {base_url}", "INFO")
        else:
            messagebox.showerror("Error", "IP y Puerto son requeridos")
    
    def save_service_config(self):
        """Guardar configuración del servicio"""
        self.config.set('SERVICE', 'ip', self.ip_var.get())
        self.config.set('SERVICE', 'port', self.port_var.get())
        self.config.set('SERVICE', 'base_url', self.base_url_var.get())
        self.save_config()
        self.log_message("Configuración del servicio guardada", "INFO")
        messagebox.showinfo("Éxito", "Configuración guardada correctamente")
    
    def load_service_config(self):
        """Cargar configuración del servicio"""
        self.load_config()
        self.ip_var.set(self.config.get('SERVICE', 'ip', fallback='127.0.0.1'))
        self.port_var.set(self.config.get('SERVICE', 'port', fallback='5000'))
        self.base_url_var.set(self.config.get('SERVICE', 'base_url', fallback='http://127.0.0.1:5000'))
        self.log_message("Configuración del servicio cargada", "INFO")
    
    def load_endpoints_to_tree(self):
        """Cargar endpoints al treeview"""
        # Limpiar treeview
        for item in self.endpoints_tree.get_children():
            self.endpoints_tree.delete(item)
        
        # Endpoints por defecto
        endpoints = [
            ('health', '/health', 'GET'),
            ('register', '/register', 'POST'),
            ('login', '/login', 'POST'),
            ('protected', '/protected', 'GET'),
            ('refresh', '/refresh', 'POST'),
            ('logout', '/logout', 'POST'),
            ('logout_all', '/logout_all', 'POST')
        ]
        
        for endpoint_name, path, method in endpoints:
            self.endpoints_tree.insert('', 'end', values=(endpoint_name, path, method))
    
    def save_endpoints_config(self):
        """Guardar configuración de endpoints"""
        # Por simplicidad, guardamos los endpoints por defecto
        default_endpoints = {
            'health': '/health',
            'register': '/register',
            'login': '/login',
            'protected': '/protected',
            'refresh': '/refresh',
            'logout': '/logout',
            'logout_all': '/logout_all'
        }
        
        for name, path in default_endpoints.items():
            self.config.set('ENDPOINTS', name, path)
        
        self.save_config()
        self.log_message("Configuración de endpoints guardada", "INFO")
        messagebox.showinfo("Éxito", "Endpoints guardados correctamente")
    
    def restore_default_endpoints(self):
        """Restaurar endpoints por defecto"""
        self.load_endpoints_to_tree()
        self.log_message("Endpoints restaurados a valores por defecto", "INFO")
    
    # Métodos de logs
    def log_message(self, message, level="INFO"):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.logs_text.insert(tk.END, log_entry)
        self.logs_text.see(tk.END)
        
        # También imprimir en consola
        print(log_entry.strip())
    
    def clear_logs(self):
        """Limpiar logs"""
        self.logs_text.delete(1.0, tk.END)
        self.log_message("Logs limpiados", "INFO")
    
    def export_logs(self):
        """Exportar logs a archivo"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.logs_text.get(1.0, tk.END))
                self.log_message(f"Logs exportados a: {filename}", "INFO")
                messagebox.showinfo("Éxito", f"Logs exportados a: {filename}")
            except Exception as e:
                self.log_message(f"Error al exportar logs: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Error al exportar logs: {str(e)}")
    
    def save_logs(self):
        """Guardar logs (alias para exportar)"""
        self.export_logs()
    
    # Métodos de monitoreo del servicio
    def start_service_monitoring(self):
        """Iniciar monitoreo automático del servicio"""
        def monitor():
            while True:
                try:
                    self.check_service_status()
                    time.sleep(30)  # Verificar cada 30 segundos
                except Exception as e:
                    self.log_message(f"Error en monitoreo: {str(e)}", "ERROR")
                    time.sleep(30)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def check_service_status(self):
        """Verificar estado del servicio"""
        def check():
            try:
                base_url = self.base_url_var.get()
                health_url = f"{base_url}/health"
                
                self.log_message(f"Verificando estado del servicio: {health_url}", "INFO")
                
                response = requests.get(health_url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok':
                        self.service_status = "healthy"
                        self.log_message("Servicio funcionando correctamente", "INFO")
                    else:
                        self.service_status = "degraded"
                        self.log_message(f"Servicio degradado: {data.get('error', 'Error desconocido')}", "WARNING")
                else:
                    self.service_status = "down"
                    self.log_message(f"Servicio no disponible. Código: {response.status_code}", "ERROR")
                
            except requests.exceptions.ConnectionError:
                self.service_status = "down"
                self.log_message("No se puede conectar al servicio", "ERROR")
            except requests.exceptions.Timeout:
                self.service_status = "down"
                self.log_message("Timeout al conectar al servicio", "ERROR")
            except Exception as e:
                self.service_status = "unknown"
                self.log_message(f"Error al verificar servicio: {str(e)}", "ERROR")
            
            # Actualizar UI en el hilo principal
            self.root.after(0, self.update_status_indicator)
        
        # Ejecutar en hilo separado
        threading.Thread(target=check, daemon=True).start()
    
    # Métodos de prueba de endpoints
    def test_health_endpoint(self):
        """Probar endpoint /health"""
        def test():
            try:
                base_url = self.base_url_var.get()
                url = f"{base_url}/health"
                
                self.log_message(f"Probando endpoint /health: {url}", "INFO")
                
                response = requests.get(url, timeout=10)
                
                # Mostrar respuesta
                response_text = f"Status Code: {response.status_code}\n"
                response_text += f"Headers: {dict(response.headers)}\n\n"
                
                # Manejar respuesta JSON o texto
                try:
                    if response.text.strip():
                        response_data = response.json()
                        response_text += f"Response Body:\n{json.dumps(response_data, indent=2)}"
                    else:
                        response_text += "Response Body: (vacío)"
                except json.JSONDecodeError:
                    response_text += f"Response Body (texto):\n{response.text}"
                
                self.health_response_text.delete(1.0, tk.END)
                self.health_response_text.insert(1.0, response_text)
                
                self.log_message(f"Respuesta de /health: {response.status_code}", "INFO")
                
            except Exception as e:
                error_text = f"Error: {str(e)}"
                self.health_response_text.delete(1.0, tk.END)
                self.health_response_text.insert(1.0, error_text)
                self.log_message(f"Error en /health: {str(e)}", "ERROR")
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_register_endpoint(self):
        """Probar endpoint /register"""
        def test():
            try:
                base_url = self.base_url_var.get()
                url = f"{base_url}/register"
                
                username = self.register_username_var.get().strip()
                email = self.register_email_var.get().strip()
                password = self.register_password_var.get().strip()
                
                if not username or not email or not password:
                    messagebox.showerror("Error", "Todos los campos son requeridos")
                    return
                
                data = {
                    "username": username,
                    "email": email,
                    "password": password
                }
                
                self.log_message(f"Probando endpoint /register: {url}", "INFO")
                self.log_message(f"Datos enviados: {json.dumps(data, indent=2)}", "INFO")
                
                response = requests.post(url, json=data, timeout=10)
                
                # Mostrar respuesta
                response_text = f"Status Code: {response.status_code}\n"
                response_text += f"Headers: {dict(response.headers)}\n\n"
                
                # Manejar respuesta JSON o texto
                try:
                    if response.text.strip():
                        response_data = response.json()
                        response_text += f"Response Body:\n{json.dumps(response_data, indent=2)}"
                    else:
                        response_text += "Response Body: (vacío)"
                except json.JSONDecodeError:
                    response_text += f"Response Body (texto):\n{response.text}"
                
                self.register_response_text.delete(1.0, tk.END)
                self.register_response_text.insert(1.0, response_text)
                
                self.log_message(f"Respuesta de /register: {response.status_code}", "INFO")
                
                if response.status_code == 201:
                    messagebox.showinfo("Éxito", "Usuario registrado correctamente")
                
            except Exception as e:
                error_text = f"Error: {str(e)}"
                self.register_response_text.delete(1.0, tk.END)
                self.register_response_text.insert(1.0, error_text)
                self.log_message(f"Error en /register: {str(e)}", "ERROR")
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_login_endpoint(self):
        """Probar endpoint /login"""
        def test():
            try:
                base_url = self.base_url_var.get()
                url = f"{base_url}/login"
                
                username = self.login_username_var.get().strip()
                password = self.login_password_var.get().strip()
                
                if not username or not password:
                    messagebox.showerror("Error", "Username y password son requeridos")
                    return
                
                data = {
                    "username": username,
                    "password": password
                }
                
                self.log_message(f"Probando endpoint /login: {url}", "INFO")
                self.log_message(f"Datos enviados: {json.dumps(data, indent=2)}", "INFO")
                
                response = requests.post(url, json=data, timeout=10)
                
                # Mostrar respuesta
                response_text = f"Status Code: {response.status_code}\n"
                response_text += f"Headers: {dict(response.headers)}\n\n"
                
                # Manejar respuesta JSON o texto
                try:
                    if response.text.strip():
                        response_data = response.json()
                        response_text += f"Response Body:\n{json.dumps(response_data, indent=2)}"
                    else:
                        response_text += "Response Body: (vacío)"
                        response_data = {}
                except json.JSONDecodeError:
                    response_text += f"Response Body (texto):\n{response.text}"
                    response_data = {}
                
                self.login_response_text.delete(1.0, tk.END)
                self.login_response_text.insert(1.0, response_text)
                
                self.log_message(f"Respuesta de /login: {response.status_code}", "INFO")
                
                if response.status_code == 200 and response_data:
                    self.access_token = response_data.get('access_token')
                    self.refresh_token = response_data.get('refresh_token')
                    self.session_id = response_data.get('session_id')
                    
                    # Actualizar estado de autenticación
                    auth_status = f"Autenticado: {username}\n"
                    auth_status += f"Session ID: {self.session_id}\n"
                    auth_status += f"Access Token: {self.access_token[:50]}...\n"
                    auth_status += f"Refresh Token: {self.refresh_token[:50]}..."
                    
                    self.auth_status_text.config(state=tk.NORMAL)
                    self.auth_status_text.delete(1.0, tk.END)
                    self.auth_status_text.insert(1.0, auth_status)
                    self.auth_status_text.config(state=tk.DISABLED)
                    
                    self.log_message("Login exitoso - tokens guardados", "INFO")
                    messagebox.showinfo("Éxito", "Login exitoso")
                else:
                    self.log_message("Login fallido", "WARNING")
                
            except Exception as e:
                error_text = f"Error: {str(e)}"
                self.login_response_text.delete(1.0, tk.END)
                self.login_response_text.insert(1.0, error_text)
                self.log_message(f"Error en /login: {str(e)}", "ERROR")
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_refresh_endpoint(self):
        """Probar endpoint /refresh"""
        def test():
            try:
                if not self.refresh_token:
                    messagebox.showerror("Error", "No hay refresh token disponible. Haga login primero.")
                    return
                
                base_url = self.base_url_var.get()
                url = f"{base_url}/refresh"
                
                headers = {
                    "Authorization": f"Bearer {self.refresh_token}"
                }
                
                self.log_message(f"Probando endpoint /refresh: {url}", "INFO")
                
                response = requests.post(url, headers=headers, timeout=10)
                
                # Mostrar respuesta
                response_text = f"Status Code: {response.status_code}\n"
                response_text += f"Headers: {dict(response.headers)}\n\n"
                
                # Manejar respuesta JSON o texto
                try:
                    if response.text.strip():
                        response_data = response.json()
                        response_text += f"Response Body:\n{json.dumps(response_data, indent=2)}"
                    else:
                        response_text += "Response Body: (vacío)"
                        response_data = {}
                except json.JSONDecodeError:
                    response_text += f"Response Body (texto):\n{response.text}"
                    response_data = {}
                
                self.refresh_response_text.delete(1.0, tk.END)
                self.refresh_response_text.insert(1.0, response_text)
                
                self.log_message(f"Respuesta de /refresh: {response.status_code}", "INFO")
                
                if response.status_code == 200 and response_data:
                    self.access_token = response_data.get('access_token')
                    self.log_message("Access token renovado", "INFO")
                    messagebox.showinfo("Éxito", "Access token renovado correctamente")
                else:
                    self.log_message("Error al renovar token", "WARNING")
                
            except Exception as e:
                error_text = f"Error: {str(e)}"
                self.refresh_response_text.delete(1.0, tk.END)
                self.refresh_response_text.insert(1.0, error_text)
                self.log_message(f"Error en /refresh: {str(e)}", "ERROR")
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_logout_endpoint(self):
        """Probar endpoint /logout"""
        def test():
            try:
                if not self.access_token:
                    messagebox.showerror("Error", "No hay access token disponible. Haga login primero.")
                    return
                
                base_url = self.base_url_var.get()
                url = f"{base_url}/logout"
                
                headers = {
                    "Authorization": f"Bearer {self.access_token}"
                }
                
                self.log_message(f"Probando endpoint /logout: {url}", "INFO")
                
                response = requests.post(url, headers=headers, timeout=10)
                
                # Mostrar respuesta
                response_text = f"Status Code: {response.status_code}\n"
                response_text += f"Headers: {dict(response.headers)}\n\n"
                
                # Manejar respuesta JSON o texto
                try:
                    if response.text.strip():
                        response_data = response.json()
                        response_text += f"Response Body:\n{json.dumps(response_data, indent=2)}"
                    else:
                        response_text += "Response Body: (vacío)"
                except json.JSONDecodeError:
                    response_text += f"Response Body (texto):\n{response.text}"
                
                self.logout_response_text.delete(1.0, tk.END)
                self.logout_response_text.insert(1.0, response_text)
                
                self.log_message(f"Respuesta de /logout: {response.status_code}", "INFO")
                
                if response.status_code == 200:
                    self.access_token = None
                    self.log_message("Logout exitoso - access token revocado", "INFO")
                    messagebox.showinfo("Éxito", "Logout exitoso")
                else:
                    self.log_message("Error en logout", "WARNING")
                
            except Exception as e:
                error_text = f"Error: {str(e)}"
                self.logout_response_text.delete(1.0, tk.END)
                self.logout_response_text.insert(1.0, error_text)
                self.log_message(f"Error en /logout: {str(e)}", "ERROR")
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_logout_all_endpoint(self):
        """Probar endpoint /logout_all"""
        def test():
            try:
                if not self.access_token:
                    messagebox.showerror("Error", "No hay access token disponible. Haga login primero.")
                    return
                
                base_url = self.base_url_var.get()
                url = f"{base_url}/logout_all"
                
                headers = {
                    "Authorization": f"Bearer {self.access_token}"
                }
                
                self.log_message(f"Probando endpoint /logout_all: {url}", "INFO")
                
                response = requests.post(url, headers=headers, timeout=10)
                
                # Mostrar respuesta
                response_text = f"Status Code: {response.status_code}\n"
                response_text += f"Headers: {dict(response.headers)}\n\n"
                
                # Manejar respuesta JSON o texto
                try:
                    if response.text.strip():
                        response_data = response.json()
                        response_text += f"Response Body:\n{json.dumps(response_data, indent=2)}"
                    else:
                        response_text += "Response Body: (vacío)"
                except json.JSONDecodeError:
                    response_text += f"Response Body (texto):\n{response.text}"
                
                self.logout_response_text.delete(1.0, tk.END)
                self.logout_response_text.insert(1.0, response_text)
                
                self.log_message(f"Respuesta de /logout_all: {response.status_code}", "INFO")
                
                if response.status_code == 200:
                    self.access_token = None
                    self.refresh_token = None
                    self.session_id = None
                    self.log_message("Logout all exitoso - todos los tokens revocados", "INFO")
                    messagebox.showinfo("Éxito", "Logout all exitoso")
                else:
                    self.log_message("Error en logout all", "WARNING")
                
            except Exception as e:
                error_text = f"Error: {str(e)}"
                self.logout_response_text.delete(1.0, tk.END)
                self.logout_response_text.insert(1.0, error_text)
                self.log_message(f"Error en /logout_all: {str(e)}", "ERROR")
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_protected_endpoint(self):
        """Probar endpoint /protected"""
        def test():
            try:
                if not self.access_token:
                    messagebox.showerror("Error", "No hay access token disponible. Haga login primero.")
                    return
                
                base_url = self.base_url_var.get()
                url = f"{base_url}/protected"
                
                headers = {
                    "Authorization": f"Bearer {self.access_token}"
                }
                
                self.log_message(f"Probando endpoint /protected: {url}", "INFO")
                
                response = requests.get(url, headers=headers, timeout=10)
                
                # Mostrar respuesta
                response_text = f"Status Code: {response.status_code}\n"
                response_text += f"Headers: {dict(response.headers)}\n\n"
                
                # Manejar respuesta JSON o texto
                try:
                    if response.text.strip():
                        response_data = response.json()
                        response_text += f"Response Body:\n{json.dumps(response_data, indent=2)}"
                    else:
                        response_text += "Response Body: (vacío)"
                except json.JSONDecodeError:
                    response_text += f"Response Body (texto):\n{response.text}"
                
                self.protected_response_text.delete(1.0, tk.END)
                self.protected_response_text.insert(1.0, response_text)
                
                self.log_message(f"Respuesta de /protected: {response.status_code}", "INFO")
                
                if response.status_code == 200:
                    self.log_message("Acceso a endpoint protegido exitoso", "INFO")
                else:
                    self.log_message("Error al acceder a endpoint protegido", "WARNING")
                
            except Exception as e:
                error_text = f"Error: {str(e)}"
                self.protected_response_text.delete(1.0, tk.END)
                self.protected_response_text.insert(1.0, error_text)
                self.log_message(f"Error en /protected: {str(e)}", "ERROR")
        
        threading.Thread(target=test, daemon=True).start()


def main():
    """Función principal"""
    root = tk.Tk()
    app = MicroserviceGUI(root)
    
    # Configurar cierre de aplicación
    def on_closing():
        app.log_message("Aplicación cerrada", "INFO")
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()
