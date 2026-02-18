/**
 * Aplicación cliente para consumir la API de películas
 */

const API_BASE_URL = "http://localhost:5000";

// Elementos del DOM
const moviesList = document.getElementById("moviesList");
const loading = document.getElementById("loading");
const errorDiv = document.getElementById("error");
const addMovieForm = document.getElementById("addMovieForm");
const refreshBtn = document.getElementById("refreshBtn");
const apiStatus = document.getElementById("apiStatus");

/**
 * Muestra/oculta el indicador de carga
 */
function toggleLoading(show) {
  loading.style.display = show ? "block" : "none";
}

/**
 * Muestra un mensaje de error
 */
function showError(message) {
  errorDiv.textContent = `❌ Error: ${message}`;
  errorDiv.style.display = "block";
  setTimeout(() => {
    errorDiv.style.display = "none";
  }, 5000);
}

/**
 * Muestra un mensaje de éxito
 */
function showSuccess(message) {
  const successDiv = document.createElement("div");
  successDiv.className = "success";
  successDiv.textContent = `✓ ${message}`;
  moviesList.parentElement.insertBefore(successDiv, moviesList);
  setTimeout(() => successDiv.remove(), 3000);
}

/**
 * Actualiza el estado de la API
 */
function updateApiStatus(online) {
  apiStatus.className = online ? "status-indicator online" : "status-indicator offline";
  apiStatus.title = online ? "API conectada" : "API desconectada";
}

/**
 * Obtiene todas las películas de la API
 */
async function fetchMovies() {
  try {
    toggleLoading(true);
    errorDiv.style.display = "none";

    const response = await fetch(`${API_BASE_URL}/api/movies`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      displayMovies(data.data);
      updateApiStatus(true);
    } else {
      throw new Error(data.error || "Error desconocido");
    }
  } catch (error) {
    console.error("Error al obtener películas:", error);
    showError("No se pudo conectar con la API. Asegúrate de que el backend esté corriendo.");
    updateApiStatus(false);
    moviesList.innerHTML =
      '<p style="text-align: center; color: #64748b;">No hay películas disponibles</p>';
  } finally {
    toggleLoading(false);
  }
}

/**
 * Renderiza las películas en el DOM
 */
function displayMovies(movies) {
  if (movies.length === 0) {
    moviesList.innerHTML =
      '<p style="text-align: center; color: #64748b;">No hay películas en la base de datos</p>';
    return;
  }

  moviesList.innerHTML = movies
    .map(
      (movie) => `
        <div class="movie-card">
            <h3>${escapeHtml(movie.title)}</h3>
            <span class="year">${movie.year}</span>
            <p class="director">Dirigida por ${escapeHtml(movie.director)}</p>
        </div>
    `
    )
    .join("");
}

/**
 * Escapa HTML para prevenir XSS
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Agrega una nueva película
 */
async function addMovie(event) {
  event.preventDefault();

  const title = document.getElementById("title").value.trim();
  const year = parseInt(document.getElementById("year").value);
  const director = document.getElementById("director").value.trim();

  if (!title || !year || !director) {
    showError("Todos los campos son requeridos");
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/movies`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title, year, director }),
    });

    const data = await response.json();

    if (data.success) {
      showSuccess(`Película "${title}" agregada exitosamente`);
      addMovieForm.reset();
      fetchMovies(); // Recargar la lista
    } else {
      throw new Error(data.error || "Error al agregar película");
    }
  } catch (error) {
    console.error("Error al agregar película:", error);
    showError("No se pudo agregar la película. Verifica la conexión con la API.");
  }
}

/**
 * Verifica el estado de la API
 */
async function checkApiHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    updateApiStatus(data.status === "healthy");
  } catch (error) {
    updateApiStatus(false);
  }
}

// Event Listeners
addMovieForm.addEventListener("submit", addMovie);
refreshBtn.addEventListener("click", fetchMovies);

// Inicializar la aplicación
window.addEventListener("DOMContentLoaded", () => {
  console.log("🎬 Aplicación de películas iniciada");
  fetchMovies();

  // Verificar estado de la API cada 30 segundos
  setInterval(checkApiHealth, 30000);
});
