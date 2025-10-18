-- Base de datos para el microservicio de Libros con JWT + Redis
CREATE DATABASE IF NOT EXISTS Libros CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'libros_user'@'localhost' IDENTIFIED BY '666';
GRANT ALL PRIVILEGES ON Libros.* TO 'libros_user'@'localhost';
FLUSH PRIVILEGES;

USE Libros;

-- Usuarios del sistema
CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('user','admin') NOT NULL DEFAULT 'user',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_users_email (email),
  INDEX idx_users_name (name)
) ENGINE=InnoDB;

-- Tabla de libros
CREATE TABLE IF NOT EXISTS books (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  isbn VARCHAR(20) NOT NULL UNIQUE,
  titulo VARCHAR(255) NOT NULL,
  autor VARCHAR(255) NOT NULL,
  editorial VARCHAR(255) NOT NULL,
  año_publicacion YEAR NOT NULL,
  formato ENUM('fisico','digital','ambos') NOT NULL DEFAULT 'fisico',
  precio DECIMAL(10,2) NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  descripcion TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_books_isbn (isbn),
  INDEX idx_books_autor (autor),
  INDEX idx_books_formato (formato),
  INDEX idx_books_titulo (titulo)
) ENGINE=InnoDB;

-- Intentos de login (para auditoría y rate-limiting)
CREATE TABLE IF NOT EXISTS login_attempts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email VARCHAR(120) NOT NULL,
  success TINYINT(1) NOT NULL,
  ip VARCHAR(45) NULL,
  user_agent VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_login_attempts_email (email),
  INDEX idx_login_created_at (created_at)
) ENGINE=InnoDB;

-- Sesiones de usuario (una sesión por refresh token / dispositivo)
CREATE TABLE IF NOT EXISTS user_sessions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  session_id CHAR(36) NOT NULL, -- UUID4
  ip VARCHAR(45) NULL,
  user_agent VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used_at TIMESTAMP NULL DEFAULT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_user_sessions_session_id (session_id),
  INDEX idx_user_sessions_user (user_id),
  CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabla general para cualquier JWT emitido (access o refresh), útil para revocar por JTI
CREATE TABLE IF NOT EXISTS jwt_tokens (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  jti CHAR(36) NOT NULL, -- JWT ID
  token_type ENUM('access','refresh') NOT NULL,
  session_id CHAR(36) NULL, -- vínculo con la sesión (normalmente para refresh)
  issued_at DATETIME NOT NULL,
  expires_at DATETIME NOT NULL,
  revoked TINYINT(1) NOT NULL DEFAULT 0,
  parent_refresh_jti CHAR(36) NULL, -- encadenamiento si el access fue emitido vía refresh
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_jwt_tokens_jti (jti),
  INDEX idx_jwt_tokens_user (user_id),
  INDEX idx_jwt_tokens_exp (expires_at),
  CONSTRAINT fk_jwt_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabla específica de refresh tokens (activos), referenciando al registro en jwt_tokens
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  jti CHAR(36) NOT NULL, -- JTI del refresh token
  session_id CHAR(36) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  revoked_at TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_refresh_tokens_jti (jti),
  INDEX idx_refresh_tokens_user (user_id),
  CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Auditoría de eventos relacionados con tokens (emitidos, refrescados, revocados, verificados)
CREATE TABLE IF NOT EXISTS token_audit (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NULL,
  jti CHAR(36) NULL,
  action ENUM('issued','refreshed','revoked','validated','rejected') NOT NULL,
  detail VARCHAR(255) NULL,
  ip VARCHAR(45) NULL,
  user_agent VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_token_audit_jti (jti),
  INDEX idx_token_audit_user (user_id)
) ENGINE=InnoDB;

-- Insertar algunos libros de ejemplo
INSERT INTO books (isbn, titulo, autor, editorial, año_publicacion, formato, precio, stock, descripcion) VALUES
('978-84-376-0494-7', 'Cien años de soledad', 'Gabriel García Márquez', 'Cátedra', 1967, 'ambos', 15.99, 25, 'Una de las obras más importantes de la literatura hispanoamericana'),
('978-84-376-0495-4', 'El Quijote', 'Miguel de Cervantes', 'Cátedra', 1905, 'ambos', 18.50, 30, 'Obra cumbre de la literatura española'),
('978-84-376-0496-1', '1984', 'George Orwell', 'Debolsillo', 1949, 'digital', 12.99, 0, 'Novela distópica sobre el control totalitario'),
('978-84-376-0497-8', 'El señor de los anillos', 'J.R.R. Tolkien', 'Minotauro', 1954, 'fisico', 25.99, 15, 'Trilogía épica de fantasía'),
('978-84-376-0498-5', 'Harry Potter y la piedra filosofal', 'J.K. Rowling', 'Salamandra', 1997, 'ambos', 19.99, 40, 'Primera novela de la serie de Harry Potter');

-- Insertar usuario administrador de ejemplo
INSERT INTO users (name, email, password_hash, role) VALUES
('Admin', 'admin@libros.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8Kz8Kz2', 'admin');
