import sqlite3
import os
import getpass

def add_entry(mem_conn,mem_cursor):
    username = input('Enter a username : ')
    if username == None:
        return

    password = ask_password()
    if password == None:
        return

    query = """INSERT INTO keepass (username,password) VALUES ('{}','{}')""".format(username,password)
    mem_cursor.execute(query)

    # Save (commit) the changes
    mem_conn.commit()

    return

def ask_password():
    password = getpass.getpass('Password : ')
    confirm_password = getpass.getpass('Confirm password : ')
    if password == confirm_password:
        return password
    else:
        return None

    

def close_file(mem_conn,mem_cursor,password,file_name):
    # Push data from RAM to the database file .db
    conn = sqlite3.connect('{}.db'.format(file_name))
    cursor = conn.cursor()

    query = """CREATE TABLE IF NOT EXISTS keepass (id integer PRIMARY KEY, username TEXT, password TEXT)"""

    # Try to execute the query a table
    try:
        cursor.execute(query)
        # Save (commit) the changes
        conn.commit()
    except Exception as e:
        print('Error:', e)
    
    query = """SELECT * FROM keepass"""

    try:
        mem_cursor.execute(query)
    except Exception as e:
        print('Error:', e)

    entries = []
    for row in mem_cursor:
        entries.append((row[0],row[1],row[2]))

    query = """INSERT OR REPLACE INTO keepass (id,username,password) VALUES (?,?,?)"""
    cursor.executemany(query, entries)

    conn.commit()
    conn.close()

    # Encrypt
    os.system('openssl enc -e -aes-256-cbc -iter 10 -in {}.db -out {}.db.enc -pass pass:{}'.format(file_name,file_name,password))
    os.system('rm {}.db'.format(file_name))
    return

def create_file():
    # Create a file
    file_name = input('Enter the file name (without extension): ')
    if file_name == '':
        return

    print('Enter a password to encrypt {}.db into {}.db.enc'.format(file_name,file_name))
    password = ask_password()
    if password == None:
        return

    conn = sqlite3.connect('{}.db'.format(file_name))
    cursor = conn.cursor()

    query = """CREATE TABLE IF NOT EXISTS keepass (id integer PRIMARY KEY, username TEXT, password TEXT)"""

    # Try to execute the query a table
    try:
        cursor.execute(query)
        # Save (commit) the changes
        conn.commit()

        # Close the connection with the DB
        conn.close()
    except Exception as e:
        print(e)

    # Encrypt the file
    try:
        os.system('openssl enc -e -aes-256-cbc -iter 10 -in {}.db -out {}.db.enc -pass pass:{}'.format(file_name,file_name,password))
        os.system('rm {}.db'.format(file_name)) # delete the .db file to keep only the encrypted file
    except Exception as e:
        print(e)

    return(password,file_name)

def del_entry(mem_conn,mem_cursor):
    show_entry(mem_cursor)

    id = input('Select the ID to delete an entry : ')
    
    query = """DELETE FROM keepass WHERE id={}""".format(int(id))
    mem_cursor.execute(query)

    # Save (commit) the changes
    mem_conn.commit()
    return


def display_menu():
    print('Enter help command to show all commands.\n')

def show_help():
    buffer = """
COMMANDS:
add     Add an entry (username/password) to RAM   
close   Push RAM's entries into the an encrypted file
create  Create an encrypted file
del     Del an entry from RAM
exit    Exit the program
help    Show help
open    Pull entries from encrypted file to RAM
show    Show RAM's entries
    """
    print(buffer)
    return

def open_file(mem_conn,mem_cursor):
    file_name = input('Enter the file name (without extension) : ')
    if file_name == '':
        return

    print('Enter a password to decrypt {}.db.enc '.format(file_name))
    password = getpass.getpass('Password : ')

    os.system('openssl enc -d -aes-256-cbc -iter 10 -in {}.db.enc -out {}.db -pass pass:{}'.format(file_name,file_name,password))

    conn = sqlite3.connect('{}.db'.format(file_name))
    cursor = conn.cursor()
    
    query = """SELECT * FROM keepass"""

    try:
        cursor.execute(query)
    except Exception as e:
        print('Error:', e)

    entries = []
    for row in cursor:
        entries.append((row[0],row[1],row[2]))

    query = """INSERT OR REPLACE INTO keepass (id,username,password) VALUES (?,?,?)"""
    mem_cursor.executemany(query, entries)
    mem_conn.commit()

    conn.commit()
    conn.close()

    os.system('rm {}.db'.format(file_name))

    return(mem_conn,mem_cursor,password,file_name)

def show_entry(mem_cursor):
    query = """SELECT * FROM keepass"""

    try:
        mem_cursor.execute(query)
    except Exception as e:
        print('Error:', e)

    buffer = str()
    for row in mem_cursor:
        buffer += '{} {} {}\n'.format(row[0], row[1], row[2])

    print(buffer)
    return

# Program begin here
if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.dirname(__file__))) # Redirect the path into the directory

    display_menu()

    # Init the local database in the RAM 
    mem_conn = sqlite3.connect(":memory:")
    mem_conn.isolation_level = None
    mem_cursor = mem_conn.cursor()

    query = """CREATE TABLE IF NOT EXISTS keepass (id integer PRIMARY KEY, username TEXT, password TEXT)"""

    try:
        mem_cursor.execute(query)
        mem_conn.commit() # Save (commit) the changes
    except Exception as e:
        print(e)

    password = str()

    # Interface
    while True:
        choice = '-1'
        while not(choice.split()) or choice.split()[0] not in ['add','close','create','del','exit','help','open','show']:
            try:
                choice = input('>')
            except Exception as e:
                print(e)
            if choice.split() and choice.split()[0] not in ['add','close','create','del','exit','help','open','show']:
                print('{}: command not found'.format(choice.split()[0]))

        # add
        if choice.split()[0] == 'add':
            add_entry(mem_conn,mem_cursor)

        # close
        elif choice.split()[0] == 'close':
            close_file(mem_conn,mem_cursor,password,file_name)

        # create
        elif choice.split()[0] == 'create':
            (password,file_name) = create_file()

        # del
        elif choice.split()[0] == 'del':
            del_entry(mem_conn,mem_cursor)

        # exit
        elif choice.split()[0] == 'exit':
            print('QUITTING')
            break

        # help
        elif choice.split()[0] == 'help':
            show_help()

        # open
        elif choice.split()[0] == 'open':
            (mem_conn,mem_cursor,password,file_name) = open_file(mem_conn,mem_cursor)

        # show
        elif choice.split()[0] == 'show':
            show_entry(mem_cursor)

    mem_conn.close()