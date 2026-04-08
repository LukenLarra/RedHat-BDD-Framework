# language: en

Feature: Movie management
  As a user
  I want to manage a movie catalog
  So that I can easily consult and add movies

  Scenario: Retrieve all movies
    Given the API is running
    When I make a GET request to "/api/movies"
    Then I get a response with status code 200
    And the response contains a list of movies

  Scenario: Retrieve a movie by ID
    Given the API is running
    And there is a movie with ID 1
    When I make a GET request to "/api/movies/1"
    Then I get a response with status code 200
    And the response contains the details of the movie with ID 1

  @ai
  Scenario: Verify a movie specific aspect dynamically with AI
    Given the API is running
    And there is a movie with ID 2
    When I make a GET request to "/api/movies/2"
    Then I get a response with status code 200
    And the LLM confirms that "the movie was directed by Quentin Tarantino"

  # AI Capability: Advanced list evaluation and mathematical bounds check without customized loops
  @ai
  Scenario: Validate movies release era dynamically with AI
    Given the API is running
    When I make a GET request to "/api/movies"
    Then I get a response with status code 200
    And the LLM confirms that "all movies in the data list were released between 1970 and 2020"

  # AI Capability: Aggregation, counting and complex logic evaluation on collections
  @ai
  Scenario: Analyze director frequencies dynamically with AI
    Given the API is running
    When I make a GET request to "/api/movies"
    Then I get a response with status code 200
    And the LLM confirms that "Christopher Nolan is the most frequent director in the list, with exactly 3 movies"

  # AI Capability: Semantic deduction and 'Fuzzy Matching' (connecting external knowledge to the raw data)
  @ai
  Scenario: Identify movie genres using fuzzy matching with AI
    Given the API is running
    When I make a GET request to "/api/movies"
    Then I get a response with status code 200
    And the LLM confirms that "the list includes at least one mob/mafia movie from 1972 and a nonlinear crime film from 1994"

  # AI Capability: Schema validation (keys, types and overall structure validation) without external libraries
  @ai
  Scenario: Validate API response schema using AI
    Given the API is running
    When I make a GET request to "/api/movies"
    Then I get a response with status code 200
    And the LLM confirms that "every element in the data array is a valid dictionary containing id, title, year, and director keys with their corresponding values (int, string)"
