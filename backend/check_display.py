import sqlite3

conn=sqlite3.connect('ships.db')
conn.row_factory=sqlite3.Row
cur=conn.cursor()
cur.execute("SELECT display_name_raw, name FROM ships WHERE display_name_raw IS NOT NULL LIMIT 5")
rows=cur.fetchall()
print('rows with display_name_raw:', len(rows))
for r in rows:
    print(r['name'], '->', (r['display_name_raw'] or '')[:80])
conn.close()
