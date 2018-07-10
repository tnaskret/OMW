import sqlite3


dbfile = "admin.db"
con = sqlite3.connect(dbfile)
curs = con.cursor()

f = open('admin.sql', 'r')
curs.executescript(f.read())

con.commit()
con.close()
