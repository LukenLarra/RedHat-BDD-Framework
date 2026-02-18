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
