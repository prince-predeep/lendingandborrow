import mysql.connector
import hashlib
import csv
import datetime
from setup import get_database_name

PASSKEY_FILE = "passkeys.csv"

import datetime

def log_transaction(db_name, user_id, action, item_name, target_user_id=None):
    db_number = db_name.replace("lendborrow", "")  
    transactions_file = f"transactions{db_number}.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  

    # Create log message based on action
    if action == "Accepted":
        log_entry = f"[{timestamp}] User {user_id} accepted '{item_name}' request from User {target_user_id}\n"
    elif action == "Lent":
        log_entry = f"[{timestamp}] User {user_id} lent '{item_name}' to User {target_user_id}\n"
    elif action == "Cancelled":
        log_entry = f"[{timestamp}] User {user_id} cancelled request for '{item_name}'\n"
    elif action == "Deleted":
        log_entry = f"[{timestamp}] Admin removed borrow request for '{item_name}' from User {target_user_id}\n"
    else:
        log_entry = f"[{timestamp}] User {user_id} {action.lower()} '{item_name}'\n"

    # Append to transaction history file
    try:
        with open(transactions_file, "a") as file:
            file.write(log_entry)
    except Exception as e:
        print(f"Error writing to transaction log: {e}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_registration(connection):
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    hashed_password = hash_password(password)

    cursor = connection.cursor()
    cursor.execute("INSERT INTO user (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
    connection.commit()
    cursor.close()
    print("User registered successfully!")

def user_login(connection):
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    hashed_password = hash_password(password)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM user WHERE email = %s AND password = %s", (email, hashed_password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            user_id = user[0]  # Extract user_id
            print(f"Login successful! Your User ID is: {user_id}")
            return user_id  # Return user_id instead of just True
        else:
            print("Invalid email or password!")
            return None  # Return None if login fails

    except mysql.connector.Error as e:
        print(f"Error during login: {e}")
        return None

def admin_registration(connection):
    name = input("Enter admin name: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    hashed_password = hash_password(password)
    role = "admin"

    cursor = connection.cursor()
    cursor.execute("INSERT INTO admin (admin_name, email, password, role) VALUES (%s, %s, %s, %s)", (name, email, hashed_password, role))
    connection.commit()
    cursor.close()
    print("Admin registered successfully!")

def admin_login(connection):
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    hashed_password = hash_password(password)

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM admin WHERE email = %s AND password = %s", (email, hashed_password))
    admin = cursor.fetchone()
    cursor.close()

    if admin:
        print("Admin login successful!")
        return True
    else:
        print("Invalid email or password!")
        return False
    
def change_admin_passkey(db_name, connection):
    old_passkey = input("Enter the current passkey: ")

    # Read the passkey file and verify the old passkey
    rows = []
    passkey_found = False

    with open(PASSKEY_FILE, "r", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[1] == db_name:  # Match database name
                if row[0] == old_passkey:  # Verify old passkey
                    passkey_found = True
                    new_passkey = input("Enter new 4-letter passkey: ")
                    row[0] = new_passkey  # Update passkey
                else:
                    print("Error: Incorrect passkey!")
                    return  # Exit function on incorrect passkey
            rows.append(row)

    if not passkey_found:
        print("Error: Passkey verification failed!")
        return

    # Write updated data back to the CSV file
    with open(PASSKEY_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    print("Admin passkey updated successfully!")

def view_borrow_requests(db_name):
    db_number = db_name.replace("lendborrow", "")  # Extract the number from db_name
    borrow_file = f"borrow{db_number}.csv"
    
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            requests = list(reader)
            
            if not requests:
                print("No borrow requests found.")
                return
            
            print("\nBorrow Requests:")
            for request in requests:
                print(", ".join(request))
    except FileNotFoundError:
        print("No borrow requests found.")

def delete_borrow_request(db_name, connection):
    db_number = db_name.replace("lendborrow", "")
    borrow_file = f"borrow{db_number}.csv"
    
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            requests = list(reader)
            
            if not requests:
                print("No borrow requests to delete.")
                return
            
            print("\nBorrow Requests:")
            for i, request in enumerate(requests, start=1):
                print(f"{i}. {', '.join(request)}")
            
            borrow_id = int(input("Enter the Borrow ID to delete: "))
            if borrow_id < 1 or borrow_id > len(requests):
                print("Invalid Borrow ID.")
                return
            
            user_id = requests[borrow_id - 1][-1]  # Last column contains user_id
            item_name = requests[borrow_id - 1][1]  # Item name column
            del requests[borrow_id - 1]
            
            # Renumber remaining requests
            for i in range(len(requests)):
                requests[i][0] = str(i + 1)
            
            # Write updated requests back to file
            with open(borrow_file, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(requests)
            
            # Update user borrow status in database
            cursor = connection.cursor()
            cursor.execute("UPDATE user SET borrow_status = NULL WHERE user_id = %s", (user_id,))
            connection.commit()
            cursor.close()

            # Log the deletion BEFORE printing success message
            log_transaction(db_name, None, "Deleted", item_name, user_id)

            print("Borrow request deleted successfully and user borrow status updated.")
    
    except FileNotFoundError:
        print("No borrow requests found.")
    except Exception as e:
        print(f"Error: {e}")

def view_lended_items(db_name):
    db_number = db_name.replace("lendborrow", "")  # Extract the number from db_name
    lended_items_file = f"lended_items{db_number}.csv"
    
    try:
        with open(lended_items_file, "r", newline="") as file:
            reader = csv.reader(file)
            items = list(reader)
            
            if not items:
                print("No lended items found.")
                return
            
            print("\nLended Items:")
            for item in items:
                print(", ".join(item))
    except FileNotFoundError:
        print("No lended items found.")

def view_transaction_history(db_name):
    db_number = db_name.replace("lendborrow", "")  # Extract the number from db_name
    transactions_file = f"transactions{db_number}.csv"
    
    try:
        with open(transactions_file, "r", newline="") as file:
            reader = csv.reader(file)
            transactions = list(reader)
            
            if not transactions:
                print("No transactions found.")
                return
            
            print("\nTransaction History:")
            for transaction in transactions:
                print(", ".join(transaction))
    except FileNotFoundError:
        print("No transaction history found.")

def view_users_list(db_name, connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        cursor.close()
        
        if not users:
            print("No users found.")
            return
        
        print("\nUser List:")
        for user in users:
            print(user)  # Prints the full tuple directly
    
    except mysql.connector.Error as e:
        print(f"Error retrieving users: {e}")

def view_admins_list(db_name, connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM admin")
        admins = cursor.fetchall()
        cursor.close()
        
        if not admins:
            print("No users found.")
            return
        
        print("\nUser List:")
        for admin in admins:
            print(admin)  # Prints the full tuple directly
    
    except mysql.connector.Error as e:
        print(f"Error retrieving users: {e}")

def put_borrow_request(db_name, connection, user_id):
    db_number = db_name.replace("lendborrow", "")  
    borrow_file = f"borrow{db_number}.csv"

    item_name = input("Enter the item name: ")
    from_date = input("Enter the borrowing start date (YYYY-MM-DD): ")
    to_date = input("Enter the borrowing end date (YYYY-MM-DD): ")

    # Determine next Borrow ID
    next_borrow_id = 1  
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            borrow_requests = list(reader)
            if borrow_requests:
                last_id = int(borrow_requests[-1][0])
                next_borrow_id = last_id + 1  
    except FileNotFoundError:
        pass  

    # Update SQL user table
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE user 
            SET borrow_status = 'requested', borrowed_item = %s, date_start = %s, date_end = %s
            WHERE user_id = %s
        """, (item_name, from_date, to_date, user_id))
        connection.commit()
        cursor.close()
    except mysql.connector.Error as e:
        print(f"Error updating borrow status: {e}")
        return

    # Add borrow request to CSV
    try:
        with open(borrow_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([next_borrow_id, item_name, from_date, to_date, user_id])
        print("Borrow request submitted successfully!")

        # Log the transaction
        log_transaction(db_name, user_id, "requested", item_name)

    except Exception as e:
        print(f"Error writing to borrow file: {e}")

def accept_borrow_request(db_name, connection, lender_id):
    db_number = db_name.replace("lendborrow", "")  
    borrow_file = f"borrow{db_number}.csv"

    # Read and display existing borrow requests
    borrow_requests = []
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            borrow_requests = list(reader)

        if not borrow_requests:
            print("No borrow requests found.")
            return

        print("\nAvailable Borrow Requests:")
        for request in borrow_requests:
            print(f"ID: {request[0]}, Item: {request[1]}, From: {request[2]}, To: {request[3]}, User ID: {request[4]}")
        
    except FileNotFoundError:
        print("No borrow requests found.")
        return

    # Ask which request to accept
    try:
        accept_id = int(input("Enter the Borrow Request ID to accept: ")) - 1
        if accept_id < 0 or accept_id >= len(borrow_requests):
            print("Invalid selection.")
            return

        # Get the user ID and item from the request
        accepted_request = borrow_requests.pop(accept_id)
        borrower_id = accepted_request[4]
        borrowed_item = accepted_request[1]

        # Update SQL tables
        try:
            cursor = connection.cursor()
            
            # Update borrower status to 'received'
            cursor.execute("""
                UPDATE user 
                SET borrow_status = 'received'
                WHERE user_id = %s
            """, (borrower_id,))
            
            # Update lender status to 'accepted'
            cursor.execute("""
                UPDATE user 
                SET lend_status = 'accepted', lended_item = %s
                WHERE user_id = %s
            """, (borrowed_item, lender_id))

            connection.commit()
            cursor.close()
        except mysql.connector.Error as e:
            print(f"Error updating user statuses: {e}")
            return

        # Renumber borrow requests and update the CSV
        try:
            with open(borrow_file, "w", newline="") as file:
                writer = csv.writer(file)
                for index, request in enumerate(borrow_requests, start=1):
                    writer.writerow([index] + request[1:])  # Renumber IDs
            
            print("Borrow request accepted successfully!")

            # Log the transaction
            log_transaction(db_name, borrower_id, "Accepted", borrowed_item, lender_id)
            log_transaction(db_name, lender_id, "Lent", borrowed_item, borrower_id)

        except Exception as e:
            print(f"Error updating borrow file: {e}")
    
    except ValueError:
        print("Invalid input. Please enter a valid Borrow Request ID.")

def cancel_borrow_request(db_name, connection, user_id):  # Uses user_id directly
    db_number = db_name.replace("lendborrow", "")  
    borrow_file = f"borrow{db_number}.csv"

    # Read and display existing borrow requests
    borrow_requests = []
    user_requests = []
    
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            borrow_requests = list(reader)

        if not borrow_requests:
            print("No borrow requests found.")
            return

        # Filter borrow requests to show only those made by this user
        print("\nYour Borrow Requests:")
        for request in borrow_requests:
            if request[4] == str(user_id):  # Match user_id as string
                user_requests.append(request)
                print(f"ID: {request[0]}, Item: {request[1]}, From: {request[2]}, To: {request[3]}")

        if not user_requests:
            print("You have no active borrow requests.")
            return

    except FileNotFoundError:
        print("No borrow requests found.")
        return

    # Ask which request to cancel
    try:
        cancel_id = int(input("Enter the Borrow Request ID to cancel: ")) - 1
        if cancel_id < 0 or cancel_id >= len(borrow_requests):
            print("Invalid selection.")
            return

        # Remove the request and get borrower ID
        cancelled_request = borrow_requests.pop(cancel_id)

        # Reset borrow status in SQL for this user
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE user 
                SET borrow_status = NULL, borrowed_item = NULL, date_start = NULL, date_end = NULL
                WHERE user_id = %s
            """, (user_id,))
            connection.commit()
            cursor.close()
        except mysql.connector.Error as e:
            print(f"Error resetting borrow status: {e}")
            return

        # Log the cancellation BEFORE updating the borrow file
        log_transaction(db_name, user_id, "Cancelled", cancelled_request[1])

        # Renumber borrow requests and update the CSV
        try:
            with open(borrow_file, "w", newline="") as file:
                writer = csv.writer(file)
                for index, request in enumerate(borrow_requests, start=1):
                    writer.writerow([index] + request[1:])  # Renumber IDs
            
            print("Borrow request cancelled successfully!")

        except Exception as e:
            print(f"Error updating borrow file: {e}")
    
    except ValueError:
        print("Invalid input. Please enter a valid Borrow Request ID.")