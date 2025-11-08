# NFR BDD Scenarios

## Обзор
Данный документ содержит BDD (Behavior Driven Development) сценарии для приёмки Non-Functional Requirements.

## Сценарии для ключевых NFR

### NFR-001: Время ответа API

#### Сценарий 1: Успешный быстрый ответ API
```gherkin
Feature: API Response Time
  As a user
  I want API to respond quickly
  So that I have good user experience

Scenario: API responds within acceptable time
  Given the API server is running
  And the system is under normal load
  When I make a request to POST /items
  Then the response should be received within 200ms
  And the response status should be 200

Scenario: API performance under load
  Given the API server is running
  And there are 100 concurrent users
  When I make a request to GET /items/{id}
  Then the 95th percentile response time should be ≤ 200ms
  And the response should be successful

Scenario: API timeout under extreme load
  Given the API server is running
  And there are 1000 concurrent users
  When I make a request to POST /items
  Then the response time may exceed 200ms
  But the system should not crash
  And should return appropriate error after timeout

Feature: Input Data Validation
  As a system
  I want to validate all input data
  So that the system is secure from malicious input

Scenario: Valid input passes validation
  Given the API server is running
  And I have valid input data
  When I send a POST request to /items with name="valid_item"
  Then the validation should pass
  And the item should be created successfully
  And the response should contain the created item

Scenario: Invalid input is rejected
  Given the API server is running
  And I have invalid input data
  When I send a POST request to /items with name=""
  Then the validation should fail
  And the response should be 422 Unprocessable Entity
  And the error message should indicate validation failure

Scenario: Malicious input is blocked
  Given the API server is running
  And I have malicious input data
  When I send a POST request to /items with name="<script>alert('xss')</script>"
  Then the validation should fail
  And the malicious content should be sanitized
  And the system should remain secure

Feature: Error Handling
  As a user
  I want to receive clear error messages
  So that I can understand what went wrong

Scenario: Clear error message for not found
  Given the API server is running
  And there are no items with ID 999
  When I send a GET request to /items/999
  Then the response should be 404 Not Found
  And the error message should be clear and helpful
  And the error should be logged for monitoring

Scenario: Consistent error format
  Given the API server is running
  When I send an invalid request
  Then the error response should follow the standard format
  And should contain error code and message
  And should be in JSON format

Scenario: System error handling
  Given the API server is running
  And the database is unavailable
  When I send a GET request to /items/1
  Then the system should handle the error gracefully
  And should return a 500 Internal Server Error
  And should not expose internal system details
  And should log the error for debugging

Feature: Service Availability
  As an administrator
  I want to monitor service health
  So that I can ensure high availability

Scenario: Health check endpoint responds
  Given the API server is running
  When I send a GET request to /health
  Then the response should be 200 OK
  And should contain status information
  And should respond within 1 second

Scenario: Service recovery after failure
  Given the API server was down
  When the server comes back online
  Then the health check should start passing
  And the service should be available within 5 minutes
  And monitoring should detect the recovery

Feature: Attack Protection
  As a system
  I want to protect against attacks
  So that the service remains available

Scenario: Rate limiting prevents abuse
  Given the API server is running
  And rate limiting is configured to 100 requests per minute
  When I send 101 requests in one minute
  Then the first 100 requests should succeed
  And the 101st request should be rate limited
  And should return 429 Too Many Requests

Scenario: Legitimate high traffic is not blocked
  Given the API server is running
  And rate limiting is configured
  When legitimate users generate high traffic
  Then the system should handle the load
  And should not block legitimate users
  And should only block clearly malicious traffic
