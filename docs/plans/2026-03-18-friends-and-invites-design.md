# Friends & Game Invites - Design Document

## Problem

Signed-in players must manually share room codes every time they want to play with the same people. There's no way to maintain a social connection between sessions or invite friends directly from inside the app.

## Solution

Add a friends system for Google Sign-In users with mutual friend requests, online presence tracking, and in-app game invites. Room codes continue to work as the universal join method -- friends/invites are a convenience layer on top.

## Architecture

Three layers of new functionality:

### 1. Social Graph (Friendship)

- `Friendship` table: bidirectional relationship between two `User` records
- Status flow: `pending` -> `accepted` (or rejected/deleted)
- Only Google Sign-In users can participate (guests excluded)
- User A sends request -> User B accepts -> both appear in each other's friend list

### 2. Online Presence

- Track which signed-in users have an active socket connection
- New in-memory dict: `USER_TO_SIDS: Dict[int, Set[str]]` (user_id -> set of socket SIDs)
- Updated on socket connect/disconnect (global presence, not room-specific)
- `GET /friends` returns `is_online: true/false` for each friend
- Multi-tab/device support: user is online if any SID active
- Offline debounce: 30s delay before marking offline (prevents flicker on Android screen dim)

### 3. Game Invites

- `GameInvite` table: sender invites a friend to a specific room
- Delivered real-time via socket (`game:invite` event) if receiver is online
- Also queryable via `GET /notifications` (polling fallback)
- Expires after 5 minutes
- Clicking an invite auto-joins the room (same as `/join/:roomCode` flow)

## Data Model

### Friendship Table

```
Friendship
  id: int (PK)
  requester_id: int (FK -> users.id)  -- who sent the request
  addressee_id: int (FK -> users.id)  -- who received it
  status: str  -- "pending" | "accepted"
  created_at: datetime
  UNIQUE(requester_id, addressee_id)
```

### GameInvite Table

```
GameInvite
  id: int (PK)
  sender_id: int (FK -> users.id)
  receiver_id: int (FK -> users.id)
  room_code: str
  status: str  -- "pending" | "accepted" | "expired"
  created_at: datetime
  expires_at: datetime  -- created_at + 5 min
  INDEX(receiver_id, status)
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /friends/request | JWT | Send friend request. Body: `{user_id}` |
| GET | /friends | JWT | List accepted friends with online status |
| GET | /friends/requests | JWT | List pending incoming requests |
| POST | /friends/{user_id}/accept | JWT | Accept pending request |
| POST | /friends/{user_id}/reject | JWT | Reject or remove friend |
| POST | /rooms/{code}/invite | JWT | Invite friend to room. Body: `{user_id}` |
| GET | /notifications | JWT | Pending friend requests + game invites (badge count) |
| GET | /users/search?q=name | JWT | Search users by display name |

## Socket Events

| Event | Direction | Payload | Trigger |
|-------|-----------|---------|---------|
| friend:request | Server -> Client | `{from_user: {id, name, avatar}}` | Friend request received |
| friend:accepted | Server -> Client | `{user: {id, name, avatar}}` | Friend request accepted |
| game:invite | Server -> Client | `{from_user: {id, name}, room_code, game_type}` | Invited to a room |
| presence:connect | Client -> Server | `{token}` | App opens (register for presence) |

## UI Design (Mobile-First)

### Home Screen

- **NotificationBell** in TopBar (right side): red badge with count of pending requests + invites. Tap opens NotificationDrawer (bottom sheet) with game invite cards and friend request cards.
- **Friends Online** card (new, below Active Rooms): horizontal scroll of online friend avatars. Only shown for signed-in users with friends.

### Lobby Screen

- **Invite Friends** button in Room Code Hero section (alongside Copy/Share/Leave). Tap opens InviteFriendsDrawer (bottom sheet) showing online friends with [Invite] button, offline friends greyed out. Already-invited friends show "Invited" (disabled).

### New Pages/Components

| Component | Type | Description |
|-----------|------|-------------|
| NotificationBell | TopBar icon | Bell + red badge count |
| NotificationDrawer | Bottom sheet | Game invites + friend requests |
| InviteFriendsDrawer | Bottom sheet | Online/offline friends with invite |
| FriendsPage | Full page (/friends) | Manage: list, search, add, remove |
| UserSearchModal | Modal | Search by name, send request |
| FriendCard | Card | Avatar + name + online dot + action |

## Error Handling & Edge Cases

### Friend Requests
- Can't friend yourself -> 400
- Duplicate request -> idempotent (return existing)
- Can't friend a guest -> 400
- Rejected request -> can re-send later
- Block/report -> out of scope for v1

### Game Invites
- Full room -> 400 "Room is full"
- Room started -> still works (join lobby, wait)
- Expired (>5 min) -> "Invite expired" toast
- Already in room -> idempotent
- Room deleted -> "Room no longer available"

### Presence
- Multi-tab -> USER_TO_SIDS is a set, online if non-empty
- Android screen dim -> offline after 30s debounce
- Privacy: only friends see online status

### Notifications
- Poll GET /notifications every 30s on Home screen only
- Socket events for instant delivery when online
- Stop polling when leaving Home

## Testing Strategy

### Backend Tests
- test_friends.py: send, accept, reject, duplicate, self-friend, list, remove
- test_game_invites.py: send, accept, expire, full room, invalid room
- test_presence.py: online/offline, multi-tab, grace period
- test_notifications.py: badge count, combined requests + invites
- test_user_search.py: search, partial match, guest excluded

### Frontend Tests
- NotificationBell.test.jsx: badge count, zero state, click opens drawer
- FriendCard.test.jsx: online/offline dot, invite button states
- InviteFriendsDrawer.test.jsx: sections, invite click, already-invited

### E2E Tests (Playwright)
- friends-flow.spec.js: sign in -> search -> add -> accept -> verify list
- game-invite.spec.js: lobby -> invite friend -> notification -> join -> lobby

## Implementation Order

1. **Phase 1: Backend foundation** -- Friendship model, friend request/accept/reject/list APIs, user search
2. **Phase 2: Frontend friends** -- FriendsPage, UserSearchModal, friend request flow
3. **Phase 3: Presence** -- USER_TO_SIDS tracking, online status in GET /friends
4. **Phase 4: Game invites** -- GameInvite model, invite API, socket events
5. **Phase 5: Notifications** -- NotificationBell, NotificationDrawer, polling
6. **Phase 6: Lobby invite** -- InviteFriendsDrawer in lobby
7. **Phase 7: Tests** -- Backend + frontend + E2E tests

Each phase is independently deployable and testable.

## Research References

- Among Us friend system (mutual requests + lobby invite) -- closest model
- Jackbox/Gartic/Skribbl use room codes only (no social graph)
- Socket.IO presence tracking is a well-established pattern for real-time apps
