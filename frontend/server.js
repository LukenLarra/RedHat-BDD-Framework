/**
 * Servidor Node.js con Express para servir el frontend
 */
const express = require('express');
const path = require('path');
const app = express();

const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || 'http://localhost:5000';

// Middleware para servir archivos estáticos
app.use(express.static('public'));
app.use('/src', express.static('src'));

// Ruta principal
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Endpoint de configuración para el cliente
app.get('/config', (req, res) => {
  res.json({
    apiUrl: API_URL,
  });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log('🚀 Servidor frontend iniciado');
  console.log(`📍 URL: http://localhost:${PORT}`);
  console.log(`🔗 API Backend: ${API_URL}`);
});
