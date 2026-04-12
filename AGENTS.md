# AGENTS.md - Song Master Development Guidelines

## Build, Lint, and Test Commands

### Development Environment Setup

**Using Dev Container (Recommended):**
```bash
# Open in VS Code with dev container
code .
# Select "Reopen in Container" when prompted
```

**Using Docker Compose:**
```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Python Backend

**Install dependencies (in dev container):**
```bash
pip install -r requirements.txt
```

**Run the backend (in dev container):**
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Run tests in container:**
```bash
docker-compose exec backend python -m pytest
```

**Run a single test (when tests are added):**
```bash
# Run all tests
docker-compose exec backend python -m pytest

# Run a specific test file
docker-compose exec backend python -m pytest tests/test_ai_functions.py

# Run a specific test function
docker-compose exec backend python -m pytest tests/test_ai_functions.py::test_build_prompts -v

# Run tests with coverage
docker-compose exec backend python -m pytest --cov=. --cov-report=html
```

**Lint and format Python code (in dev container):**
```bash
# Install linting tools
pip install black isort flake8 mypy

# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type check
mypy . --ignore-missing-imports
```

### JavaScript/TypeScript Frontend

**Install dependencies (in container):**
```bash
docker-compose exec frontend npm install
```

**Run the frontend (in container):**
```bash
docker-compose exec frontend npm run dev
```

**Build frontend for production:**
```bash
docker-compose exec frontend npm run build
```

**Run a single test (when tests are added):**
```bash
# Run all tests
docker-compose exec frontend npm test

# Run a specific test file
docker-compose exec frontend npm test -- SongDetailPage.test.tsx

# Run tests in watch mode
docker-compose exec frontend npm run test:watch

# Run tests with coverage
docker-compose exec frontend npm run test:coverage
```

**Lint and format frontend code (in container):**
```bash
# Install additional linting tools if needed
docker-compose exec frontend npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin prettier

# Format code
docker-compose exec frontend npm run format

# Lint code
docker-compose exec frontend npm run lint

# Type check
docker-compose exec frontend npm run type-check
```

### Docker Development Workflow

**Build and run with Docker Compose:**
```bash
# Build all services
docker-compose build

# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Run tests in containers
docker-compose exec backend python -m pytest

# Access running containers
docker-compose exec backend bash
docker-compose exec frontend sh

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

**Health checks:**
```bash
# Backend health check
curl http://localhost:8000/health

# Frontend health check
curl http://localhost:5173
```

## Code Style Guidelines

### Python Code Style

**Imports:**
- Use absolute imports instead of relative imports
- Group imports: standard library, third-party, local modules
- Use `from typing import` for type hints
- Sort imports alphabetically within groups

```python
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate

from backend.shared.helpers import load_resources
```

**Naming Conventions:**
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Type variables: `PascalCase` with `T` prefix
- Private methods/attributes: `_single_underscore_prefix`

**Type Hints:**
- Use comprehensive type hints for all function parameters and return values
- Use `Optional` for nullable types
- Use `Union` for multiple possible types
- Use `TypedDict` for structured dictionaries
- Use `dataclasses` for simple data structures

```python
from typing import Optional, Dict, List
from dataclasses import dataclass

@dataclass
class SongMetadata:
    title: str
    artist: Optional[str] = None
    bpm: int = 120

def process_song(prompt: str, metadata: Optional[Dict[str, Any]] = None) -> SongMetadata:
    # Implementation
    pass
```

**Docstrings:**
- Use triple-quoted docstrings for all public functions and classes
- Follow Google-style docstring format
- Include parameter descriptions and return value descriptions

```python
def generate_song(prompt: str, use_local: bool = False) -> Dict[str, Any]:
    """Generate a song based on the given prompt.

    Args:
        prompt: The user's song description or request
        use_local: Whether to use local AI model instead of OpenRouter

    Returns:
        Dictionary containing the generated song data

    Raises:
        RuntimeError: If song generation fails
    """
    pass
```

**Error Handling:**
- Use specific exception types, not generic `Exception`
- Provide meaningful error messages
- Use context managers for resource cleanup
- Log errors appropriately

```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    logger.error(f"Failed to fetch data from {url}: {e}")
    raise RuntimeError(f"API request failed: {e}") from e
```

**Code Structure:**
- Keep functions under 50 lines when possible
- Use early returns to reduce nesting
- Separate concerns into different modules
- Use configuration files instead of hardcoding values

### JavaScript/TypeScript Code Style

**Imports:**
- Use ES6 imports/exports
- Group imports: React, third-party libraries, local components/utilities
- Use absolute imports with path mapping
- Sort imports alphabetically within groups

```typescript
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import { SongDetail } from '../types';
import { apiService } from '../services/apiService';
```

**Component Structure:**
- Use functional components with hooks
- Prefer custom hooks for shared logic
- Use TypeScript interfaces for props
- Keep components under 200 lines

```typescript
interface SongCardProps {
  song: SongDetail;
  onEdit?: (songId: number) => void;
}

export const SongCard: React.FC<SongCardProps> = ({ song, onEdit }) => {
  const handleEdit = () => {
    onEdit?.(song.id);
  };

  return (
    <div className="song-card">
      <h3>{song.title}</h3>
      <button onClick={handleEdit}>Edit</button>
    </div>
  );
};
```

