from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

from pyfiglet import Figlet

from storeFunctions import *
from helpers import *

import time
import getpass
import re

import sqlite3 

connection = sqlite3.connect('./database/virtualeStore.db')

cursor = connection.cursor()
createTable(cursor)
connection.commit()

f = Figlet(font='speed')
print(f.renderText('Virtuale Bot'))


username = "giuseppe.berardi3@studio.unibo.it" #input("Enter your UNIBO username: ")
password = "///--ciaociaociao34" #getpass.getpass("Enter your UNIBO password: ")
module = "45323" #input("Enter the course id: ")

"""
CODE TO RUN THE BOT IN GOOGLE CHROME DEFAULT MODE

chromedriver_autoinstaller.install()
chrome_options = Options()

# Set up WebDriver (assuming you're using Chrome)
driver = webdriver.Chrome(service=Service(), options=chrome_options)
"""

driver = webdriver.Chrome()

# Step 1: Navigate to the main page and go to the login page
driver.get("https://virtuale.unibo.it/")
time.sleep(2)

# Step 2: Click the "Log in" link
login_link = driver.find_element(By.LINK_TEXT, "Log in")
login_link.click()

# Step 3: Click the "Enter with UNIBO" button
unibo_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, '.idp.btnUnibo'))
)
unibo_button.click()

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


# Iterate over each 'courseindex-section' element
for section in course_sections:
    # Find elements whose id starts with 'course-index-cm-' followed by a number
    matching_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, ".//*[starts-with(@id, 'course-index-cm-')]"))
    )
            
    for counter in range(len(matching_elements)):
        matching_elements2 = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, ".//*[starts-with(@id, 'course-index-cm-')]"))
        )
        
        element = matching_elements2[counter]
        elementId = element.get_attribute("id")
        
        match = re.search(r'course-index-cm-(\d+)', elementId)
        if match:
            number = match.group(1)
            
            done_icon = None
            try:
                # Use WebDriverWait to wait for the parent element
                parent_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[@id='{elementId}']/.."))
                )
                
                # Now, within the parent element, wait for the icon with title "Done"
                done_icon = WebDriverWait(parent_element, 10).until(
                    EC.presence_of_element_located((By.XPATH, ".//i[contains(@class, 'icon fa fa-circle fa-fw') and @title='Done']"))
                )
                
                print(f"Module {number} is already marked as done")
                insertLink(cursor, number)
                continue  # Skip to the next iteration if already done
            except:
                # If the 'Done' icon is not found, or some other error occurs, continue the process
                pass
            
            # If not done, proceed with checking and watching the course
            if not checkLink(cursor, number) or not done_icon:
                if not checkLink(cursor, number):
                    insertLink(cursor, number)
                    connection.commit()
                
                watchcourse(number, driver, module)
                print(f"Module {number} watched")
            else:
                print(f"Module {number} already watched")




    
print("program completed")
cursor.close()
connection.close()
driver.quit()



    

    
    
    