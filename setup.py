import csv
import os
import random
import string
import mysql.connector

PASSKEY_FILE = "passkeys.csv"
DB_PREFIX = "lendborrow"
DEFAULT_ADMIN_PASS = "123123"

def generate_passkey():
    """Generates a unique 4-letter passkey."""
    while True:
        passkey = ''.join(random.choices(string.ascii_uppercase, k=4))
        if not passkey_exists(passkey):
            return passkey

def passkey_exists(passkey):
    """Checks if the passkey already exists in the CSV file."""
    if not os.path.exists(PASSKEY_FILE):
        return False
    with open(PASSKEY_FILE, "r", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == passkey:
                return True
    return False

def get_last_db_number():
    """Finds the last used database number from the passkey file."""
    if not os.path.exists(PASSKEY_FILE):
        return 0
    with open(PASSKEY_FILE, "r", newline="") as file:
        reader = csv.reader(file)
        db_numbers = [int(row[1].replace(DB_PREFIX, "")) for row in reader if row]
        return max(db_numbers, default=0)

def get_database_name(passkey):
    """Retrieves the database name associated with a passkey and returns a connection."""
    if not os.path.exists(PASSKEY_FILE):
        return None, None
    with open(PASSKEY_FILE, "r", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == passkey:
                db_name = row[1]
                connection = mysql.connector.connect(host="localhost", user="root", password="yourpassword", database=db_name)
                return db_name, connection
    return None, None

def create_new_database():
    """Creates a new database, user and admin tables, and tracking files."""
    passkey = generate_passkey()
    db_number = get_last_db_number() + 1
    db_name = f"{DB_PREFIX}{db_number}"
    
    # Save passkey, database name, and default admin password
    with open(PASSKEY_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([passkey, db_name, DEFAULT_ADMIN_PASS])
    
    # Create SQL database and tables
    connection = mysql.connector.connect(host="localhost", user="root", password="yourpassword")
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE {db_name}")
    cursor.execute(f"USE {db_name}")
    
    # Create user table
    cursor.execute("""
        CREATE TABLE user (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            lend_status ENUM('accepted', NULL) DEFAULT NULL,
            lended_item VARCHAR(255) DEFAULT NULL,
            borrow_status ENUM('requested', 'received', NULL) DEFAULT NULL,
            borrowed_item VARCHAR(255) DEFAULT NULL,
            date_start DATE DEFAULT NULL,
            date_end DATE DEFAULT NULL
        )
    """)
    
    # Create admin table
    cursor.execute("""
        CREATE TABLE admin (
            admin_id INT AUTO_INCREMENT PRIMARY KEY,
            admin_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL DEFAULT '123123'
        )
    """)
    
    connection.commit()
    cursor.close()
    connection.close()
    
    # Create tracking files for this database
    borrow_file = f"borrow{db_number}.csv"
    transactions_file = f"transactions{db_number}.txt"  # Changed to .txt
    lended_items_file = f"lended_items{db_number}.csv"
    
    for filename in [borrow_file, lended_items_file]:
        if not os.path.exists(filename):
            with open(filename, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Borrow ID", "Item", "From Date", "To Date", "User ID"])
    
    # Create an empty transaction log file
    if not os.path.exists(transactions_file):
        with open(transactions_file, "w") as file:
            file.write(f"Transaction Log for {db_name}\n")
            file.write("=" * 40 + "\n")

    print(f"New database created: {db_name} with passkey: {passkey} and default admin password: {DEFAULT_ADMIN_PASS}")
