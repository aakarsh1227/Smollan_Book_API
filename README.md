# Book Management API

A FastAPI-based application for managing a book collection with real-time updates via WebSockets.

## Features
- **CRUD Operations**: Combined Create/Update (Upsert) logic.
- **Real-time Notifications**: WebSockets notify all connected clients of data changes.
- **Data Persistence**: Stores data in a thread-safe JSON file.
- **Advanced Filtering**: Support for pagination, sorting, and filtering by author/genre.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `uvicorn main:app --reload`
3. Access API Docs: `http://127.0.0.1:8000/docs`
