import os
import sys
import shutil
import subprocess
import datetime
import sqlite3
from prettytable import PrettyTable

# ANSI escape codes for colors
color_red = '\033[31m'
color_green = '\033[32m'
color_yellow = '\033[33m'
color_blue = '\033[34m'
color_cyan = '\033[36m'
color_lightred = '\033[91m'
color_light_blue = '\033[94m'
color_reset = '\033[0m'

# Display of InstaScraper Bannner & other details
banner_path = os.path.join('banner.txt')
with open(banner_path, 'r') as file:
    banner = file.read()
    print(color_lightred + banner + color_reset)

print(color_light_blue +
      "Welcome to InstaScraper - A powerful content scraping tool for Instagram.\n" + "(Currently supports only Instagram Public Accounts)\n" + color_reset)

print(color_cyan + "Developed and maintained by Aswin V S (" +
      "https://github.com/aswin-vs" + ')\n')

print("This software is intended solely for educational purposes only. The author and publisher of this tool are not responsible for any damages or losses that may occur from this. Use at your own risk and liability.\n" + color_reset)

# Getting User chose
print("What you choose to do ?\n" + "1) Scrap Now !\n" +
      "2) View Scrap History\n" + "3) Clear any Record\n" + "4) Exit\n")


def scrapNow():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # create the table if it doesn't exist
    cursor.execute("CREATE TABLE IF NOT EXISTS InstaScraper (Serial_No INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, From_Date DATE, To_Date DATE, Scraped_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

    # ask for user input and validate the dates
    while True:
        try:
            print()
            name = input("Enter a valid Instagram account name: ")
            from_date_str = input("Enter From Date (DD/MM/YYYY): ")
            from_date = datetime.datetime.strptime(
                from_date_str, '%d/%m/%Y').date()
            if not (1 <= from_date.day <= 31 and 1 <= from_date.month <= 12 and 2010 <= from_date.year <= datetime.date.today().year):
                raise ValueError
            to_date_str = input("Enter To Date (DD/MM/YYYY): ")
            print()
            to_date = datetime.datetime.strptime(
                to_date_str, '%d/%m/%Y').date()
            if not (1 <= to_date.day <= 31 and 1 <= to_date.month <= 12 and 2010 <= to_date.year <= datetime.date.today().year):
                raise ValueError
            if from_date > to_date:
                print(
                    color_red+"From Date cannot be greater than To Date. Please enter valid dates.\n"+color_reset)
                continue
        except ValueError:
            print(color_red+"Invalid date format or date range. Please enter dates in DD/MM/YYYY format between 2010 and present year.\n"+color_reset)
            continue

        # check for overlapping dates
        cursor.execute("SELECT * FROM InstaScraper WHERE Name=? AND ((From_Date <= ? AND To_Date >= ?) OR (From_Date >= ? AND From_Date <= ?) OR (To_Date >= ? AND To_Date <= ?))",
                       (name, from_date, from_date, from_date, to_date, to_date, to_date))
        overlapping_dates = cursor.fetchall()
        if overlapping_dates:
            print(
                color_red+"The following date ranges already exist in the database:"+color_reset)
            table = PrettyTable(
                ['Serial No', 'Name', 'From', 'To', 'Scraped At'])
            for row in overlapping_dates:
                table.add_row(row)
            print(table)
            print(color_red+"Please enter different dates.\n"+color_reset)
        else:
            break

    from_date_str = str(from_date)
    to_date_str = str(to_date)

    # Scrapping process
    from_mod = str(from_date_str).replace('-0', ', ')
    from_mod = str(from_mod).replace('-', ', ')
    to_mod = str(to_date_str).replace('-0', ', ')
    to_mod = str(to_mod).replace('-', ', ')

    from_mod1 = "-".join(from_date_str.split('-')[::-1])
    to_mod1 = "-".join(to_date_str.split('-')[::-1])

    command1 = 'date_utc >= datetime(' + from_mod + \
        ') and ' + 'date_utc <= datetime(' + to_mod + ')'

    command2 = '" --dirname-pattern "Scraps/'+name+'_'+from_mod1+'_'+to_mod1+'"'

    command3 = "instaloader --no-resume --no-video-thumbnails --no-captions --no-profile-pic --no-metadata-json --sanitize-paths --post-filter=" + \
        '"'+command1+command2+' "'+name+'"'

    # Check if the Output folder already exists and deletes it
    folder_path = "Scraps/"+name+'_'+from_mod1+'_'+to_mod1

    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            print(f"Existing folder at {folder_path} has been deleted\n")
        except Exception as e:
            print(f"Error deleting existing folder at {folder_path}: {e}\n")

    process = subprocess.Popen(
        command3, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # loop over the output line by line and display it in real-time
    for line in iter(process.stdout.readline, b''):
        print(line.decode().rstrip())

    # check for the end of the output
    while process.poll() is None:
        pass

    # wait for the process to finish and get the final output
    stdout, stderr = process.communicate()

    err_found = False

    if stderr is not None:
        if (len(stderr.decode()) > 1):
            err_found = True
            print(color_red+"\nSomething went wrong!\n"+color_reset)
            print(stderr.decode())

    if (err_found is False):
        print(color_green+"\nScrapping process completed successfully\nFiles can be found at InstaScraper/Scraps\n"+color_reset)

        # Insert data into the table
        cursor.execute("INSERT INTO InstaScraper (Name, From_Date, To_Date) VALUES (?, ?, ?)",
                       (name, from_date, to_date))
        conn.commit()
        print(color_yellow, cursor.rowcount, "Scrap record inserted.\n")

        # print the table data
        cursor.execute("SELECT * FROM InstaScraper")
        table = PrettyTable(['Serial No', 'Name', 'From', 'To', 'Scraped At'])
        for row in cursor.fetchall():
            table.add_row(row)
        print(table)
        print("\n", color_reset)

        # close the database connection
        conn.close()

        # Getting User chose once again
        print("What you choose to do ?\n" + "1) Scrap Now !\n" +
              "2) View Scrap History\n" + "3) Clear any Record\n" + "4) Exit\n")
        getChoose()


def scrapHistory():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # print the table data
    print(color_yellow + "\nPrevious Scrape History")
    cursor.execute("SELECT * FROM InstaScraper")
    table = PrettyTable(['Serial No', 'Name', 'From', 'To', 'Scraped At'])
    for row in cursor.fetchall():
        table.add_row(row)
    print(table)
    print("\n"+color_reset)

    # close the database connection
    conn.close()

    # Getting User chose once again
    print("What you choose to do ?\n" + "1) Scrap Now !\n" +
          "2) View Scrap History\n" + "3) Clear any Record\n" + "4) Exit\n")
    getChoose()


def clearRecord():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # print the table data
    print(color_yellow + "\nPrevious Scrape History")
    cursor.execute("SELECT * FROM InstaScraper")
    table = PrettyTable(['Serial No', 'Name', 'From', 'To', 'Scraped At'])
    for row in cursor.fetchall():
        table.add_row(row)
    print(table)
    print("\n"+color_reset)

    # get user input for delete option
    delete_option = input(
        "Enter 'all' to delete all records, or enter comma-separated serial numbers to delete specific records: ")

    if delete_option.lower() == 'all':
        # execute a DELETE statement to remove all records from the table
        cursor = conn.cursor()
        cursor.execute("DELETE FROM InstaScraper")
        conn.commit()
        cursor.execute("VACUUM")
        conn.commit()
        print(color_lightred+"All records deleted successfully."+color_reset)
    else:
        try:
            # split the user input into individual serial numbers
            serial_numbers = delete_option.split(',')

            # execute a DELETE statement to remove the records with the given serial numbers
            cursor = conn.cursor()
            for serial_number in serial_numbers:
                cursor.execute(
                    "DELETE FROM InstaScraper WHERE SERIAL NO=?", (serial_number,))
            conn.commit()
            print(color_lightred +
                  f"{len(serial_numbers)} records deleted successfully."+color_reset)

        except:
            print(
                color_red+"Incorrect serial number Input. Try again"+color_reset)

    # print the updated table data
    print(color_yellow + "\nUpdated Scrape History")
    cursor.execute("SELECT * FROM InstaScraper")
    table = PrettyTable(['Serial No', 'Name', 'From', 'To', 'Scraped At'])
    for row in cursor.fetchall():
        table.add_row(row)
    print(table)
    print("\n"+color_reset)

    # close the database connection
    conn.close()

    # Getting User chose once again
    print("What you choose to do ?\n" + "1) Scrap Now !\n" +
          "2) View Scrap History\n" + "3) Clear any Record\n" + "4) Exit\n")
    getChoose()


def getChoose():

    UserChoose = int(input("Enter Chose Number: "))

    if (UserChoose == 1):
        scrapNow()
    elif (UserChoose == 2):
        scrapHistory()
    elif (UserChoose == 3):
        clearRecord()
    elif (UserChoose == 4):
        sys.exit()
    else:
        print(color_red+"Incorrect Input! Try Again..\n"+color_reset)
        getChoose()


# Driver code
getChoose()
