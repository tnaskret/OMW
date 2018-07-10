import sqlite3

dbfile = "omw.db"
con = sqlite3.connect(dbfile)
curs = con.cursor()

f = open('omw.sql', 'r')
curs.executescript(f.read())

con.commit()
con.close()
