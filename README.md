# Charade Chat

  ## Tech Stack
  1. React JS
  2. Node JS/Express JS
  3. SQLITE3
  

## Overview

  

We will be developing a web-based multiplayer game titled "Charade Chat". The game involves a room where players join, and they participate in rounds where one player, the "describer", explains words without stating them directly, while others guess the words as quickly as possible. The game leverages real-time communication and involves a competitive scoring system with a leaderboard.

  

## Objectives

  

### Game Setup and User Management

  

1. Implement user authentication using email/password (atleast) and Google OAuth (later) for a quick sign-in option. Ensure that user sessions are managed securely.

2. Room management should allow users to create a game room and invite others via a unique link or a room code. Rooms should support a configurable maximum number of participants.

3. The frontend will be developed using React JS, emphasizing a dynamic and responsive design to accommodate desktop and mobile browsers.

4. Each room supports multiple players, with one acting as a describer at a time.

5. Backend choices are Django or Node.js. Pick one based on your familiarity or the specific needs of the game mechanics.

  

### Game Mechanics

  

1. The game consists of timed rounds where the describer tries to explain as many words as possible without using the actual words. Set a default time limit of 60 seconds per round, adjustable in the room settings.

2. Words can be sourced from a predefined list categorized by difficulty levels. Optionally, integrate an external API for dynamic word generation.

3. Implement a "Skip" function for the describer, with a maximum of 3 skips per round to avoid excessive skipping.

4. Real-time communication for guess submissions should be facilitated through WebSockets, ensuring minimal latency.

5. Only the first guess will earn points to that guesser (the user who types in that guess and also the describer) after that the describer has to describe another word.

6. After the describer has exhausted their timer, it's the turn of another player to describe. And he/she becomes the guesser.

  
  

### Scoring and Leaderboard

  

1. Scoring should reward quick guesses, with only the first guess earning points.

2. The describer earns points equivalent to the average score of the correct guesses to incentivize clear and quick descriptions.

3. Implement a leaderboard that updates in real-time and is displayed at the end of each game, highlighting the top scorers and their respective points.

  
  

### Database Integration

  

1. Choose between SQL (starting with SQLite) or NoSQL (MongoDB) for data storage. Consider factors like data structure, scalability, and the complexity of queries.

2. The initial database schema should include tables/collections for Users, Rooms, Rounds, Words, and Scores, ensuring relationships are well-defined for efficient queries.

  

### Code Conventions and Best Practices

  

1. Adhere to code conventions for React, Django/Node, and the chosen database. Use ESLint for JavaScript and PEP 8 for Python, if using Django.

2. Use Git for version control with a clear branching strategy: feature branches for new features, a develop branch for integration testing, and a main branch for stable releases.

3. Encourage code reusability and modularity, especially for React components and backend services, to maintain a clean and manageable codebase.

  
  

### Testing and Documentation

  

1. Utilize Jest and React Testing Library for frontend unit and integration tests. For Django, leverage its built-in testing framework; for Node.js, use Mocha or Jest.

2. Document setup instructions and game mechanics in the README.md, employing markdown features for structured and engaging documentation.

3. Inline documentation and comments should be used judiciously within the code to explain complex logic or important decisions.

  
  

### Repo Guidelines

  
  

1. Project code should be inside a github repo and the frontend and backend code should be separated in separate folders within the same repo. (e.g., /frontend, /backend).

2. A detailed README.md with setup instructions, an overview of the project structure, and a guide to the game mechanics.

3. (Optional) Deploy a demo version of the game and include the link in your submission for a live preview can come later.
