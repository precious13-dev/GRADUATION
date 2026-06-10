import sqlite3
db = sqlite3.connect('gpms.db')
c = db.execute("SELECT email FROM users WHERE name='BEN PHIRI'")
print(c.fetchone()[0])
