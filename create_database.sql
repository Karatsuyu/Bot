-- Script SQL para crear la base de datos en pgAdmin
-- Ejecuta esto en la herramienta de consultas de pgAdmin

-- Crear la base de datos
CREATE DATABASE telegram_archive
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- Comentario sobre la base de datos
COMMENT ON DATABASE telegram_archive
    IS 'Base de datos para almacenar grupos, canales y bots de Telegram';
