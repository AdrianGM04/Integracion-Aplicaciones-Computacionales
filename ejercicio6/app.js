// Configuración de la API
const API_BASE_URL = 'http://localhost:5000';

// Estado global de la aplicación
let currentUser = null;
let accessToken = null;
let refreshToken = null;
let sessionId = null;

// Elementos del DOM
const authPanel = document.getElementById('auth-panel');
const booksPanel = document.getElementById('books-panel');
const authStatus = document.getElementById('auth-status');
const userInfo = document.getElementById('user-info');
const tokenInfo = document.getElementById('token-info');
const booksContainer = document.getElementById('books-container');
const logsContainer = document.getElementById('logs-container');
const bookForm = document.getElementById('book-form');
const bookFormElement = document.getElementById('bookForm');

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkStoredAuth();
});

function initializeApp() {
    log('info', 'Aplicación inicializada');
    log('info', `Conectando a API: ${API_BASE_URL}`);
}

function setupEventListeners() {
    // Formularios de autenticación
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    
    // Botones de autenticación
    document.getElementById('refreshTokenBtn').addEventListener('click', handleRefreshToken);
    document.getElementById('checkStatusBtn').addEventListener('click', handleCheckStatus);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('logoutAllBtn').addEventListener('click', handleLogoutAll);
    
    // Controles de libros
    document.getElementById('loadBooksBtn').addEventListener('click', loadAllBooks);
    document.getElementById('loadDigitalBtn').addEventListener('click', loadDigitalBooks);
    document.getElementById('showCreateFormBtn').addEventListener('click', showCreateForm);
    
    // Búsquedas
    document.getElementById('searchByIsbnBtn').addEventListener('click', searchByIsbn);
    document.getElementById('searchByAuthorBtn').addEventListener('click', searchByAuthor);
    
    // Formulario de libro
    bookFormElement.addEventListener('submit', handleBookSubmit);
    document.getElementById('cancelBookBtn').addEventListener('click', hideBookForm);
    document.getElementById('deleteBookBtn').addEventListener('click', handleDeleteBook);
    
    // Logs
    document.getElementById('clearLogsBtn').addEventListener('click', clearLogs);
    document.getElementById('exportLogsBtn').addEventListener('click', exportLogs);
}

// ==================== AUTENTICACIÓN ====================

