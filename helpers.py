import openai
import time
from tqdm import tqdm
import subprocess

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os

from selenium.common.exceptions import TimeoutException
from storeFunctions import *

def find_chrome_path():
    try:
        # Use 'mdfind' to locate Google Chrome
        path = subprocess.check_output(["mdfind", "Google Chrome"]).decode("utf-8").strip().splitlines()
        
        # Filter to find the correct path
        for p in path:
            if "Google Chrome.app" in p:
                return p
            
        return None
    except subprocess.CalledProcessError:
        return None

load_dotenv()
# Initialize the OpenAI API key
key = os.getenv("OPENAI_API_KEY")
openai.api_key = key

def get_quiz_answer(quiz_string):
    # Make an API call to OpenAI to get the answer
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Or use another model if available
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer the following quiz by providing only the letter in lower case of the correct answer."},
            {"role": "user", "content": quiz_string}
        ],
        temperature=0.0  # Keep it deterministic for quizzes
    )

    # Extract and return the assistant's message (answer)
    answer = response['choices'][0]['message']['content']
    return answer.strip()



def watchcourse(module, driver, homepageId, cursor):   
    
    try:
        # Step 1: Navigate to the SCORM page (after successful login)
        WebDriverWait(driver, 10).until(
            EC.url_contains("https://virtuale.unibo.it/")
        )
        driver.get(f"https://virtuale.unibo.it/mod/scorm/view.php?id={module}")
            
        # Step 2: Submit the SCORM form to start the content
        scorm_form_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "n"))
        )
        scorm_form_button.click()
    
    except Exception as e:
        print("Error navigating to the SCORM page")
        print("This must be an introductory page or a page without videos to show")
        print("Redirecting to the homepage")
        print("")
        
        WebDriverWait(driver, 10).until(
            EC.url_contains("https://virtuale.unibo.it/")
        )
        driver.get(f"https://virtuale.unibo.it/course/view.php?id={homepageId}")
        
        print("Module", module, "skipped")
        print("")
        return
    
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "scorm_object")))
    driver.switch_to.frame("scorm_object")

    time.sleep(2)  # Wait for the content to load (adjust as needed)

    try:
        riprendi_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Riprendi']"))
        )
        
        if riprendi_button.is_displayed() and riprendi_button.is_enabled():
            riprendi_button.click()
        else:
            print("Riprendi button is not visible or enabled")
            
    except Exception as e:
        print("Error finding 'Riprendi' button:")
        print("This must be the first video of the course")
        print("")
    

    counter = 0
    while True:
        if counter == 0:
            # Initial wait to check if the progress truly starts at 100%
            time.sleep(5)  # Wait to allow the content to load properly
            print("Starting the progress bar monitoring...")    
            progress_bar = tqdm(total=100, desc="Progress", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}", initial=0)  
            print("Here we go!")     
        try:
            # Wait until the input element representing the progress bar is present
            progress_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="range"][aria-label="avanzamento diapositiva"]'))
            )
            
            # Get the current progress value
            progress_value_text = progress_input.get_attribute("aria-valuetext")
            if progress_value_text:
                progress_value = int(progress_value_text.replace("%", ""))  # Convert to an integer
            else:
                progress_value = 0

            # Confirm if the bar is at 100% and remains there
            if progress_value == 100 and counter > 3:  # Allow some time to confirm progress
                print("\nProgress reached 100%! Clicking 'Next' button...")
                print("")

                try:
                    # Step 4: Click the "Next" button once progress is 100%
                    next_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#next:not([aria-disabled='true'])"))
                    )
                    next_button.click()
                    time.sleep(1)
                    
                    progress_bar.close()  # Close the progress bar
                    counter = -1  # Reset the counter after clicking the "Next" button
                except Exception as e:
                    print("There is no Next Button, we have reached the end of this module")
                    print("")
                    
                    driver.switch_to.default_content()
                    insertLink(cursor, module)
                    break

            if counter < 3:
                # Update tqdm progress bar
                progress_bar.n = progress_value
                progress_bar.refresh()  # Manually refresh to show the new progress

            counter += 1
            time.sleep(1)  # Wait before checking again

        except Exception as e:
            print("Error monitoring the progress bar:", e)
            break
    print(f"Module {module} watched")
    print("")
        
    WebDriverWait(driver, 10).until(
        EC.url_contains("https://virtuale.unibo.it/")
    )
    driver.get(f"https://virtuale.unibo.it/course/view.php?id={homepageId}")
    
    time.sleep(3) 
    
