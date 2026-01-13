# Persona Editing Feature Implementation Plan

## Overview
Add a new "Personas" navigation option alongside the existing "Albums" button in the header. This will open a dedicated page for viewing, creating, and editing personas with an intuitive GUI interface.

## Current State Analysis

### Existing Persona Structure
Personas are stored as markdown files in `personas/` directory with the following format:
```markdown
# Suno Persona Name
[Persona Name]

## Persona styles
[comma-separated style tags]

## Visual styles
[visual description for album art]
```

### Existing Backend API
- `GET /api/personas` - Returns list of personas (name, description, styles)
- Persona schema: `{ name: string, description?: string, styles?: string }`

### Existing Frontend Structure
- Header navigation in [`Header.tsx`](frontend/src/components/layout/Header.tsx:3-8)
- Page routing in [`App.tsx`](frontend/src/App.tsx:13-19)
- API service functions in [`api.ts`](frontend/src/services/api.ts:12-15)
- Type definitions in [`api.ts`](frontend/src/types/api.ts:1-5)

---

## Implementation Plan

### Phase 1: Backend API Extensions

#### 1.1 Add Persona CRUD Endpoints
Create new endpoints in [`backend/app/api/routes/personas.py`](backend/app/api/routes/personas.py):

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/personas` | List all personas (existing) |
| `GET` | `/api/personas/{name}` | Get single persona with full content |
| `POST` | `/api/personas` | Create new persona |
| `PUT` | `/api/personas/{name}` | Update existing persona |
| `DELETE` | `/api/personas/{name}` | Delete persona |

#### 1.2 Update Persona Service
Extend [`backend/app/services/persona_service.py`](backend/app/services/persona_service.py) with:

```python
def get_persona(name: str) -> Optional[Persona]:
    """Get a single persona with all fields."""

def create_persona(persona: PersonaCreate) -> Persona:
    """Create a new persona markdown file."""

def update_persona(name: str, persona: PersonaUpdate) -> Persona:
    """Update an existing persona file."""

def delete_persona(name: str) -> bool:
    """Delete a persona file."""
```

#### 1.3 Add New Schema
Update [`backend/app/schemas/personas.py`](backend/app/schemas/personas.py):

```python
class PersonaCreate(BaseModel):
    name: str
    styles: str
    visual_styles: Optional[str] = None

class PersonaUpdate(BaseModel):
    styles: Optional[str] = None
    visual_styles: Optional[str] = None
```

---

### Phase 2: Frontend API Service Extensions

#### 2.1 Add API Functions
Update [`frontend/src/services/api.ts`](frontend/src/services/api.ts):

```typescript
export async function fetchPersona(name: string): Promise<PersonaDetail>

export async function createPersona(payload: {
  name: string;
  styles: string;
  visual_styles?: string;
}): Promise<Persona>

export async function updatePersona(
  name: string,
  payload: Partial<{ styles: string; visual_styles: string }>
): Promise<Persona>

export async function deletePersona(name: string): Promise<void>
```

#### 2.2 Update Type Definitions
Update [`frontend/src/types/api.ts`](frontend/src/types/api.ts):

```typescript
export type PersonaDetail = {
  name: string;
  styles: string;
  visual_styles?: string;
  file_path: string;
}
```

---

### Phase 3: Frontend UI Components

#### 3.1 Add Navigation Link
Update [`frontend/src/components/layout/Header.tsx`](frontend/src/components/layout/Header.tsx:3-8):

```typescript
const nav = [
  { path: "/", label: "Home" },
  { path: "/personas", label: "Personas" },  // NEW
  { path: "/dashboard", label: "Albums" },
  { path: "/generate", label: "Generate" },
  { path: "/settings", label: "Settings" }
];
```

#### 3.2 Add Route
Update [`frontend/src/App.tsx`](frontend/src/App.tsx:13-19):

```typescript
import { PersonasPage } from "./pages/PersonasPage";

// Add route:
<Route path="/personas" element={<PersonasPage />} />
```

#### 3.3 Create PersonasPage
Create [`frontend/src/pages/PersonasPage.tsx`](frontend/src/pages/PersonasPage.tsx) with:

- **Persona List View**: Grid/card view of existing personas with edit/delete buttons
- **Create New Persona**: Button to add a new persona
- **Edit Persona Form**: Modal or inline form with fields:
  - Name (text input, disabled for existing personas)
  - Persona Styles (textarea, comma-separated tags)
  - Visual Styles (textarea, description for album art)
- **Delete Confirmation**: Modal when deleting a persona

#### 3.4 Create PersonaForm Component
Create [`frontend/src/components/persona/PersonaForm.tsx`](frontend/src/components/persona/PersonaForm.tsx) as a reusable form component for creating/editing personas.

---

### Phase 4: Persona File Format

#### 4.1 Standard Persona Template
All personas will follow this format:

```markdown
# Suno Persona Name
[Name]

## Persona styles
[style1, style2, style3, ...]

## Visual styles
[Visual description for album art generation]
```

#### 4.2 File Naming
- Filename: `personas/{name_lower_snake_case}.md`
- Example: "Anagram" → `personas/anagram.md`

---

## UI Mockup

```
┌─────────────────────────────────────────────────────────────┐
│  Song Master                    Home | Personas | Albums... │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ Personas ───────────────────────────────────────────┐  │
│  │  ┌─ Create New Persona ──────────────────────────┐   │  │
│  │  │ [ + New Persona ]                             │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │                                                             │
│  │  ┌─ Existing Personas ──────────────────────────────┐   │  │
│  │  │ ┌─────────┐ ┌─────────┐ ┌─────────┐              │   │  │
│  │  │ │ Anagram │ │ Antidote│ │ ...     │              │   │  │
│  │  │ │ [Edit]  │ │ [Edit]  │ │ [Edit]  │              │   │  │
│  │  │ └─────────┘ └─────────┘ └─────────┘              │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  │                                                             │
│  │  ┌─ Edit Persona Modal ──────────────────────────────┐   │  │
│  │  │ Name: [ Anagram        ]                          │   │  │
│  │  │ Styles: [ alt pop rock, modern rock, stadium... ] │   │  │
│  │  │ Visual:  [ 1950s style, fallout boy look...    ]  │   │  │
│  │  │ [ Cancel ] [ Save Changes ] [ Delete ]           │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Order

1. **Backend API** - Add CRUD endpoints and service functions
2. **Frontend API** - Add service functions and types
3. **Navigation** - Add "Personas" link to header
4. **Routing** - Add route for personas page
5. **PersonasPage** - Create main page with list view
6. **PersonaForm** - Create form component for create/edit
7. **Testing** - Verify all CRUD operations work

---

## Files to Create/Modify

### New Files
- `frontend/src/pages/PersonasPage.tsx`
- `frontend/src/components/persona/PersonaForm.tsx`

### Modified Files
- `backend/app/api/routes/personas.py`
- `backend/app/services/persona_service.py`
- `backend/app/schemas/personas.py`
- `frontend/src/services/api.ts`
- `frontend/src/types/api.ts`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/App.tsx`
