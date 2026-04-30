import json
import threading
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, validator

app = FastAPI()

DB_FILE = "books.json"
file_lock = threading.Lock()
active_connections: List[WebSocket] = []

class Book(BaseModel):
    id: Optional[int] = None
    title: str
    author: str
    publication_year: int
    genre: str
    isbn: str

    @validator("publication_year")
    def validate_year(cls, v):
        current_year = datetime.now().year
        if not (1450 <= v <= current_year):
            raise ValueError(f"Year must be between 1450 and {current_year}")
        return v

def read_db() -> List[dict]:
    with file_lock:
        with open(DB_FILE, "r") as f:
            return json.load(f)

def write_db(data: List[dict]):
    with file_lock:
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)

async def notify_clients(message: dict):
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            active_connections.remove(connection)

@app.get("/books")
def get_books(
    author: Optional[str] = None,
    genre: Optional[str] = None,
    sort_by: Optional[str] = Query(None, pattern="^(title|author|publication_year)$"),
    page: int = 1,
    size: int = 5
):
    books = read_db()
    if author:
        books = [b for b in books if author.lower() in b['author'].lower()]
    if genre:
        books = [b for b in books if genre.lower() in b['genre'].lower()]
    
    if sort_by:
        books.sort(key=lambda x: x.get(sort_by, ""))

    start = (page - 1) * size
    end = start + size
    return books[start:end]

@app.post("/books/upsert")
async def upsert_book(book: Book):
    books = read_db()
    existing_book = None
    
    for b in books:
        if b['isbn'] == book.isbn or (
            b['title'] == book.title and 
            b['author'] == book.author and 
            b['publication_year'] == book.publication_year
        ):
            existing_book = b
            break

    if existing_book:
        index = books.index(existing_book)
        updated_data = book.dict()
        updated_data['id'] = existing_book['id']
        books[index] = updated_data
        action = "updated"
    else:
        new_id = max([b['id'] for b in books]) + 1 if books else 1
        updated_data = book.dict()
        updated_data['id'] = new_id
        books.append(updated_data)
        action = "created"

    write_db(books)
    await notify_clients({"action": action, "book": updated_data})
    return {"status": "success", "action": action, "data": updated_data}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
