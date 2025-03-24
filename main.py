import setup
import roles  

def user_menu(db_name, connection, user_id):
    while True:
        print(f"\nUser Menu (User ID: {user_id}):")  # Show logged-in user's ID
        print("1. View Borrow Requests")
        print("2. Put a Borrow Request")
        print("3. Accept Borrow Request")
        print("4. Cancel Borrow Request")  
        print("5. Logout")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            roles.view_borrow_requests(db_name, connection)
        elif choice == "2":
            roles.put_borrow_request(db_name, connection, user_id)  # Pass user_id
        elif choice == "3":
            roles.accept_borrow_request(db_name, connection, user_id)  # Pass user_id
        elif choice == "4":
            roles.cancel_borrow_request(db_name, connection, user_id)  # Pass user_id
        elif choice == "5":
            print("Logging out from user menu...")
            break
        else:
            print("Invalid choice! Please enter a valid option.")

def admin_menu(db_name, connection):
    while True:
        print("\nAdmin Menu:")
        print("1. View borrow requests")
        print("2. Remove borrow requests")
        print("3. View lended items list")
        print("4. View transaction history")
        print("5. View users list")
        print("6. View admins list")
        print("7. Logout")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            roles.view_borrow_requests(db_name, connection)
        elif choice == "2":
            roles.remove_borrow_requests(db_name, connection)
        elif choice == "3":
            roles.view_lended_items(db_name, connection)
        elif choice == "4":
            roles.view_transaction_history(db_name, connection)
        elif choice == "5":
            roles.view_users_list(db_name, connection)
        elif choice == "6":
            roles.view_admins_list(db_name, connection)
        elif choice == "7":
            print("Logging out from admin menu...")
            break
        else:
            print("Invalid choice! Please enter a valid option.")

def database_menu(db_name, connection):
    while True:
        print("\nDatabase Menu:")
        print("1. Change admin passkey")
        print("2. User registration")
        print("3. User login")
        print("4. Admin registration")
        print("5. Admin login")
        print("6. Logout")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            roles.change_admin_passkey(db_name, connection)
        elif choice == "2":
            roles.user_registration(connection)
        elif choice == "3":
            user_id = roles.user_login(connection)  # Capture user_id
            if user_id:  # If login successful, pass user_id to user_menu
                user_menu(db_name, connection, user_id)  
        elif choice == "4":
            roles.admin_registration(connection)
        elif choice == "5":
            if roles.admin_login(connection):  
                admin_menu(db_name, connection)  
        elif choice == "6":
            print("Logging out...")
            break
        else:
            print("Invalid choice! Please enter a valid option.")

def main():
    print("Welcome to the Lend and Borrow System")
    while True:
        print("\n1. Enter passkey to access a database")
        print("2. First time using? Create a new database")
        print("3. Exit")
        choice = input("Enter your choice: ")
        
        if choice == "1":
            passkey = input("Enter your 4-letter passkey: ")
            db_name, connection = setup.get_database_name(passkey)
            
            if db_name and connection:
                cursor = connection.cursor()
                cursor.execute(f"USE {db_name}")  # Explicitly select the database
                print(f"Access granted to database: {db_name}")
                database_menu(db_name, connection)
                connection.close()  # Close the connection after use
            else:
                print("Invalid passkey! Please try again.")
        
        elif choice == "2":
            setup.create_new_database()
        
        elif choice == "3":
            print("Exiting... Goodbye!")
            break
        
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
