import sqlite3

# Opret database med KUN navne
conn = sqlite3.connect('navne_database.db')
cursor = conn.cursor()

# Opret KUN én simpel tabel
cursor.execute('''
CREATE TABLE IF NOT EXISTS navne (
    navn TEXT
)
''')

# Indsæt dine navne - INGEN ID, INGEN ekstra kolonner
navne_liste = ['Louise', 'David', 'Mads']

for navn in navne_liste:
    cursor.execute("INSERT INTO navne (navn) VALUES (?)", (navn,))

conn.commit()
conn.close()

print("Simpel database oprettet med navne:")
for navn in navne_liste:
    print(f" - {navn}")