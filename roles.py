import mysql.connector
import hashlib
import csv
import datetime
from setup import get_database_name
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table
import getpass

console = Console()
PASSKEY_FILE = "passkeys.csv"

def log_transaction(db_name, user_id, action, item_name, target_user_id=None):
    db_number = db_name.replace("lendborrow", "")  
    transactions_file = f"transactions{db_number}.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  

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

    try:
        with open(transactions_file, "a") as file:
            file.write(log_entry)
    except Exception as e:
        console.print(f"[red]Error writing to transaction log: {e}[/red]")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_registration(connection):
    name = Prompt.ask("[cyan]Enter your name[/cyan]")
    email = Prompt.ask("[cyan]Enter your email[/cyan]")
    password = input("Enter your password: ")
    hashed_password = hash_password(password)

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO user (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        connection.commit()
        cursor.close()
        console.print("[green]User registered successfully![/green]")
    except mysql.connector.Error as e:
        console.print(f"[red]Error during registration: {e}[/red]")

def user_login(connection):
    email = Prompt.ask("[cyan]Enter your email[/cyan]")
    password = input("Enter your password: ")
    hashed_password = hash_password(password)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM user WHERE email = %s AND password = %s", (email, hashed_password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            user_id = user[0]
            console.print(f"[green]Login successful! Your User ID is: {user_id}[/green]")
            return user_id
        else:
            console.print("[red]Invalid email or password![/red]")
            return None

    except mysql.connector.Error as e:
        console.print(f"[red]Error during login: {e}[/red]")
        return None

def admin_registration(db_name, connection):
    with open(PASSKEY_FILE, "r", newline="") as file:
        password = input("Enter current admin passkey : ")
        reader = csv.reader(file)
        for row in reader:
            if row[1] == db_name:
                if row[2] == password:
                    console.print("[green]Access Granted[/green]")
                else:
                    console.print("[red]Password is incorrect[/red]")
                    return
    name = Prompt.ask("[cyan]Enter admin name[/cyan]")
    email = Prompt.ask("[cyan]Enter admin email[/cyan]")
    password = input("Enter current admin password: ")
    hashed_password = hash_password(password)

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO admin (admin_name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        connection.commit()
        cursor.close()
        console.print("[green]Admin registered successfully![/green]")
    except mysql.connector.Error as e:
        console.print(f"[red]Error during admin registration: {e}[/red]")

def admin_login(connection):
    email = Prompt.ask("[cyan]Enter admin email[/cyan]")
    password = input("Enter current admin password: ")
    hashed_password = hash_password(password)

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM admin WHERE email = %s AND password = %s", (email, hashed_password))
    admin = cursor.fetchone()
    cursor.close()

    if admin:
        console.print("[green]Admin login successful![/green]")
        return True
    else:
        console.print("[red]Invalid email or password![/red]")
        return False

def change_admin_passkey(db_name, connection):
    old_passkey = input("Enter current passkey : ")


    rows = []
    passkey_found = False

    with open(PASSKEY_FILE, "r", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[1] == db_name:
                if row[2] == old_passkey:
                    passkey_found = True
                    new_passkey = input("Enter new passkey : ")

                    row[2] = new_passkey
                else:
                    console.print("[red]Error: Incorrect passkey![/red]")
                    return
            rows.append(row)

    if not passkey_found:
        console.print("[red]Error: Passkey verification failed![/red]")
        return

    with open(PASSKEY_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    console.print("[green]Admin passkey updated successfully![/green]")

def view_borrow_requests(db_name, connection):
    db_number = db_name.replace("lendborrow", "")  
    borrow_file = f"borrow{db_number}.csv"
    
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            requests = list(reader)

            if not requests or len(requests) <= 1:  # If only header exists, no requests
                console.print("[yellow]No borrow requests found.[/yellow]")
                return

            # Remove header before displaying
            if requests[0][0].lower() == "borrow id":
                requests = requests[1:]

            table = Table(title="Borrow Requests", show_lines=True)
            table.add_column("ID", justify="center", style="cyan")
            table.add_column("Item", style="bold")
            table.add_column("From Date", justify="center")
            table.add_column("To Date", justify="center")
            table.add_column("User ID", justify="center", style="magenta")
            
            for request in requests:
                table.add_row(*request)
            
            console.print(table)
    except FileNotFoundError:
        console.print("[yellow]No borrow requests found.[/yellow]")

def delete_borrow_request(db_name, connection):
    db_number = db_name.replace("lendborrow", "")
    borrow_file = f"borrow{db_number}.csv"
    
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            requests = list(reader)
            
            if len(requests) <= 1:  # Only header exists, no borrow requests
                console.print("[yellow]No borrow requests to delete.[/yellow]")
                return
            
            header = requests[0]  # Store header separately
            borrow_requests = requests[1:]  # Exclude header from processing
            
            table = Table(title="Borrow Requests", show_lines=True)
            table.add_column("Index", justify="center", style="cyan")
            table.add_column("Item", style="bold")
            table.add_column("From Date", justify="center")
            table.add_column("To Date", justify="center")
            table.add_column("User ID", justify="center", style="magenta")
            
            for i, request in enumerate(borrow_requests, start=1):
                table.add_row(str(i), *request[1:])  
            
            console.print(table)
            
            borrow_id = Prompt.ask("[cyan]Enter the Borrow ID to delete[/cyan]", default="0")
            borrow_id = int(borrow_id)
            if borrow_id < 1 or borrow_id > len(borrow_requests):
                console.print("[red]Invalid Borrow ID.[/red]")
                return
            
            user_id = borrow_requests[borrow_id - 1][-1]  # Last column contains user_id
            item_name = borrow_requests[borrow_id - 1][1]  # Item name column
            
            del borrow_requests[borrow_id - 1]  # Remove the selected request
            
            # Renumber remaining requests
            for i, request in enumerate(borrow_requests, start=1):
                request[0] = str(i)  
            
            # Write updated requests back to file
            with open(borrow_file, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Borrow ID", "Item", "From Date", "To Date", "User ID"])  # Keep header
                for i, request in enumerate(borrow_requests, start=1):
                    writer.writerow([i] + request[1:])  # Ensure IDs remain sequential
            
            # Update user borrow status in database
            cursor = connection.cursor()
            cursor.execute("UPDATE user SET borrow_status = NULL WHERE user_id = %s", (user_id,))
            connection.commit()
            cursor.close()

            log_transaction(db_name, None, "Deleted", item_name, user_id)

            console.print("[green]Borrow request deleted successfully and user borrow status updated.[/green]")
    
    except FileNotFoundError:
        console.print("[yellow]No borrow requests found.[/yellow]")
    except ValueError:
        console.print("[red]Invalid input. Please enter a valid Borrow ID.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def view_lended_items(db_name, connection):
    db_number = db_name.replace("lendborrow", "")  
    lended_items_file = f"lended_items{db_number}.csv"
    
    try:
        with open(lended_items_file, "r", newline="") as file:
            reader = csv.reader(file)
            items = list(reader)
            
            if not items:
                console.print("[yellow]No lended items found.[/yellow]")
                return
            
            table = Table(title="Lended Items", show_lines=True)
            table.add_column("ID", justify="center", style="cyan")
            table.add_column("Item", style="bold")
            table.add_column("Lender ID", justify="center", style="magenta")
            table.add_column("Borrower ID", justify="center", style="magenta")
            table.add_column("From Date", justify="center")
            table.add_column("To Date", justify="center")
            
            # Skip header if it matches expected column names
            if items and items[0] == ["Borrow ID", "Item", "From Date", "To Date", "Borrower ID", "Lender ID"]:
                items = items[1:]  # Remove header row

            for item in items:
                table.add_row(*item)

            console.print(table)
    except FileNotFoundError:
        console.print("[yellow]No lended items found.[/yellow]")

def view_transaction_history(db_name, connection):
    db_number = db_name.replace("lendborrow", "")  
    transactions_file = f"transactions{db_number}.txt"
    
    try:
        with open(transactions_file, "r", newline="") as file:
            data = file.read().strip()
            if not data:
                console.print("[yellow]No transaction history found.[/yellow]")
                return
            
            console.print("\n[bold cyan]Transaction History:[/bold cyan]")
            console.print(Text(data, style="dim"))
            
    except FileNotFoundError:
        console.print("[yellow]No transaction history found.[/yellow]")

def view_users_list(db_name, connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, name, email FROM user")
        users = cursor.fetchall()
        cursor.close()
        
        if not users:
            console.print("[yellow]No users found.[/yellow]")
            return
        
        table = Table(title="User List", show_lines=True)
        table.add_column("User ID", justify="center", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Email", style="magenta")
        
        for user in users:
            table.add_row(*map(str, user))
        
        console.print(table)
    
    except mysql.connector.Error as e:
        console.print(f"[red]Error retrieving users: {e}[/red]")

def view_admins_list(db_name, connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT admin_id, admin_name, email FROM admin")
        admins = cursor.fetchall()
        cursor.close()
        
        if not admins:
            console.print("[yellow]No admins found.[/yellow]")
            return
        
        table = Table(title="Admin List", show_lines=True)
        table.add_column("Admin ID", justify="center", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Email", style="magenta")
        
        for admin in admins:
            table.add_row(*map(str, admin))
        
        console.print(table)
    
    except mysql.connector.Error as e:
        console.print(f"[red]Error retrieving admins: {e}[/red]")

def put_borrow_request(db_name, connection, user_id):
    db_number = db_name.replace("lendborrow", "")  
    borrow_file = f"borrow{db_number}.csv"

    item_name = Prompt.ask("[cyan]Enter the item name[/cyan]")
    from_date = Prompt.ask("[cyan]Enter the borrowing start date (YYYY-MM-DD)[/cyan]")
    to_date = Prompt.ask("[cyan]Enter the borrowing end date (YYYY-MM-DD)[/cyan]")

    next_borrow_id = 1  
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            borrow_requests = list(reader)

            if borrow_requests and borrow_requests[0][0].lower() == "borrow id":
                borrow_requests = borrow_requests[1:]

            if borrow_requests:
                last_id = int(borrow_requests[-1][0])
                next_borrow_id = last_id + 1  

    except FileNotFoundError:
        pass  

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
        console.print(f"[red]Error updating borrow status: {e}[/red]")
        return

    try:
        with open(borrow_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([next_borrow_id, item_name, from_date, to_date, user_id])
        console.print("[green]Borrow request submitted successfully![/green]")

        log_transaction(db_name, user_id, "requested", item_name)

    except Exception as e:
        console.print(f"[red]Error writing to borrow file: {e}[/red]")

def accept_borrow_request(db_name, connection, lender_id):
    db_number = db_name.replace("lendborrow", "")  
    borrow_file = f"borrow{db_number}.csv"
    lended_items_file = f"lended_items{db_number}.csv"

    borrow_requests = []
    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            borrow_requests = list(reader)

        if not borrow_requests:
            console.print("[yellow]No borrow requests found.[/yellow]")
            return

        if borrow_requests[0][0].lower() == "borrow id":
            borrow_requests = borrow_requests[1:]

        table = Table(title="Available Borrow Requests", show_lines=True)
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("Item", style="bold")
        table.add_column("From Date", justify="center")
        table.add_column("To Date", justify="center")
        table.add_column("User ID", justify="center", style="magenta")

        for request in borrow_requests:
            table.add_row(*request)

        console.print(table)

    except FileNotFoundError:
        console.print("[yellow]No borrow requests found.[/yellow]")
        return

    try:
        accept_id = int(Prompt.ask("[cyan]Enter the Borrow Request ID to accept[/cyan]")) - 1
        if accept_id < 0 or accept_id >= len(borrow_requests):
            console.print("[red]Invalid selection.[/red]")
            return

        accepted_request = borrow_requests.pop(accept_id)
        
        try:
            borrower_id = int(accepted_request[4])  
        except ValueError:
            console.print("[red]Error: Borrower ID is not a valid number.[/red]")
            return
        
        borrowed_item = accepted_request[1]
        from_date = accepted_request[2]
        to_date = accepted_request[3]

        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE user SET borrow_status = 'received' WHERE user_id = %s", (borrower_id,))
            cursor.execute("UPDATE user SET lend_status = 'accepted', lended_item = %s WHERE user_id = %s", (borrowed_item, lender_id))
            connection.commit()
            cursor.close()
        except mysql.connector.Error as e:
            console.print(f"[red]Error updating user statuses: {e}[/red]")
            return

        try:
            with open(borrow_file, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Borrow ID", "Item", "From Date", "To Date", "User ID"])  # Keep header
                for index, request in enumerate(borrow_requests, start=1):
                    writer.writerow([index] + request[1:])
            
            console.print("[green]Borrow request accepted successfully![/green]")

            with open(lended_items_file, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([accepted_request[0], borrowed_item, from_date, to_date, borrower_id, lender_id])

            log_transaction(db_name, borrower_id, "Accepted", borrowed_item, lender_id)
            log_transaction(db_name, lender_id, "Lent", borrowed_item, borrower_id)

        except Exception as e:
            console.print(f"[red]Error updating files: {e}[/red]")
    
    except ValueError:
        console.print("[red]Invalid input. Please enter a valid Borrow Request ID.[/red]")

def cancel_borrow_request(db_name, connection, user_id):
    db_number = db_name.replace("lendborrow", "")  
    borrow_file = f"borrow{db_number}.csv"

    borrow_requests = []
    user_requests = {}

    try:
        with open(borrow_file, "r", newline="") as file:
            reader = csv.reader(file)
            borrow_requests = list(reader)

        if not borrow_requests:
            console.print("[yellow]No borrow requests found.[/yellow]")
            return

        table = Table(title="Your Borrow Requests", show_lines=True)
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("Item", style="bold")
        table.add_column("From Date", justify="center")
        table.add_column("To Date", justify="center")

        for request in borrow_requests[1:]:  # Skip header row
            if request[4] == str(user_id):  
                request_id = request[0]  
                user_requests[request_id] = request
                table.add_row(str(request_id), request[1], request[2], request[3])

        if not user_requests:
            console.print("[yellow]You have no active borrow requests.[/yellow]")
            return

        console.print(table)

    except FileNotFoundError:
        console.print("[yellow]No borrow requests found.[/yellow]")
        return

    # Ask which request to cancel
    try:
        cancel_id = Prompt.ask("[cyan]Enter the Borrow Request ID to cancel[/cyan]")
        if cancel_id not in user_requests:
            console.print("[red]Invalid selection.[/red]")
            return

        # Remove the request based on request ID (not list index)
        cancelled_request = user_requests.pop(str(cancel_id))
        borrow_requests = [req for req in borrow_requests if req[0] != str(cancel_id)]

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
            console.print(f"[red]Error resetting borrow status: {e}[/red]")
            return

        # Log the cancellation
        log_transaction(db_name, user_id, "Cancelled", cancelled_request[1])

        # Renumber borrow requests and update the CSV
        try:
            with open(borrow_file, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Borrow ID", "Item", "From Date", "To Date", "User ID"])  # Write header once
                for index, request in enumerate(borrow_requests[1:], start=1):
                    writer.writerow([str(index)] + request[1:])  # Ensure ID remains as a string

            console.print("[green]Borrow request cancelled successfully![/green]")

        except Exception as e:
            console.print(f"[red]Error updating borrow file: {e}[/red]")
    
    except ValueError:
        console.print("[red]Invalid input. Please enter a valid Borrow Request ID.[/red]")
        