def elements_loader(driver, first, section_num):
    course_section = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'courseindex-section'))
    )

    # Find all elements with the class 'courseindex-section'
    course_sections = driver.find_elements(By.CLASS_NAME, 'courseindex-section')
    section = course_sections[section_num]
    
    # Check for visible elements in the current section
    try:
        # Wait for the content of the current section to be visible
        section_content = WebDriverWait(section, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'courseindex-item-content'))
        )

        # Find all course modules within the section
        matching_elements = WebDriverWait(section_content, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, ".//li[starts-with(@id, 'course-index-cm-')]"))
        )
        
        if first:
            print("Found", len(matching_elements), "course modules in this section")
        
        return matching_elements
    except TimeoutException:
        if first:
            print(f"Timeout: No course modules found in section {section_num}.")
        
        return 0 # Skip to the next section if no modules are found
    

answers = {
    "a": 0,
    "b": 1,
    "c": 2,
    "d": 3
}
def AutoTest(driver, number, cursor):
    print("Starting the quiz...")
    # Step 1: click the "Attempt quiz" button
    attempt_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, ".//form[contains(@action, 'quiz') and @method='post']//button[@type='submit']"))
    )
    attempt_button.click()
    
    print("Quiz started")
    
    time.sleep(2)
    
    while True:
        # Step 2: search the question and the choices
        question_container = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'question-')]"))
        )
        question_content = question_container.find_element(By.CLASS_NAME, "content")
        question_text = question_content.text
        print("Question:", question_text)
        print("")
        
        print("Getting the answer...")
        # Get the correct response based on the question text
        response = get_quiz_answer(question_text)
        answer = answers[response]
        print("Answer:", response)
        print("")
        
        # Get all choices (radio buttons)
        print("Selecting the answer...")
        choices_num = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, ".//input[@type='radio']"))
        )
        print("Iterating through the choices...")
        counter = 0
        for choice in choices_num:
            if choice.get_attribute("value") == str(answer):
                choices = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, ".//input[@type='radio']"))
                )
                
                choices[counter].click()
                print("Selected:", response)
                print("")
                break
            counter += 1
        
        # Find and click the "Next page" or "Finish attempt" button
        print("Moving to the next question...")
        next_buttons_ids = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//input[@type='submit']"))
        )
        
        goOut = False
        for counter in range(len(next_buttons_ids)):
            next_buttons = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//input[@type='submit']"))
            )
            # Check if the value contains "Next page"
            if "Next page" in next_buttons[counter].get_attribute("value"):
                print("Next question...")
                next_buttons[counter].click()
                print("Button clicked")
                break
            # Check if the value contains "Finish attempt"
            elif "Finish attempt" in next_buttons[counter].get_attribute("value"):
                print("Last question reached. Attempting to finish the quiz...")
                next_buttons[counter].click()
                goOut = True
                break
        if goOut:
            break
    
    # Step 3: Submit all answers
    print("Submitting the quiz...")
    submit_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Submit all and finish']"))
    )
    submit_button.click()
    
    print("Confirming the submission...")
    # Confirm the submission in the modal dialog
    submit_button_confirm = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-dialog')]//button[text()='Submit all and finish']"))
    )
    submit_button_confirm.click()
    
    insertLink(cursor, number)
    print("Quiz completed successfully")
    print("")
    return True

    
    