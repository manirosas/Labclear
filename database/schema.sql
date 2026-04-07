CREATE DATABASE IF NOT EXISTS labclear_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE labclear_db;
 
CREATE TABLE usuarios (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  nombre          VARCHAR(120) NOT NULL,
  correo          VARCHAR(200) UNIQUE NOT NULL,
  contrasena      VARCHAR(200) NOT NULL,
  sexo            ENUM('M','F') DEFAULT NULL,
  fecha_nac       DATE DEFAULT NULL,
  aviso_aceptado  TINYINT(1) DEFAULT 0,
  creado_en       DATETIME DEFAULT NOW()
);
 
CREATE TABLE resultados (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id      INT NOT NULL,
  tipo_estudio    VARCHAR(60) NOT NULL,
  fecha_estudio   DATE NOT NULL,
  valores         JSON NOT NULL,
  resumen_ia      TEXT,
  estado          ENUM('normal','precaucion','alerta') DEFAULT 'normal',
  creado_en       DATETIME DEFAULT NOW(),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
 