**Naming Conventions:**
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_CASE`
- Files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Custom hooks: `useCamelCase`

**Styling:**
- Use CSS modules or styled-components
- Follow BEM naming convention for CSS classes
- Use design system tokens for colors, spacing, typography

### General Guidelines

**Security:**
- Never log or commit API keys, secrets, or sensitive data
- Use environment variables for configuration
- Validate user inputs on both client and server
- Implement proper authentication and authorization

**Performance:**
- Avoid unnecessary re-renders in React components
- Use memoization for expensive computations
- Implement proper loading states and error boundaries
- Optimize database queries and API calls

**Testing:**
- Write unit tests for pure functions and utilities
- Write integration tests for API endpoints
- Write E2E tests for critical user flows
- Aim for >80% code coverage
- Use descriptive test names and arrange-act-assert pattern

**Git Workflow:**
- Use feature branches for development
- Write clear, concise commit messages
- Squash commits before merging
- Use pull requests for code review
- Follow semantic versioning for releases

**Documentation:**
- Keep README.md updated with setup and usage instructions
- Document complex business logic in code comments
- Use API documentation tools like Swagger/OpenAPI
- Maintain changelog for releases

## Code Style Guidelines

### Python Code Style

**Imports:**
- Use absolute imports instead of relative imports
- Group imports: standard library, third-party, local modules
- Use `from typing import` for type hints
- Sort imports alphabetically within groups

```python
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate

from backend.shared.helpers import load_resources
```

**Naming Conventions:**
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Type variables: `PascalCase` with `T` prefix
- Private methods/attributes: `_single_underscore_prefix`

**Type Hints:**
- Use comprehensive type hints for all function parameters and return values
- Use `Optional` for nullable types
- Use `Union` for multiple possible types
- Use `TypedDict` for structured dictionaries
- Use `dataclasses` for simple data structures

```python
from typing import Optional, Dict, List
from dataclasses import dataclass

@dataclass
class SongMetadata:
    title: str
    artist: Optional[str] = None
    bpm: int = 120

def process_song(prompt: str, metadata: Optional[Dict[str, Any]] = None) -> SongMetadata:
    # Implementation
    pass
```

**Docstrings:**
- Use triple-quoted docstrings for all public functions and classes
- Follow Google-style docstring format
- Include parameter descriptions and return value descriptions

```python
def generate_song(prompt: str, use_local: bool = False) -> Dict[str, Any]:
    """Generate a song based on the given prompt.

    Args:
        prompt: The user's song description or request
        use_local: Whether to use local AI model instead of OpenRouter

    Returns:
        Dictionary containing the generated song data

    Raises:
        RuntimeError: If song generation fails
    """
    pass
```

**Error Handling:**
- Use specific exception types, not generic `Exception`
- Provide meaningful error messages
- Use context managers for resource cleanup
- Log errors appropriately

```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    logger.error(f"Failed to fetch data from {url}: {e}")
    raise RuntimeError(f"API request failed: {e}") from e
```

**Code Structure:**
- Keep functions under 50 lines when possible
- Use early returns to reduce nesting
- Separate concerns into different modules
- Use configuration files instead of hardcoding values

### JavaScript/TypeScript Code Style

**Imports:**
- Use ES6 imports/exports
- Group imports: React, third-party libraries, local components/utilities
- Use absolute imports with path mapping
- Sort imports alphabetically within groups

```typescript
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import { SongDetail } from '../types';
import { apiService } from '../services/apiService';
```

**Component Structure:**
- Use functional components with hooks
- Prefer custom hooks for shared logic
- Use TypeScript interfaces for props
- Keep components under 200 lines

```typescript
interface SongCardProps {
  song: SongDetail;
  onEdit?: (songId: number) => void;
}

export const SongCard: React.FC<SongCardProps> = ({ song, onEdit }) => {
  const handleEdit = () => {
    onEdit?.(song.id);
  };

  return (
    <div className="song-card">
      <h3>{song.title}</h3>
      <button onClick={handleEdit}>Edit</button>
    </div>
  );
};
```

**Naming Conventions:**
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_CASE`
- Files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Custom hooks: `useCamelCase`

**Styling:**
- Use CSS modules or styled-components
- Follow BEM naming convention for CSS classes
- Use design system tokens for colors, spacing, typography

### General Guidelines

**Security:**
- Never log or commit API keys, secrets, or sensitive data
- Use environment variables for configuration
- Validate user inputs on both client and server
- Implement proper authentication and authorization

**Performance:**
- Avoid unnecessary re-renders in React components
- Use memoization for expensive computations
- Implement proper loading states and error boundaries
- Optimize database queries and API calls

**Testing:**
- Write unit tests for pure functions and utilities
- Write integration tests for API endpoints
- Write E2E tests for critical user flows
- Aim for >80% code coverage
- Use descriptive test names and arrange-act-assert pattern

**Git Workflow:**
- Use feature branches for development
- Write clear, concise commit messages
- Squash commits before merging
- Use pull requests for code review
- Follow semantic versioning for releases

**Documentation:**
- Keep README.md updated with setup and usage instructions
- Document complex business logic in code comments
- Use API documentation tools like Swagger/OpenAPI
- Maintain changelog for releases