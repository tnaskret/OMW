import sys
import click
import sqlite3
import os

from omw.app import create_app
# Create an app context for the database connection.
app = create_app()

omw_db = os.path.realpath(
    os.path.join(os.getcwd(), 'db', app.config['OMW_DATABASE_FILE_NAME']))

admin_db = os.path.realpath(
    os.path.join(os.getcwd(), 'db', app.config['ADMIN_DATABASE_FILE_NAME']))


@click.group()
def cli():
    """ Run SqlLite related tasks to initialize database"""
    pass


@click.command()
def omwdb():
    """
    Creates empty omw database.

    :return: None
    """
    if os.path.isfile(omw_db):
        os.remove(omw_db)
        sys.stdout.write('Old database file (%s) removed \n' % omw_db)

    omw_connection = sqlite3.connect(omw_db)
    curs = omw_connection.cursor()

    sql_script = os.path.realpath(
        os.path.join(os.getcwd(), 'sql_scripts', 'omw.sql'))

    f = open(sql_script, 'r')
    curs.executescript(f.read())

    omw_connection.commit()
    omw_connection.close()

    sys.stdout.write('Omw database initialized\n')
    return None


@click.command()
def admindb():
    """
    Creates empty admin database.

    :return: None
    """

    if os.path.isfile(admin_db):
        os.remove(admin_db)
        sys.stdout.write('Old database file (%s) removed\n' % admin_db)

    omw_connection = sqlite3.connect(admin_db)
    curs = omw_connection.cursor()

    sql_script = os.path.realpath(
        os.path.join(os.getcwd(), 'sql_scripts', 'admin.sql'))

    f = open(sql_script, 'r')
    curs.executescript(f.read())

    omw_connection.commit()
    omw_connection.close()
    sys.stdout.write('Admin database initialized\n')
    return None


@click.command()
def seed():
    """
    Seed the database with an initial users.

    :return: User instance
    """
    u = "Initial seed"
    if os.path.isfile(admin_db):
        omw_connection = sqlite3.connect(admin_db)
        cursor = omw_connection.cursor()
        cursor.execute("""INSERT INTO users (userID, full_name, password, 
                 email, access_level, access_group, affiliation, u)
                 VALUES (?,?,?,?,?,?,?,?)""",
              ['admin', 'System Administrator',
               '1fc9b75701d72e2051441d23ee8acc20',
               'changeme@changeme.com', 99, 'admin', 'sys', u])

        cursor.execute("""INSERT INTO users (userID, full_name, password, 
                 email, access_level, access_group, affiliation, u)
                 VALUES (?,?,?,?,?,?,?,?)""",
              ['user1', 'System User 1',
               '46bcc2d7eb5723292133857fa95454b9',
               'changeme@changeme.com', 0, 'common', 'sys', u])
        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Admin database seeded with initial users\n')
    else:
        sys.stderr.write('Unable to load users\n')
    return None


@click.command()
@click.pass_context
def reset(ctx):
    """
    Init and seed automatically.

    :ctx: Context
    :return: None
    """
    ctx.invoke(omwdb)
    ctx.invoke(admindb)
    ctx.invoke(seed)

    return None


cli.add_command(omwdb)
cli.add_command(admindb)
cli.add_command(seed)
cli.add_command(reset)
