Feature: Validaciones E2E del Frontend con IA

  @ui @ai
  Scenario: La IA verifica que la página principal carga la lista de películas
    Given the frontend is running
    When I open the frontend homepage
    # Para el texto principal y estructura básica
    Then the AI visually confirms that "the main title should be 'Catálogo de Películas' and there is an 'Add Movie' form"

  @ui @ai
  Scenario: Rellenar el formulario para interactuar con la web
    Given the frontend is running
    When I open the frontend homepage
    When the AI acts on the page to "fill the add movie form with title 'Pirates of the Caribbean', year '2003', director 'Gore Verbinski' and click the submit button"
    Then the AI visually confirms that "the movie 'Pirates of the Caribbean' appears in the movie catalog list"
