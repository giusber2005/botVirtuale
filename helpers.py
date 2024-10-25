import openai
import time
from tqdm import tqdm

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os

from selenium.common.exceptions import TimeoutException, NoSuchElementException



""" 
secret_path = "/run/secrets/openai_api_key"

with open(secret_path, 'r') as secret_file:
    key = secret_file.read().strip()
"""

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



def watchcourse(module, driver, homepageId):   
    
    try:
        # Step 1: Navigate to the SCORM page (after successful login)
        WebDriverWait(driver, 10).until(
            EC.url_contains("https://virtuale.unibo.it/")
        )
        driver.get(f"https://virtuale.unibo.it/mod/scorm/view.php?id={module}")

    
        h1_elements = driver.find_elements(By.TAG_NAME, 'h1')
        for h1 in h1_elements:
            if "Test" in h1.text:
                AutoTest(driver)
                print("Test completed")
                return
            
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
        print("Error finding 'Riprendi' button:", e)

    progress_bar = tqdm(total=100, desc="Progress", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}", initial=0)
    
    # Step 3: Monitor progress bar for aria-valuetext="100%"
    counter = 0
    while True:
        try:
            # Wait until the input element representing the progress bar is present
            progress_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="range"][aria-label="avanzamento diapositiva"]'))
            )
            
            if counter == 0:
                time.sleep(4)  # Wait for the progress bar to update initially
                counter += 1
                
            progress_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="range"][aria-label="avanzamento diapositiva"]'))
            )
                          
            # Get the current progress value
            progress_value_text = progress_input.get_attribute("aria-valuetext")
            if progress_value_text:
                progress_value = int(progress_value_text.replace("%", ""))  # Convert to an integer
            else:
                progress_value = 0
    
            # Update tqdm progress bar
            progress_bar.n = progress_value
            progress_bar.refresh()  # Manually refresh to show the new progress
    
            # Check if progress reached 100%
            if progress_value == 100:
                print("\nProgress reached 100%! Clicking 'Next' button...")
                print("")

                try:
                    # Step 4: Click the "Next" button once progress is 100%
                    next_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#next:not([aria-disabled='true'])"))
                    )
                    next_button.click()
                    time.sleep(1)
                    break  # Exit the loop once the next button is clicked
                except Exception as e:
                    print("There is no Next Button, we have reached to end of this module")
                    print("")
                    break
            else:
                # Wait before checking again
                time.sleep(1)

        except Exception as e:
            print("Error monitoring the progress bar:", e)
            break
        
    print(f"Module {module} watched")
    print("")
    
    #Close the tqdm progress bar once done
    progress_bar.close()
        
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
    

def AutoTest(driver):
    # Step 1: click the "Attempt quiz" button
    attempt_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Attempt quiz']"))
    )
    attempt_button.click()
    
    time.sleep(2)
    
    while True:
        # Step 2: search the question and the choices
        question_container = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'question-')]"))
        )
        question_content = question_container.find_element(By.CLASS_NAME, "content")
        question_text = question_content.text
        
        # Get the correct response based on the question text
        response = get_quiz_answer(question_text)
        
        # Get all choices (radio buttons)
        choices = question_container.find_elements(By.XPATH, ".//input[@type='radio']")
        for choice in choices:
            # Compare the associated label text with the response
            label = driver.find_element(By.XPATH, f"//label[@for='{choice.get_attribute('id')}']")
            if label.text.strip().lower() == response.lower():
                choice.click()
                break
        
        # Find and click the "Next page" or "Finish attempt" button
        next_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        )
        
        if next_button.get_attribute("value") == "Next page":
            next_button.click()
        elif next_button.get_attribute("value") == "Finish attempt":
            next_button.click()
            break
    
    # Step 3: Submit all answers
    submit_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Submit all and finish']"))
    )
    submit_button.click()
    
    # Confirm the submission in the modal dialog
    submit_button_confirm = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-dialog')]//button[text()='Submit all and finish']"))
    )
    submit_button_confirm.click()
    
    return True