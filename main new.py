import setup
import roles  
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text

console = Console()

def user_menu(db_name, connection, user_id):
    while True:
        console.print(f"[bold cyan]\nUser Menu (User ID: {user_id}):[/bold cyan]")
        table = Table(show_header=False)
        table.add_row("1.", "View Borrow Requests")
        table.add_row("2.", "Put a Borrow Request")
        table.add_row("3.", "Accept Borrow Request")
        table.add_row("4.", "Cancel Borrow Request")
        table.add_row("5.", "Logout")
        console.print(table)
        
        choice = Prompt.ask("Enter your choice")
        
        if choice == "1":
            roles.view_borrow_requests(db_name, connection)
        elif choice == "2":
            roles.put_borrow_request(db_name, connection, user_id)
        elif choice == "3":
            roles.accept_borrow_request(db_name, connection, user_id)
        elif choice == "4":
            roles.cancel_borrow_request(db_name, connection, user_id)
        elif choice == "5":
            console.print("[yellow]Logging out from user menu...[/yellow]")
            break
        else:
            console.print("[red]Invalid choice! Please enter a valid option.[/red]")

def admin_menu(db_name, connection):
    while True:
        console.print("[bold cyan]\nAdmin Menu:[/bold cyan]")
        table = Table(show_header=False)
        options = [
            "View borrow requests", "Remove borrow requests", "View lended items list", 
            "View transaction history", "View users list", "View admins list", "Logout"
        ]
        for i, option in enumerate(options, start=1):
            table.add_row(str(i) + ".", option)
        console.print(table)
        
        choice = Prompt.ask("Enter your choice")
        
        if choice == "1":
            roles.view_borrow_requests(db_name, connection)
        elif choice == "2":
            roles.delete_borrow_request(db_name, connection)
        elif choice == "3":
            roles.view_lended_items(db_name, connection)
        elif choice == "4":
            roles.view_transaction_history(db_name, connection)
        elif choice == "5":
            roles.view_users_list(db_name, connection)
        elif choice == "6":
            roles.view_admins_list(db_name, connection)
        elif choice == "7":
            console.print("[yellow]Logging out from admin menu...[/yellow]")
            break
        else:
            console.print("[red]Invalid choice! Please enter a valid option.[/red]")

def database_menu(db_name, connection):
    while True:
        console.print("[bold cyan]\nDatabase Menu:[/bold cyan]")
        table = Table(show_header=False)
        options = [
            "Change admin passkey", "User registration", "User login", 
            "Admin registration", "Admin login", "Logout"
        ]
        for i, option in enumerate(options, start=1):
            table.add_row(str(i) + ".", option)
        console.print(table)
        
        choice = Prompt.ask("Enter your choice")
        
        if choice == "1":
            roles.change_admin_passkey(db_name, connection)
        elif choice == "2":
            roles.user_registration(connection)
        elif choice == "3":
            user_id = roles.user_login(connection)
            if user_id:
                user_menu(db_name, connection, user_id)
        elif choice == "4":
            roles.admin_registration(db_name, connection)
        elif choice == "5":
            if roles.admin_login(connection):
                admin_menu(db_name, connection)
        elif choice == "6":
            console.print("[yellow]Logging out...[/yellow]")
            break
        else:
            console.print("[red]Invalid choice! Please enter a valid option.[/red]")

def main():
    console.print("[bold green]Welcome to the Lend and Borrow System[/bold green]")
    while True:
        table = Table(show_header=False)
        options = ["Enter passkey to access a database", "Create a new database", "Exit"]
        for i, option in enumerate(options, start=1):
            table.add_row(str(i) + ".", option)
        console.print(table)
        
        choice = Prompt.ask("Enter your choice")
        
        if choice == "1":
            passkey = Prompt.ask("Enter your 4-letter passkey")
            db_name, connection = setup.get_database_name(passkey)
            
            if db_name and connection:
                cursor = connection.cursor()
                cursor.execute(f"USE {db_name}")
                console.print(f"[green]Access granted to database: {db_name}[/green]")
                database_menu(db_name, connection)
                connection.close()
            else:
                console.print("[red]Invalid passkey! Please try again.[/red]")
        elif choice == "2":
            setup.create_new_database()
        elif choice == "3":
            console.print("[yellow]Exiting... Goodbye![/yellow]")
            break
        else:
            console.print("[red]Invalid choice! Please enter 1, 2, or 3.[/red]")

if __name__ == "__main__":
    main()
