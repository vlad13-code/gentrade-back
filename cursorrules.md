"# Cursor Rules for Project

## Project Overview

**Project Name:** GenTrade\
**Description:** GenTrade is a web-based platform designed to empower individuals with no programming or trading experience to easily create, deploy, and manage automated trading bots. Through an intuitive chat interface, users can seamlessly design strategies, monitor performance, and optimize their bots without requiring technical expertise.\
**Tech Stack:**

*   Frontend: Next.js 15, TypeScript, Tailwind CSS, shadcn/UI, Radix UI, Lucide Icons
*   Backend: Freqtrade, FastAPI, LangGraph, SQLAlchemy, Pydantic
*   Database: PostgreSQL
*   AI Integration: GPT-4o or Claude 3.5 Sonnet
*   IDE Tool: Cursor AI for AI-powered coding

**Key Features:**

*   Secure Authentication with role-based access
*   Interactive Chat Interface for bot creation
*   Multiple Strategy Creation
*   User Strategies Library
*   A rich Strategy Library
*   Bot Creation Lifecycle (creation, backtesting, paper trading, live trading)
*   Real-Time Analytics Dashboards
*   Exchange Integration
*   AI Recommendations
*   Community Support

## Project Structure

### Root Directory:

*   Contains the main configuration files and documentation.

### /frontend:

*   Contains all frontend-related code, including components, styles, and assets.

    *   **/components:**

        *   AI Chat Interface
        *   Strategy Widgets
        *   Notification System

    *   **/assets:**

        *   Logo
        *   Icons
        *   Media files

    *   **/styles:**

        *   Global CSS
        *   Tailwind Configuration

### /backend:

*   Contains all backend-related code, including API routes and database models.

    *   **/controllers:**

        *   BotManagementController
        *   StrategyController

    *   **/models:**

        *   UserModel
        *   StrategyModel

    *   **/routes:**

        *   /api/v1/users
        *   /api/v1/strategies

    *   **/config:** Configuration files for environment variables and application settings.

### /tests:

*   Contains unit and integration tests for both frontend and backend.

## Development Guidelines

**Coding Standards:**

*   Follow the Airbnb JavaScript style guide for uniformity.
*   Use TypeScript for type safety.

**Component Organization:**

*   Organize components by functionality. Components should be reusable and stored in shared directories if applicable.

## Cursor IDE Integration

**Setup Instructions:**

1.  Clone the repository from the version control system.
2.  Install dependencies for both frontend and backend using `npm install` and `pip install` respectively.
3.  Configure environment variables as per the `/config` documentation.
4.  Run backend service using FastAPI and frontend using a Next.js server.

**Key Commands:**

*   `npm run dev` for starting the Next.js development server.
*   `uvicorn main:app --reload` for starting the FastAPI server.

## Additional Context

**User Roles:**

*   Admin: Full access to all functionalities.
*   Trader: Can create and manage bots and strategies.
*   Viewer: Can view strategies and performance dashboards.

**Accessibility Considerations:**

*   Ensure all interactive elements have accessible labels and can be navigated using a keyboard.
*   Implement color contrast standards for users with visual impairments.

## Expert Rules for API Development

**Key Principles:**

*   Write concise, technical responses with accurate Python examples.
*   Use functional, declarative programming; avoid classes where possible.
*   Prefer iteration and modularization over code duplication.
*   Use descriptive variable names with auxiliary verbs (e.g., is_active, has_permission).
*   Use lowercase with underscores for directories and files (e.g., routers/user_routes.py).
*   Favor named exports for routes and utility functions.
*   Use the Receive an Object, Return an Object (RORO) pattern.

**Python/FastAPI**

*   Use `def` for pure functions and `async def` for asynchronous operations.
*   Use type hints for all function signatures. Prefer Pydantic models over raw dictionaries for input validation.
*   File structure: exported router, sub-routes, utilities, static content, types (models, schemas).
*   Avoid unnecessary curly braces in conditional statements.
*   For single-line statements in conditionals, omit curly braces.
*   Use concise, one-line syntax for simple conditional statements (e.g., `if condition: do_something()`).

**Error Handling and Validation**

*   Prioritize error handling and edge cases:

    *   Handle errors and edge cases at the beginning of functions.
    *   Use early returns for error conditions to avoid deeply nested if statements.
    *   Place the happy path last in the function for improved readability.
    *   Avoid unnecessary else statements; use the if-return pattern instead.
    *   Use guard clauses to handle preconditions and invalid states early.
    *   Implement proper error logging and user-friendly error messages.
    *   Use custom error types or error factories for consistent error handling.

**Dependencies**

*   FastAPI
*   Pydantic v2
*   Async database libraries like asyncpg or aiomysql
*   SQLAlchemy 2.0 (if using ORM features)

**FastAPI-Specific Guidelines**

*   Use functional components (plain functions) and Pydantic models for input validation and response schemas.
*   Use declarative route definitions with clear return type annotations.
*   Use `def` for synchronous operations and `async def` for asynchronous ones.
*   Minimize `@app.on_event("startup")` and `@app.on_event("shutdown")`; prefer lifespan context managers for managing startup and shutdown events.
*   Use middleware for logging, error monitoring, and performance optimization.
*   Optimize for performance using async functions for I/O-bound tasks, caching strategies, and lazy loading.
*   Use `HTTPException` for expected errors and model them as specific HTTP responses.
*   Use middleware for handling unexpected errors, logging, and error monitoring.
*   Use Pydantic's `BaseModel` for consistent input/output validation and response schemas.

**Performance Optimization**

*   Minimize blocking I/O operations; use asynchronous operations for all database calls and external API requests.
*   Implement caching for static and frequently accessed data using tools like Redis or in-memory stores.
*   Optimize data serialization and deserialization with Pydantic.
*   Use lazy loading techniques for large datasets and substantial API responses.

**Key Conventions**

1.  Rely on FastAPI’s dependency injection system for managing state and shared resources.

2.  Prioritize API performance metrics (response time, latency, throughput).

3.  Limit blocking operations in routes:

    *   Favor asynchronous and non-blocking flows.
    *   Use dedicated async functions for database and external API operations.
    *   Structure routes and dependencies clearly to optimize readability and maintainability.

Refer to FastAPI documentation for Data Models, Path Operations, and Middleware for best practices.
