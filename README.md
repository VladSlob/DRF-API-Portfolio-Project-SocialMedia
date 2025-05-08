# DRF-API-Portfolio-Project-SocialMedia (Vladyslav Slobodian)

RESTful API for a social media application. The API provides functionality for users to establish profiles, follow other accounts, generate and access posts, control likes and comments, and execute standard social media operations.

# Technologies to implement:
- Python, Django, Django, REST
- Docker
- Celery
- Redis

# How to run
- Clone project: git clone https://github.com/VladSlob/DRF-API-Portfolio-Project-SocialMedia
- go to project path: cd <project_directory>
- Create venv: python -m venv venv
- Activate it: venv\scripts\activate
- Build conteiner: docker compose build
- Run conteiners: docker compose up

# API Endpoints
- POST /api/register/: Register a new user
- POST /api/login/: Log in to get the authentication token
- POST /api/logout/: Log out and invalidate the token
- GET /api/profile/: List users profiles with optional filters (user id, username, first name, last name)
- GET /api/profile/{id}/: Retrieve a user profile by user id
- PUT /api/profile/{id}/: Update a user profile
- GET /api/post/: List all posts, with optional filters (by hashtags, author, content)
- POST /api/post/: Create a new post
- GET /api/post/{id}/: Retrieve a single post by ID
- PUT /api/post/{id}/: Update post
- EXTRA /api/post/{id}/upload_image/: add image to post
- EXTRA /api/post/{id}/like/: like / unlike post
- EXTRA /api/post/liked/: list posts that you likes
- DELETE /api/post/{id}/: Delete post
- POST /api/comment/: Add a comment to a post
- GET /api/comment/: List comments
- POST /api/comment/: Add a like to a post
- GET /api/comment/: List likes
- GET /api/following/: List of following
- GET /api/follow/: List of your follow
- POST /api/follow/: Create follow
- GET /api/follow/{id}/: Retrieve a single follow by ID
- DELETE GET /api/follow/{id}/: Unfollow

# Documentation
The API documentation is available through Swagger/OpenAPI and Redoc/OpenAPI interfaces, which can be accessed at the
- api/schema/swagger/
- api/schema/redoc/
