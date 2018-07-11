import click

import sqlite3
import os

from omw.app import create_app, sys, dd
from warnings import warn

# Create an app context for the database connection.
app = create_app()

omw_db = os.path.realpath(
    os.path.join(os.getcwd(), 'db', app.config['OMW_DATABASE_FILE_NAME']))

admin_db = os.path.realpath(
    os.path.join(os.getcwd(), 'db', app.config['ADMIN_DATABASE_FILE_NAME']))


@click.group()
def cli():
    """ Run SqlLite related tasks tu update database """
    pass


@click.command()
def freq():
    """
    Updates frequency

    :return: None
    """
    if os.path.isfile(omw_db):

        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        sfreq = dd(int)

        cursor.execute("""SELECT s_id, x3 FROM sxl WHERE x1='freq'""")
        for (s_id, count) in cursor:
            sfreq[s_id] += int(count)

        smt_id = None
        uname = 'update freq'
        cursor.execute("""SELECT id FROM smt WHERE tag='freq'""")
        r = cursor.fetchone()
        if r:
            smt_id = r[0]
        else:
            cursor.execute("""INSERT INTO smt(tag, name, u) VALUES (?,?,?)""",
                           ('freq', 'frequency', uname))
            smt_id = cursor.lastrowid

        update = {}
        delete = set()
        cursor.execute("""SELECT s_id,  sml_id  FROM sm WHERE smt_id =?""", (smt_id,))
        for (s_id, sml_id) in cursor:
            if s_id in sfreq:
                if sml_id != sfreq[s_id]:  # new value for frequency
                    update[s_id] = sml_id
                del sfreq[s_id]  # either it is unchanged or we update it
            else:
                warn("No frequency for {} (was {})".format(s_id, sml_id))
                delete.add(s_id)

        # anything left in sfreq must be added
        # print (smt_id)
        cursor.executemany("""
        INSERT OR REPLACE 
        INTO sm (s_id, smt_id, sml_id, u)
        VALUES (?, ?, ?, ?)""",
                           [(s_id, smt_id, count, uname)
                            for (s_id, count) in sfreq.items() if count > 0])

        # update changed values
        cursor.executemany("""
        UPDATE sm SET sml_id=? 
        WHERE s_id = ? AND smt_id=?""",
                           [(count, s_id, smt_id)
                            for (s_id, count) in update.items() if count > 0])

        # delete zero frequency
        cursor.execute("""DELETE FROM sm WHERE s_id in (%s)"""
                       % ",".join('?' for s_id in delete), list(delete))

        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Updating freq finished\n')

    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)
    return None


@click.command()
def label():
    """
    Creates empty admin database.

    :return: None
    """

    if os.path.isfile(omw_db):

        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        sfreq = dd(int)
        cursor.execute("""SELECT id FROM smt WHERE tag='freq'""")
        r = cursor.fetchone()
        # print (r[0])
        if r:
            cursor.execute("""SELECT s_id, sml_id FROM sm WHERE smt_id=?""", str(r[0]))
            for s_id, sml_id in cursor:
                sfreq[s_id] = sml_id

        # get the senses (from sm)
        cursor.execute("""
        SELECT s_id, ss_id, lemma, lang_id
          FROM (SELECT w_id, canon, ss_id, s_id 
            FROM (SELECT id as s_id, ss_id, w_id FROM s) 
                 JOIN w ON w_id = w.id ) 
           JOIN f ON canon = f.id
        """)

        senses = dd(lambda: dd(list))
        # senses[ss_id][lang_id]=[(ls_id, lemma, freq), ...]
        forms = dd(lambda: dd(int))
        # forms[lang][word] = freq

        langs = set()
        eng_id = 1  ### we know this :-)
        for (s_id, ss_id, lemma, lang_id) in cursor:
            senses[ss_id][lang_id].append((s_id, lemma, sfreq[s_id]))
            forms[lang_id][lemma] += 1
            langs.add(lang_id)
            # print  (s_id, ss_id, lemma, lang_id)

        # sort the things
        # prefer frequent sense; infrequent form; short; alphabetical
        for ss in senses:
            for l in senses[ss]:
                senses[ss][l].sort(key=lambda x: (-x[2],  # sense freq (freq is good)
                                                  forms[l][x[1]],  # uniqueness (freq is bad)
                                                  len(x[1]),  # length (short is good)
                                                  x[1]))  # lemma (so it is the same)

        _label = dd(lambda: dd(str))

        lgs = sorted(langs)

        values = list()
        for ss in senses:
            for l in lgs:
                if senses[ss][l]:
                    _label[ss][l] = senses[ss][l][0][1]
                else:
                    for lx in lgs:  # start with eng and go through till you find one
                        # print ("Looking elsewhere", ss, l, lx,senses[ss][lx])
                        if senses[ss][lx]:
                            _label[ss][l] = senses[ss][lx][0][1]
                            break
                    else:
                        _label[ss][l] = "?????"
                values.append((ss, l, _label[ss][l]))

        # write the labels (delete old ones first)
        cursor.execute("""DELETE FROM label""")
        cursor.executemany("""INSERT INTO label(ss_id, lang_id, label, u) 
        VALUES (?,?,?,"omw")""", values)

        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Updating labels finished\n')

    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)
    return None


@click.command()
@click.pass_context
def update_all(ctx):
    """
    Runs all updates.

    :ctx: Context
    :return: None
    """
    ctx.invoke(freq)
    ctx.invoke(label)

    return None


cli.add_command(freq)
cli.add_command(label)
cli.add_command(update_all)
