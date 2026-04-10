Feature: Validaciones E2E del Frontend con IA

  @ui @ai
  Scenario: La IA verifica que la página principal carga la lista de películas
    Given the frontend is running
    When I open the frontend homepage
    # Para el texto principal y estructura básica
    Then the AI visually confirms that "the main title should be 'Movie Catalog' and there is an 'Add Movie' form"