async function handleRegister(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        log('info', 'Intentando registro...');
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', `Usuario registrado: ${result.msg}`);
            showAlert('success', 'Usuario registrado exitosamente');
            e.target.reset();
        } else {
            log('error', `Error en registro: ${result.msg}`);
            showAlert('error', result.msg);
        }
    } catch (error) {
        log('error', `Error de conexión en registro: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        log('info', 'Intentando login...');
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', 'Login exitoso');
            accessToken = result.access_token;
            refreshToken = result.refresh_token;
            sessionId = result.session_id;
            
            // Decodificar JWT para obtener información del usuario
            const payload = JSON.parse(atob(accessToken.split('.')[1]));
            currentUser = {
                id: payload.sub,
                name: payload.name,
                email: payload.email,
                role: payload.role
            };
            
            // Guardar en localStorage
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('refreshToken', refreshToken);
            localStorage.setItem('sessionId', sessionId);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            updateAuthUI();
            showAlert('success', 'Login exitoso');
            e.target.reset();
        } else {
            log('error', `Error en login: ${result.msg}`);
            showAlert('error', result.msg);
        }
    } catch (error) {
        log('error', `Error de conexión en login: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

async function handleRefreshToken() {
    if (!refreshToken) {
        log('error', 'No hay refresh token disponible');
        return;
    }
    
    try {
        log('info', 'Refrescando token...');
        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${refreshToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', 'Token refrescado exitosamente');
            accessToken = result.access_token;
            localStorage.setItem('accessToken', accessToken);
            updateTokenInfo();
            showAlert('success', 'Token refrescado');
        } else {
            log('error', `Error al refrescar token: ${result.msg}`);
            showAlert('error', result.msg);
            handleLogout();
        }
    } catch (error) {
        log('error', `Error de conexión al refrescar token: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

async function handleCheckStatus() {
    if (!accessToken) {
        log('error', 'No hay token de acceso');
        return;
    }
    
    try {
        log('info', 'Verificando estado de autenticación...');
        const response = await fetch(`${API_BASE_URL}/auth/status`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', 'Estado verificado exitosamente');
            updateTokenInfo(result);
            showAlert('success', 'Estado verificado');
        } else {
            log('error', `Error al verificar estado: ${result.msg}`);
            showAlert('error', result.msg);
        }
    } catch (error) {
        log('error', `Error de conexión al verificar estado: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

async function handleLogout() {
    if (!accessToken) {
        log('error', 'No hay token de acceso');
        return;
    }
    
    try {
        log('info', 'Cerrando sesión...');
        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        const result = await response.json();
        log('success', `Sesión cerrada: ${result.msg}`);
        
        clearAuth();
        showAlert('success', 'Sesión cerrada');
    } catch (error) {
        log('error', `Error al cerrar sesión: ${error.message}`);
        clearAuth();
    }
}

async function handleLogoutAll() {
    if (!accessToken) {
        log('error', 'No hay token de acceso');
        return;
    }
    
    try {
        log('info', 'Cerrando todas las sesiones...');
        const response = await fetch(`${API_BASE_URL}/auth/logout_all`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        const result = await response.json();
        log('success', `Todas las sesiones cerradas: ${result.msg}`);
        
        clearAuth();
        showAlert('success', 'Todas las sesiones cerradas');
    } catch (error) {
        log('error', `Error al cerrar todas las sesiones: ${error.message}`);
        clearAuth();
    }
}

function clearAuth() {
    currentUser = null;
    accessToken = null;
    refreshToken = null;
    sessionId = null;
    
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('sessionId');
    localStorage.removeItem('currentUser');
    
    updateAuthUI();
}

function checkStoredAuth() {
    const storedAccessToken = localStorage.getItem('accessToken');
    const storedRefreshToken = localStorage.getItem('refreshToken');
    const storedSessionId = localStorage.getItem('sessionId');
    const storedUser = localStorage.getItem('currentUser');
    
    if (storedAccessToken && storedRefreshToken && storedUser) {
        accessToken = storedAccessToken;
        refreshToken = storedRefreshToken;
        sessionId = storedSessionId;
        currentUser = JSON.parse(storedUser);
        
        // Verificar si el token sigue siendo válido
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        const now = Math.floor(Date.now() / 1000);
        
        if (payload.exp > now) {
            log('info', 'Sesión restaurada desde localStorage');
            updateAuthUI();
        } else {
            log('warning', 'Token expirado, intentando refrescar...');
            handleRefreshToken();
        }
    }
}

function updateAuthUI() {
    if (currentUser && accessToken) {
        authStatus.style.display = 'block';
        booksPanel.style.display = 'block';
        
        userInfo.innerHTML = `
            <strong>Usuario:</strong> ${currentUser.name}<br>
            <strong>Email:</strong> ${currentUser.email}<br>
            <strong>Rol:</strong> ${currentUser.role}<br>
            <strong>ID:</strong> ${currentUser.id}
        `;
        
        updateTokenInfo();
    } else {
        authStatus.style.display = 'none';
        booksPanel.style.display = 'none';
    }
}

function updateTokenInfo(statusData = null) {
    if (accessToken) {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        const now = Math.floor(Date.now() / 1000);
        const expiresIn = payload.exp - now;
        
        let tokenHtml = `
            <strong>Token JTI:</strong> ${payload.jti}<br>
            <strong>Expira en:</strong> ${Math.max(0, expiresIn)} segundos<br>
            <strong>Session ID:</strong> ${sessionId || 'N/A'}
        `;
        
        if (statusData) {
            tokenHtml += `<br><strong>Redis Status:</strong> ${statusData.redis_status}<br>`;
            tokenHtml += `<strong>Redis Exists:</strong> ${statusData.comparison.redis_exists}<br>`;
            tokenHtml += `<strong>DB Exists:</strong> ${statusData.comparison.db_exists}<br>`;
            tokenHtml += `<strong>Consistent:</strong> ${statusData.comparison.consistent}`;
        }
        
        tokenInfo.innerHTML = tokenHtml;
    }
}

// ==================== GESTIÓN DE LIBROS ====================

async function loadAllBooks() {
    try {
        log('info', 'Cargando todos los libros (XML)...');
        const response = await fetch(`${API_BASE_URL}/api/books`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const xmlText = await response.text();
            log('success', 'Libros cargados exitosamente (XML)');
            
            // Parsear XML y mostrar
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
            const books = Array.from(xmlDoc.querySelectorAll('item')).map(item => {
                const book = {};
                Array.from(item.children).forEach(child => {
                    book[child.tagName] = child.textContent;
                });
                return book;
            });
            
            displayBooks(books);
        } else {
            const result = await response.json();
            log('error', `Error al cargar libros: ${result.error || result.msg}`);
            showAlert('error', result.error || result.msg);
        }
    } catch (error) {
        log('error', `Error de conexión al cargar libros: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

async function loadDigitalBooks() {
    try {
        log('info', 'Cargando libros digitales...');
        const response = await fetch(`${API_BASE_URL}/api/books/format/digital`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', `${result.length} libros digitales cargados`);
            displayBooks(result);
        } else {
            log('error', `Error al cargar libros digitales: ${result.error || result.msg}`);
            showAlert('error', result.error || result.msg);
        }
    } catch (error) {
        log('error', `Error de conexión al cargar libros digitales: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

async function searchByIsbn() {
    const isbn = document.getElementById('searchIsbn').value.trim();
    if (!isbn) {
        showAlert('warning', 'Por favor ingresa un ISBN');
        return;
    }
    
    try {
        log('info', `Buscando libro por ISBN: ${isbn}`);
        const response = await fetch(`${API_BASE_URL}/api/books/${isbn}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', `Libro encontrado: ${result.titulo}`);
            displayBooks([result]);
        } else {
            log('error', `Error al buscar libro: ${result.msg}`);
            showAlert('error', result.msg);
        }
    } catch (error) {
        log('error', `Error de conexión al buscar libro: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

async function searchByAuthor() {
    const author = document.getElementById('searchAuthor').value.trim();
    if (!author) {
        showAlert('warning', 'Por favor ingresa un autor');
        return;
    }
    
    try {
        log('info', `Buscando libros por autor: ${author}`);
        const response = await fetch(`${API_BASE_URL}/api/books/autor/${author}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', `${result.length} libros encontrados del autor ${author}`);
            displayBooks(result);
        } else {
            log('error', `Error al buscar libros: ${result.error || result.msg}`);
            showAlert('error', result.error || result.msg);
        }
    } catch (error) {
        log('error', `Error de conexión al buscar libros: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

function displayBooks(books) {
    if (!books || books.length === 0) {
        booksContainer.innerHTML = '<p>No se encontraron libros</p>';
        return;
    }
    
    const booksHtml = books.map(book => `
        <div class="book-card">
            <h4>${book.titulo}</h4>
            <div class="book-meta">
                <strong>Autor:</strong> ${book.autor}<br>
                <strong>Editorial:</strong> ${book.editorial}<br>
                <strong>Año:</strong> ${book.año_publicacion}<br>
                <strong>Formato:</strong> ${book.formato}<br>
                <strong>Stock:</strong> ${book.stock}
            </div>
            <div class="book-price">$${parseFloat(book.precio).toFixed(2)}</div>
            ${book.descripcion ? `<p><em>${book.descripcion}</em></p>` : ''}
            <div class="book-actions">
                <button onclick="editBook('${book.isbn}')">✏️ Editar</button>
                <button onclick="deleteBook('${book.isbn}')">🗑️ Eliminar</button>
            </div>
        </div>
    `).join('');
    
    booksContainer.innerHTML = `<div class="books-grid">${booksHtml}</div>`;
}

function showCreateForm() {
    bookForm.style.display = 'block';
    bookFormElement.reset();
    document.getElementById('deleteBookBtn').style.display = 'none';
    document.getElementById('saveBookBtn').textContent = '💾 Crear Libro';
}

function editBook(isbn) {
    // Buscar el libro en la lista actual
    const bookCards = document.querySelectorAll('.book-card');
    let bookData = null;
    
    bookCards.forEach(card => {
        const actions = card.querySelector('.book-actions');
        if (actions && actions.innerHTML.includes(`editBook('${isbn}')`)) {
            const title = card.querySelector('h4').textContent;
            const meta = card.querySelector('.book-meta').textContent;
            const price = card.querySelector('.book-price').textContent;
            const description = card.querySelector('p') ? card.querySelector('p').textContent : '';
            
            // Extraer datos del meta
            const metaLines = meta.split('\n');
            const autor = metaLines[0].replace('Autor: ', '').trim();
            const editorial = metaLines[1].replace('Editorial: ', '').trim();
            const año = metaLines[2].replace('Año: ', '').trim();
            const formato = metaLines[3].replace('Formato: ', '').trim();
            const stock = metaLines[4].replace('Stock: ', '').trim();
            
            bookData = {
                isbn: isbn,
                titulo: title,
                autor: autor,
                editorial: editorial,
                año_publicacion: año,
                formato: formato,
                precio: price.replace('$', ''),
                stock: stock,
                descripcion: description.replace(/^\s*$/, '')
            };
        }
    });
    
    if (bookData) {
        // Llenar el formulario
        document.getElementById('bookIsbn').value = bookData.isbn;
        document.getElementById('bookTitulo').value = bookData.titulo;
        document.getElementById('bookAutor').value = bookData.autor;
        document.getElementById('bookEditorial').value = bookData.editorial;
        document.getElementById('bookAno').value = bookData.año_publicacion;
        document.getElementById('bookFormato').value = bookData.formato;
        document.getElementById('bookPrecio').value = bookData.precio;
        document.getElementById('bookStock').value = bookData.stock;
        document.getElementById('bookDescripcion').value = bookData.descripcion;
        
        bookForm.style.display = 'block';
        document.getElementById('deleteBookBtn').style.display = 'inline-block';
        document.getElementById('saveBookBtn').textContent = '💾 Actualizar Libro';
    }
}

async function handleBookSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    // Convertir tipos
    data.año_publicacion = parseInt(data.año_publicacion);
    data.precio = parseFloat(data.precio);
    data.stock = parseInt(data.stock) || 0;
    
    const isEdit = document.getElementById('deleteBookBtn').style.display !== 'none';
    const endpoint = isEdit ? '/api/books/update' : '/api/books/create';
    const method = isEdit ? 'PUT' : 'POST';
    
    try {
        log('info', `${isEdit ? 'Actualizando' : 'Creando'} libro: ${data.titulo}`);
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', `Libro ${isEdit ? 'actualizado' : 'creado'}: ${result.msg}`);
            showAlert('success', result.msg);
            hideBookForm();
            loadAllBooks(); // Recargar lista
        } else {
            log('error', `Error al ${isEdit ? 'actualizar' : 'crear'} libro: ${result.msg || result.error}`);
            showAlert('error', result.msg || result.error);
        }
    } catch (error) {
        log('error', `Error de conexión al ${isEdit ? 'actualizar' : 'crear'} libro: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

async function handleDeleteBook() {
    const isbn = document.getElementById('bookIsbn').value;
    if (!isbn) {
        showAlert('warning', 'No hay ISBN para eliminar');
        return;
    }
    
    if (!confirm(`¿Estás seguro de que quieres eliminar el libro con ISBN ${isbn}?`)) {
        return;
    }
    
    try {
        log('info', `Eliminando libro: ${isbn}`);
        const response = await fetch(`${API_BASE_URL}/api/books/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({ isbn: isbn })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            log('success', `Libro eliminado: ${result.msg}`);
            showAlert('success', result.msg);
            hideBookForm();
            loadAllBooks(); // Recargar lista
        } else {
            log('error', `Error al eliminar libro: ${result.msg || result.error}`);
            showAlert('error', result.msg || result.error);
        }
    } catch (error) {
        log('error', `Error de conexión al eliminar libro: ${error.message}`);
        showAlert('error', 'Error de conexión');
    }
}

function deleteBook(isbn) {
    if (!confirm(`¿Estás seguro de que quieres eliminar el libro con ISBN ${isbn}?`)) {
        return;
    }
    
    // Llenar el formulario con el ISBN y mostrar botón de eliminar
    document.getElementById('bookIsbn').value = isbn;
    document.getElementById('deleteBookBtn').style.display = 'inline-block';
    bookForm.style.display = 'block';
}

function hideBookForm() {
    bookForm.style.display = 'none';
    bookFormElement.reset();
    document.getElementById('deleteBookBtn').style.display = 'none';
}

// ==================== UTILIDADES ====================

function log(level, message) {
    const timestamp = new Date().toLocaleString();
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `
        <span class="log-timestamp">[${timestamp}]</span>
        <span class="log-level ${level}">[${level.toUpperCase()}]</span>
        <span class="log-message">${message}</span>
    `;
    
    logsContainer.appendChild(logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

function showAlert(type, message) {
    // Remover alertas existentes
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    alert.textContent = message;
    
    // Insertar al inicio del container
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function clearLogs() {
    logsContainer.innerHTML = '';
    log('info', 'Logs limpiados');
}

function exportLogs() {
    const logs = Array.from(logsContainer.children).map(entry => entry.textContent).join('\n');
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    log('info', 'Logs exportados');
}

// Interceptor para manejar tokens expirados automáticamente
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const response = await originalFetch(...args);
    
    if (response.status === 401 && accessToken) {
        log('warning', 'Token expirado, intentando refrescar...');
        await handleRefreshToken();
        
        // Reintentar la petición original con el nuevo token
        if (accessToken) {
            const [url, options] = args;
            if (options && options.headers) {
                options.headers.Authorization = `Bearer ${accessToken}`;
            }
            return originalFetch(url, options);
        }
    }
    
    return response;
};
