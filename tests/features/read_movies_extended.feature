# language: en

Feature: Extended Movie Retrieval
  As a user
  I want to query movies from the catalog
  So that I can verify the retrieval endpoints without modifying the database

  Scenario: Retrieve movie with ID 2
    Given the API is running
    When I make a GET request to "/api/movies/2"
    Then I get a response with status code 200
    And the response contains the details of the movie with ID 2

  Scenario: Retrieve movie with ID 3
    Given the API is running
    When I make a GET request to "/api/movies/3"
    Then I get a response with status code 200
    And the response contains the details of the movie with ID 3

  Scenario: Retrieve movie with ID 4
    Given the API is running
    When I make a GET request to "/api/movies/4"
    Then I get a response with status code 200
    And the response contains the details of the movie with ID 4

  Scenario: Attempt to retrieve a non-existent movie
    Given the API is running
    When I make a GET request to "/api/movies/9999"
    Then I get a response with status code 404
