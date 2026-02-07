# Charade Chat UI Plan (Mobile-First)

## 1. Design Goals
- Neutral, modern, classy aesthetic with a clean, sophisticated feel.
- Mobile-first layouts with thumb-friendly interactions.
- Keep users engaged with tasteful motion, subtle ambient animation, and rewarding feedback.

## 2. Visual Direction
- **Typography**: Pair a refined serif for headings and a crisp sans for body/UI.
  - Selected: `"Playfair Display"` (headings) + `"Manrope"` (body/UI)
- **Color Palette** (neutral + single accent):
  - Background: soft off-white / warm gray
  - Surfaces: white with slight shadow and thin border
  - Text: charcoal / near-black
  - Accent: muted emerald
- **Shapes**: Rounded corners (10–16px), thin 1px borders, subtle elevation.
- **Background**: soft gradient wash + gentle grain/noise overlay.
- **Logo**: Minimal wordmark + symbol.

## 3. Motion & Engagement
- Page load: staggered fade-up of hero elements.
- Turn change: timer sweep + pulse ring.
- Correct guess: confetti burst + score pop.
- Lobby: player list pulse + live banner.
- Ambient: low-motion background drift and shimmer accents.

## 4. Screen Map & Layout (Implemented)

### 4.1 Welcome / Onboarding
- **Goal**: quick entry + tone.
- Elements:
  - Logo + tagline
  - CTAs: `Play as Guest`, `Sign In`
  - “How to play” link
- Motion: floating hero word card with shimmer.

### 4.2 Auth (Sign In / Register)
- Single card with tab switch.
- Inputs: email + password.
- CTA sticky near bottom on mobile.

### 4.3 Home (Create / Join)
- Create room card (rounds, difficulty, timer, max players).
- Join room card with room code input.
- “How to play” CTA and stats pills.

### 4.4 Lobby
- Room code with copy/share.
- Player list with join order.
- Host settings editable + save.
- **Waiting Room**: if `room.status === active`, banner shows “Game in progress” and players marked `Waiting for next game`.
- Start game CTA (host).

### 4.5 Game Screen
- Top: round + timer + describer chip.
- Middle: word panel (describer only; hidden otherwise).
- Bottom: chat log + input.
- Live score panel.
- **Reconnect**: banner + grace countdown + rejoin CTA.
- **Removal**: player removed banner.

### 4.6 Round End
- Scoreboard panel wired to live scores.

### 4.7 Game End
- Final leaderboard wired to live scores.

### 4.8 How to Play (Modal / Sheet)
- 3-step list with icons.

## 5. Components (Reusable)
- `PrimaryButton`, `GhostButton`
- `Card`, `StatPill`, `Badge`
- `TimerSweep`, `ConfettiBurst`
- `Scoreboard`, `Toast`

## 6. Responsive Rules
- Mobile-first single column.
- Desktop: two-column for Home & Lobby.
- Max width (1100px) for content.

## 7. UI States (Implemented)
- Loading / empty: placeholder text.
- Error states: toast banner.
- Reconnect banner with countdown.
- Waiting room banner.

## 8. Integration Notes
- See `docs/api.md` for socket + REST references.
- UI listens to `room:lobby_update`, `game:turn_start`, `game:new_word`, `game:correct_guess`, `game:round_end`, `game:game_end`, `game:reconnect_grace`, `game:player_removed`.

