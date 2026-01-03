# Song Master Web GUI - UI/UX Wireframes & Component Hierarchy

## Design System

### Color Palette
```css
/* Primary Colors */
--primary-50: #f0f9ff;
--primary-100: #e0f2fe;
--primary-500: #0ea5e9;
--primary-600: #0284c7;
--primary-700: #0369a1;

/* Neutral Colors */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;
--gray-400: #9ca3af;
--gray-500: #6b7280;
--gray-600: #4b5563;
--gray-700: #374151;
--gray-800: #1f2937;
--gray-900: #111827;

/* Accent Colors */
--success: #10b981;
--warning: #f59e0b;
--error: #ef4444;
--info: #3b82f6;
```

### Typography
```css
/* Font Families */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

### Spacing System
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
```

## Page Wireframes

### 1. Landing Page
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Song Master                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Generate Your Next Hit Song                   │   │
│  │                                                                     │   │
│  │  Transform your ideas into professional lyrics with AI-powered      │   │
│  │  songwriting assistance. Create songs in minutes, not hours.        │   │
│  │                                                                     │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │   Quick Start   │  │   View Albums │  │   Learn More    │     │   │
│  │  │                 │  │                 │  │                 │     │   │
│  │  │  Start creating │  │  Browse your    │  │  See how it     │     │   │
│  │  │  your first     │  │  existing       │  │  works          │     │   │
│  │  │  song now       │  │  songs          │  │                 │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           Recent Songs                               │   │
│  │                                                                     │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                │   │
│  │  │  Cover  │  │  Cover  │  │  Cover  │  │  Cover  │                │   │
│  │  │  Art    │  │  Art    │  │  Art    │  │  Art    │                │   │
│  │  │         │  │         │  │         │  │         │                │   │
│  │  │ Song 1  │  │ Song 2  │  │ Song 3  │  │ Song 4  │                │   │
│  │  │ 2 days  │  │ 1 week  │  │ 2 weeks │  │ 1 month │                │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          Features                                     │   │
│  │                                                                     │   │
│  │  🎵 AI-Powered Lyrics    🎨 Album Art Generation    📊 Progress     │   │
│  │     Generation              & Metadata              Tracking         │   │
│  │                                                                     │   │
│  │  🎭 Persona-Based Styles  ⚙️  Customizable Settings   📁 Album     │   │
│  │     & Themes               & Preferences            Management       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Song Generation Page
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard    Song Master    ⚙️ Settings    👤 Profile    [Logout] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Create New Song                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Song Description                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ Describe the song you want to create...                        │ │   │
│  │  │                                                                 │ │   │
│  │  │ Write about the theme, mood, genre, or any specific ideas      │ │   │
│  │  │ you have in mind.                                               │ │   │
│  │  │                                                                 │ │   │
│  │  │ Example: "A upbeat pop song about summer love with a retro     │ │   │
│  │  │ 80s vibe, featuring electric guitars and synthesizers"         │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  📎 Upload Prompt File (optional)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Song Details                                                       │   │
│  │                                                                     │   │
│  │  Song Title (optional)    ┌─────────────────────────────────────┐   │   │
│  │  ┌─────────────────────┐   │  Persona Selection                 │   │   │
│  │  │ My Awesome Song     │   │  ┌─────────────────────────────┐   │   │   │
│  │  └─────────────────────┘   │  │ 🔍 Search personas...        │   │   │   │
│  │                             │  └─────────────────────────────┘   │   │   │
│  │                             │                                     │   │   │
│  │                             │  ┌─────────────────────────────────┐ │   │   │
│  │                             │  │ 🎭 Antidote                    │ │   │   │
│  │                             │  │ 80s hair metal, glam rock...   │ │   │   │
│  │                             │  └─────────────────────────────────┘ │   │   │
│  │                             │                                     │   │   │
│  │                             │  ┌─────────────────────────────────┐ │   │   │
│  │                             │  │ 🎭 Bleached to Perfection      │ │   │   │
│  │                             │  │ Pop, Alternative Folk...        │ │   │   │
│  │                             │  └─────────────────────────────────┘ │   │   │
│  │                             └─────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  ⚙️ Advanced Settings                                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ ☑️ Use Local LLM (LM Studio)                                     │ │   │
│  │  │ Review Max Rounds: [3] Score Threshold: [8.0]                   │ │   │
│  │  │ Default Genre: [Rock ▼] Tempo: [120 BPM] Key: [C Major ▼]      │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    [Generate Song]                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. Generation Progress Page
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard    Song Master    ⚙️ Settings    👤 Profile    [Logout] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Generating Your Song                          │   │
│  │                                                                     │   │
│  │  "My Awesome Song" - Creating your AI-powered masterpiece...        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Progress Tracker                              │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ ████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ │   │
│  │  │                        65% Complete                             │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  Current Stage: Reviewing and refining lyrics                       │   │
│  │  Estimated time remaining: 2 minutes 30 seconds                     │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ ✅ Parsing user input and persona                               │ │   │
│  │  │ ✅ Loading resources (styles, tags, personas)                   │ │   │
│  │  │ ✅ Generating initial song draft                                │ │   │
│  │  │ 🔄 Reviewing and refining lyrics (Round 2 of 3)                │ │   │
│  │  │ ⏳ Applying critic feedback                                     │ │   │
│  │  │ ⏳ Running preflight checks                                     │ │   │
│  │  │ ⏳ Generating metadata summary                                  │ │   │
│  │  │ ⏳ Generating album artwork                                     │ │   │
│  │  │ ⏳ Formatting and saving final song                             │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Live Logs                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ 17:15:32 - Starting song generation process...                  │ │   │
│  │  │ 17:15:33 - Loaded persona: Antidote                             │ │   │
│  │  │ 17:15:35 - Generated initial draft (1,247 characters)           │ │   │
│  │  │ 17:15:38 - Review round 1: score 7.2/10                         │ │   │
│  │  │ 17:15:42 - Review round 2: score 8.1/10                         │ │   │
│  │  │ 17:15:45 - Applying critic feedback...                          │ │   │
│  │  │ 17:15:48 - Running preflight validation...                      │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    [Cancel Generation]                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. Song Results Page
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard    Song Master    ⚙️ Settings    👤 Profile    [Logout] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Your Song is Ready!                           │   │
│  │                                                                     │   │
│  │  ┌─────────────────┐  ┌─────────────────────────────────────────────┐ │   │
│  │  │                 │  │  My Awesome Song                           │ │   │
│  │  │   Album Cover   │  │                                             │ │   │
│  │  │                 │  │  A high-energy anthem about summer love    │ │   │
│  │  │   [Download]    │  │  with an 80s rock vibe.                    │ │   │
│  │  │   [Regenerate]  │  │                                             │ │   │
│  │  └─────────────────┘  │  🎵 Score: 8.1/10                          │ │   │
│  │                       │  🎭 Persona: Antidote                       │ │   │
│  │                       │  🎼 Genre: Rock                             │ │   │
│  │                       │  ⏱️  BPM: 120                               │ │   │
│  │                       │  🎹 Key: C Major                            │ │   │
│  │                       └─────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Song Lyrics                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ ## My Awesome Song                                              │ │   │
│  │  │                                                                 │ │   │
│  │  │ [Verse 1]                                                       │ │   │
│  │  │ [Male Vocal]                                                    │ │   │
│  │  │ Summer nights and neon lights                                   │ │   │
│  │  │ Dancing through the city streets                                │ │   │
│  │  │ Your smile shines brighter than the stars                       │ │   │
│  │  │ In this moment, nothing else competes                           │ │   │
│  │  │                                                                 │ │   │
│  │  │ [Chorus]                                                        │ │   │
│  │  │ [Male Vocal]                                                    │ │   │
│  │  │ This is our time, this is our song                              │ │   │
│  │  │ Together we're unbreakable, together we're strong               │ │   │
│  │  │ ...                                                             │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  [View Clean Lyrics] [Copy to Clipboard] [Edit Lyrics]              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Metadata & Details                            │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ **Suno Styles:** rock, 80s rock, arena rock, party anthem      │ │   │
│  │  │ **Target Audience:** Young adults, rock music fans             │ │   │
│  │  │ **Commercial Potential:** High - catchy hook, broad appeal     │ │   │
│  │  │ **Instruments:** Electric guitar, bass, drums, synthesizers    │ │   │
│  │  │ **Mood:** Uplifting, celebratory, energetic                    │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [Download Song] [Share] [Create Another] [Back to Dashboard]       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5. Dashboard/Albums Page
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard    Song Master    ⚙️ Settings    👤 Profile    [Logout] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Your Albums                                 │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ 🔍 Search songs...                    [+ New Album]           │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  Filter: [All ▼] [Sort: Date ▼] [View: Grid ▼]                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Recent Songs                                  │   │
│  │                                                                     │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │ Cover   │ │ Cover   │ │ Cover   │ │ Cover   │ │ Cover   │        │   │
│  │  │ Art     │ │ Art     │ │ Art     │ │ Art     │ │ Art     │        │   │
│  │  │         │ │         │ │         │ │         │ │         │        │   │
│  │  │ Summer  │ │ Midnight│ │ Electric│ │ Ocean   │ │ Dancing │        │   │
│  │  │ Dreams  │ │ Drive   │ │ Storm   │ │ Breeze  │ │ Queen   │        │   │
│  │  │         │ │         │ │         │ │         │ │         │        │   │
│  │  │ Score:  │ │ Score:  │ │ Score:  │ │ Score:  │ │ Score:  │        │   │
│  │  │ 8.1/10  │ │ 7.8/10  │ │ 9.2/10  │ │ 6.9/10  │ │ 8.5/10  │        │   │
│  │  │         │ │         │ │         │ │         │ │         │        │   │
│  │  │ 2 days  │ │ 1 week  │ │ 2 weeks │ │ 1 month │ │ 3 months│        │   │
│  │  │ ago     │ │ ago     │ │ ago     │ │ ago     │ │ ago     │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  │                                                                     │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │ Cover   │ │ Cover   │ │ Cover   │ │ Cover   │ │ [+]      │        │   │
│  │  │ Art     │ │ Art     │ │ Art     │ │ Art     │ │ New      │        │   │
│  │  │         │ │         │ │         │ │         │ │ Song     │        │   │
│  │  │ Rock &   │ │ Jazz    │ │ Pop     │ │ Classical│ │          │        │   │
│  │  │ Roll     │ │ Nights  │ │ Princess│ │ Symphony│ │          │        │   │
│  │  │         │ │         │ │         │ │         │ │          │        │   │
│  │  │ Score:  │ │ Score:  │ │ Score:  │ │ Score:  │ │          │        │   │
│  │  │ 7.5/10  │ │ 8.9/10  │ │ 7.2/10  │ │ 9.5/10  │ │          │        │   │
│  │  │         │ │         │ │         │ │         │ │          │        │   │
│  │  │ 6 months│ │ 8 months│ │ 1 year  │ │ 1 year  │ │          │        │   │
│  │  │ ago     │ │ ago     │ │ ago     │ │ ago     │ │          │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [Load More] [Export All] [Bulk Actions ▼]                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6. Settings Page
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard    Song Master    ⚙️ Settings    👤 Profile    [Logout] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Settings                                      │   │
│  │                                                                     │   │
│  │  ┌─────────────┐ ┌─────────────────────────────────────────────────┐ │   │
│  │  │             │ │                                                 │ │   │
│  │  │ LLM Config  │ │  API Configuration                              │ │   │
│  │  │             │ │                                                 │ │   │
│  │  │ Generation  │ │  Provider: [OpenAI ▼]                           │ │   │
│  │  │             │ │                                                 │ │   │
│  │  │ Personas    │ │  Model: [gpt-3.5-turbo ▼]                      │ │   │
│  │  │             │ │                                                 │ │   │
│  │  │ Styles      │ │  API Key: [••••••••••••••••••••••••] [Test]    │ │   │
│  │  │             │ │                                                 │ │   │
│  │  │ UI          │ │  Temperature: [0.1]                             │ │   │
│  │  │             │ │  Max Tokens: [4096]                             │ │   │
│  │  │             │ │                                                 │ │   │
│  │  │ About       │ │  ☑️ Use Local LLM (LM Studio)                   │ │   │
│  │  │             │ │  Local URL: [http://localhost:1234/v1]          │ │   │
│  │  │             │ │                                                 │ │   │
│  │  └─────────────┘ └─────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Generation Parameters                         │   │
│  │                                                                     │   │
│  │  Review Max Rounds: [3]    Score Threshold: [8.0]                   │   │
│  │                                                                     │   │
│  │  Default Song Parameters:                                            │   │
│  │  Genre: [Rock ▼]  Tempo: [120] BPM  Key: [C Major ▼]               │   │
│  │  Instruments: [guitar,bass,drums]                                    │   │
│  │  Mood: [happy ▼]                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        UI Preferences                                │   │
│  │                                                                     │   │
│  │  Theme: [Dark ▼]  Language: [English ▼]                             │   │
│  │  ☑️ Auto-save drafts  ☑️ Show progress notifications               │   │
│  │  ☑️ Play completion sound  ☑️ Compact view                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    [Save Settings] [Reset to Defaults]               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

### 1. Layout Components
```
App
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   ├── Navigation
│   │   ├── SearchBar
│   │   ├── UserMenu
│   │   └── Notifications
│   ├── Sidebar
│   │   ├── MainNav
│   │   ├── QuickActions
│   │   └── AlbumSwitcher
│   └── Footer
│       ├── Links
│       ├── Version
│       └── Status
```

### 2. Page Components
```
Pages
├── LandingPage
│   ├── HeroSection
│   ├── FeatureHighlights
│   ├── RecentSongs
│   └── CallToAction
├── DashboardPage
│   ├── AlbumGrid
│   ├── QuickActions
│   ├── RecentActivity
│   └── StatsOverview
├── GenerationPage
│   ├── InputForm
│   ├── PersonaSelector
│   ├── SettingsPanel
│   └── GenerationControls
├── ProgressPage
│   ├── ProgressTracker
│   ├── StageIndicator
│   ├── LiveLogs
│   └── CancelControls
├── ResultsPage
│   ├── SongViewer
│   ├── AlbumArt
│   ├── MetadataPanel
│   └── ExportOptions
└── SettingsPage
    ├── LLMSettings
    ├── GenerationSettings
    ├── UIPreferences
    └── AboutSection
```

### 3. Feature Components
```
Features
├── SongGeneration
│   ├── PromptInput
│   ├── FileUpload
│   ├── SongTitle
│   ├── PersonaSelector
│   ├── AdvancedSettings
│   └── GenerateButton
├── ProgressTracking
│   ├── ProgressBar
│   ├── StageIndicator
│   ├── TimeEstimator
│   ├── LogViewer
│   └── CancelButton
├── SongDisplay
│   ├── LyricsViewer
│   ├── MetadataDisplay
│   ├── AlbumArtViewer
│   ├── ScoreDisplay
│   └── CleanLyricsToggle
├── AlbumManagement
│   ├── AlbumGrid
│   ├── SongCard
│   ├── SearchFilter
│   ├── SortControls
│   └── BulkActions
└── Settings
    ├── LLMConfig
    ├── GenerationParams
    ├── UIPreferences
    └── SettingsForm
```

### 4. Shared Components
```
Shared
├── UI Components
│   ├── Button
│   ├── Input
│   ├── Select
│   ├── Textarea
│   ├── Modal
│   ├── Dropdown
│   ├── Tabs
│   ├── Accordion
│   ├── Alert
│   ├── Badge
│   ├── Card
│   ├── Avatar
│   ├── Progress
│   ├── Skeleton
│   └── Toast
├── Layout Components
│   ├── Container
│   ├── Grid
│   ├── Flex
│   ├── Stack
│   ├── Divider
│   └── Spacer
├── Media Components
│   ├── Image
│   ├── Video
│   ├── AudioPlayer
│   └── FileUpload
└── Data Components
    ├── DataTable
    ├── Pagination
    ├── Search
    ├── Filter
    └── Sort
```

## User Flow Diagrams

### 1. Song Generation Flow
```
User Input → Form Validation → Generation Start → Progress Tracking → Results Display
     ↓              ↓                ↓                ↓                ↓
  Prompt Text    Validate Data    CLI Execution    Real-time       Song Viewer
  Song Title     Check Persona    Background      Updates         Export Options
  Persona        Check Settings   Task            WebSocket       Share/Edit
  Settings       File Upload      Queue           Progress Bar    New Song
```

### 2. Album Management Flow
```
Dashboard → Album Selection → Song Library → Song Actions → Export/Share
    ↓            ↓                ↓              ↓              ↓
View All    Open Album      Browse Songs    View/Edit     Download
Albums    Create New        Search/Filter   Delete        Share Link
Stats       Manage Settings   Sort/Organize   Regenerate    Archive
```

## Responsive Design

### Breakpoints
```css
/* Mobile First Approach */
sm: 640px   /* Small tablets */
md: 768px   /* Tablets */
lg: 1024px  /* Small desktops */
xl: 1280px  /* Large desktops */
2xl: 1536px /* Extra large screens */
```

### Layout Adaptations

#### Mobile (< 768px)
- Single column layout
- Collapsible sidebar
- Touch-friendly buttons (44px minimum)
- Simplified navigation
- Stacked forms
- Swipe gestures for song cards

#### Tablet (768px - 1024px)
- Two-column layout where appropriate
- Condensed sidebar
- Larger touch targets
- Grid-based song display
- Modal dialogs for complex forms

#### Desktop (> 1024px)
- Multi-column layouts
- Persistent sidebar
- Hover states and tooltips
- Keyboard shortcuts
- Advanced filtering options
- Bulk operations

## Interaction Patterns

### 1. Loading States
- Skeleton screens for content loading
- Progress bars for long operations
- Spinners for quick actions
- Shimmer effects for images

### 2. Feedback Patterns
- Toast notifications for actions
- Inline validation messages
- Success/error states
- Confirmation dialogs for destructive actions

### 3. Navigation Patterns
- Breadcrumb navigation
- Back/forward buttons
- Tab navigation for related content
- Modal dialogs for complex workflows

### 4. Data Interaction
- Infinite scroll for large lists
- Search with debounced input
- Real-time updates via WebSocket
- Optimistic updates for better UX

## Accessibility Considerations

### 1. Keyboard Navigation
- Tab order optimization
- Focus indicators
- Keyboard shortcuts
- Skip links

### 2. Screen Reader Support
- Semantic HTML structure
- ARIA labels and descriptions
- Alt text for images
- Live regions for dynamic content

### 3. Visual Accessibility
- High contrast mode support
- Scalable fonts
- Color-blind friendly palette
- Reduced motion preferences

### 4. Motor Accessibility
- Large click targets (44px minimum)
- Generous spacing between interactive elements
- Drag and drop alternatives
- Voice control compatibility

This comprehensive wireframe and component hierarchy provides a detailed blueprint for implementing the Song Master Web GUI with a focus on user experience, accessibility, and maintainability.