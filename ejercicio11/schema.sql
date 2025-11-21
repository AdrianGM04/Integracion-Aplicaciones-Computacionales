CREATE DATABASE IF NOT EXISTS JWT03 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'libros_user'@'localhost' IDENTIFIED BY '666';
GRANT ALL PRIVILEGES ON JWT03.* TO 'libros_user'@'localhost';
FLUSH PRIVILEGES;

USE JWT03;

-- Usuarios del sistema
CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('user','admin') NOT NULL DEFAULT 'user',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_users_username (username),
  INDEX idx_users_email (email)
) ENGINE=InnoDB;

-- Intentos de login (para auditoría y rate-limiting manual si se desea)
CREATE TABLE IF NOT EXISTS login_attempts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(120) NOT NULL,
  success TINYINT(1) NOT NULL,
  ip VARCHAR(45) NULL,
  user_agent VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_login_attempts_username (username),
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




