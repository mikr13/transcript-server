# Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview

This is a FastAPI server that provides an API for fetching YouTube transcript data using the `youtube-transcript-api` library. The project uses `uv` for modern Python dependency management.

## Key Features

- Fetch transcript data for YouTube videos by video ID
- Return raw transcript data in JSON format with text, start time, and duration
- Handle multiple transcript languages and generated vs manual transcripts
- Proper error handling for various YouTube API exceptions
- Health check endpoints and API documentation via FastAPI

## Development Guidelines

### Dependencies

- Use `uv` for all dependency management operations
- Add new dependencies with `uv add <package>`
- The project uses FastAPI, uvicorn, and youtube-transcript-api as core dependencies

### Code Style

- Follow FastAPI best practices for endpoint definitions
- Use proper HTTP status codes and exception handling
- Include comprehensive docstrings for all endpoints
- Type hints are required for all functions and endpoints

### API Design

- All endpoints should return JSON responses
- Use proper HTTP methods (GET for fetching data)
- Include comprehensive error handling with appropriate HTTP status codes
- Provide clear API documentation through FastAPI's automatic docs

### Running the Server

- Use `uv run main.py` to start the development server
- The server runs on `http://localhost:8000` by default
- API documentation is available at `http://localhost:8000/docs`

### Testing

- Test endpoints with various YouTube video IDs
- Handle edge cases like disabled transcripts, unavailable videos, etc.
- Verify proper error responses and status codes
