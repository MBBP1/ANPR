from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI(title="Navne API")

# Tillad CORS for Raspberry Pi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Velkommen til Navne API"}

@app.get("/api/navne", response_model=dict)
def hent_navne():
    """Hent alle navne fra databasen"""
    try:
        # Opret en simpel test-database hvis den ikke findes
        conn = sqlite3.connect('navne_database.db')
        cursor = conn.cursor()
        
        # Opret tabel hvis den ikke findes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS navne_tabel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            navn TEXT NOT NULL
        )
        ''')
        
        # Tjek om der er data, ellers indsæt testdata
        cursor.execute("SELECT COUNT(*) FROM navne_tabel")
        count = cursor.fetchone()[0]
        
        if count == 0:
            test_navne = ['Anna', 'Bo', 'Clara', 'David', 'Eva', 'Frank']
            for navn in test_navne:
                cursor.execute("INSERT INTO navne_tabel (navn) VALUES (?)", (navn,))
            conn.commit()
            print("Test data indsat!")
        
        # Hent alle navne
        cursor.execute("SELECT navn FROM navne_tabel")
        navne = cursor.fetchall()
        conn.close()
        
        navne_liste = [navn[0] for navn in navne]
        return {"navne": navne_liste, "antal": len(navne_liste)}
    
    except Exception as e:
        return {"error": f"Database fejl: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)