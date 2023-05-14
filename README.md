# dating-app

## Project Proposal

My dating app, called MatchMeet, aims to connect individuals based on their interests and preferences. Users will be able to create a profile, browse potential matches, and message each other through the app.

## Technologies Required

Flask as backend
Jinja as template engine

## Data Model

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  email TEXT NOT NULL
);

CREATE TABLE user_profile (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  photo TEXT NOT NULL,
  description TEXT,
  interests TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id_1 INTEGER NOT NULL,
    user_id_2 INTEGER NOT NULL,
    match_time DATETIME NOT NULL,
    FOREIGN KEY (user_id_1) REFERENCES users(id),
    FOREIGN KEY (user_id_2) REFERENCES users(id)
);

CREATE TABLE likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id_1 INTEGER NOT NULL,
    user_id_2 INTEGER NOT NULL,
    like_time DATETIME NOT NULL,
    FOREIGN KEY (user_id_1) REFERENCES users(id),
    FOREIGN KEY (user_id_2) REFERENCES users(id)
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    send_time DATETIME NOT NULL,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);
```

## Roadmap

### MVP

- User authentication and profile creation
- Matching system

### 2.0

- In-app messaging
- Advanced filtering options

### Nice-to-haves

- Integration with social media accounts
- Location-based matching
- User verification system

## Notes

I believe that there is a significant market for a dating app that prioritizes user interests and preferences over superficial factors. I plan to differentiate ourselves from other dating apps by offering advanced filtering options and a location-based matching system. Additionally, I will prioritize user privacy and safety by implementing a user verification system and ensuring that all communication takes place within the app.
