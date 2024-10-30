#libraries to work with the browser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

#libary to create a banner
from pyfiglet import Figlet

#libraries to work with the database
from storeFunctions import *
import sqlite3 

#functions to work with the bot
from helpers import *

#libraries to manage sleep time and re expressions
import time
import re

print("Starting the program...")
print("Connecting to the database...")
print("")
connection = sqlite3.connect('./database/virtualeStore.db')

cursor = connection.cursor()
createTable(cursor)
connection.commit()

f = Figlet(font='speed')
red = "\033[91m"
reset = "\033[0m"
print(f"{red}{f.renderText('Virtuale Bot')}{reset}")


username = "giuseppe.berardi3@studio.unibo.it" #input("Enter your UNIBO username: ")
password = "///--ciaociaociao34" #getpass.getpass("Enter your UNIBO password: ")
module = "45323" #input("Enter the course id: ")

chrome_path = find_chrome_path()
if chrome_path is None:
    print("Google Chrome is not installed or not found.")
    exit(1)
    
# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Optional: run in headless mode
chrome_options.add_argument("--no-sandbox")  # Optional: for certain environments
chrome_options.add_argument("--disable-dev-shm-usage")  # Optional: for certain environments

chrome_options.binary_location = chrome_path

# Set up WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


# Step 1: Navigate to the main page and go to the login page
print("Navigating to the main page...")
print("")
driver.get("https://virtuale.unibo.it/")
time.sleep(2)

print("Logging in...")
print("")
# Step 2: Click the "Log in" link
login_link = driver.find_element(By.LINK_TEXT, "Log in")
login_link.click()

# Step 3: Click the "Enter with UNIBO" button
unibo_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, '.idp.btnUnibo'))
)
unibo_button.click()

try:
    # Step 4: Enter username and password in the login form
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "userNameInput"))
    )
    password_input = driver.find_element(By.ID, "passwordInput")

    # Enter your UNIBO credentials
    username_input.send_keys(username)  
    password_input.send_keys(password)  

    # Submit the form by pressing Enter
    password_input.send_keys(Keys.RETURN)
except Exception as e:
    print("Error logging in:", e)
    print("Please check your credentials and try again.")
    print("Exiting the program...")
    driver.quit()
    exit()

print("Logged in successfully")
print("")

print("Navigating to the course page...")
print("")
# Step 5: Navigate to the page of the current course
WebDriverWait(driver, 10).until(
    EC.url_contains("https://virtuale.unibo.it/")
)
driver.get(f"https://virtuale.unibo.it/course/view.php?id={module}")

# Wait for at least one element with the class 'courseindex-section' to be present
course_section = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CLASS_NAME, 'courseindex-section'))
)

# Find all elements with the class 'courseindex-section'
course_sections = driver.find_elements(By.CLASS_NAME, 'courseindex-section')
print("Found", len(course_sections), "course sections")
print("Starting to watch the course modules...")
print("This may take some time depending on the course content.")
print("Please do not close the browser window.")
print("")


# Iterate over each 'courseindex-section' element
for section_num in range(len(course_sections)):    
    print("-----------------------------------")
    print(f"Section {section_num}")
    print("-----------------------------------")
    

    # Check for visible elements in the current section
    matching_elements = elements_loader(driver, True, section_num)
    print("")
    if matching_elements == 0:
        continue

    for counter in range(len(matching_elements)):
        matching_elements2 = elements_loader(driver, False, section_num)
        
        element = matching_elements2[counter]
        elementId = element.get_attribute("id")
        
        match = re.search(r'course-index-cm-(\d+)', elementId)
        if match:
            number = match.group(1)
            
            if not checkLink(cursor, number):
                icon_state = None
                try:
                    # Use WebDriverWait to wait for the parent element
                    parent_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, f"//*[@id='{elementId}']"))
                    )
                    
                    try:
                        print(f"Checking if module {number} is already marked as done...")
                        # Now, within the parent element, wait for the icon with title "Done"
                        icon_state = WebDriverWait(parent_element, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "completion_complete"))
                        )

                        print(f"Module {number} is already marked as done")
                        print("")
                        
                        insertLink(cursor, number)
                        connection.commit()
                        continue  # Skip to the next iteration if already done
                    except:
                        print(f"Module {number} is not marked as done")
                        print("")
                        # If the 'Done' icon is not found, or some other error occurs, continue the process
                        pass
                    
                    
                    link_element = WebDriverWait(parent_element, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'a'))
                    )
                    
                    print("Checking if the module is a quiz...")
                    if "quiz" in link_element.get_attribute("href"):
                        WebDriverWait(driver, 10).until(
                            EC.url_contains("https://virtuale.unibo.it/")
                        )
                        driver.get(f"https://virtuale.unibo.it/mod/quiz/view.php?id={number}")

                        AutoTest(driver, number, cursor)
                        continue 
                    else:
                        print("Module is not a quiz")
                        print("The module is a set of videos")
                        print(f"Watching module {number}...")
                        watchcourse(number, driver, module, cursor) 
                except:
                    print(f"Error watching module {number}")
                    print("The module may be some other type of content")
                    print("Continuing to the next module...")
                    print("")
                    
                    insertLink(cursor, number)
                    # If the 'Done' icon is not found, or some other error occurs, continue the process
                    pass
                connection.commit()
            else:
                print(f"Module {number} already watched")
                print("")

    
print("Program completed")
print("Bye Bye")
cursor.close()
connection.close()
driver.quit()



    

    
    
    