from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import csv
import sys

# Configuración para evitar errores de Unicode en Windows
sys.stdout.reconfigure(encoding='utf-8')

# Configuración del navegador
options = webdriver.ChromeOptions()
options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option('excludeSwitches', ['enable-logging'])

def parse_questions(filename):
    """Parse the questions and options from the txt file"""
    questions = []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    current_question = None
    current_options = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('☐'):
            if current_question:
                questions.append((current_question, current_options))
            current_question = line
            current_options = []
        elif line.startswith('☐'):
            option = line[1:].strip()
            current_options.append(option)
    if current_question:
        questions.append((current_question, current_options))
    return questions

# Load questions from the file
QUESTIONS = parse_questions("preguntas y respuestas InterviewPro.txt")

def seleccionar_radio_especifico(driver, texto_pregunta, opcion):
    """Selecciona un radio button específico anclado a una pregunta"""
    try:
        # Buscar por texto visible dentro del grupo (más flexible)
        # Normalizar espacios y eliminar caracteres especiales para evitar problemas
        xpath = f"//div[contains(normalize-space(string()), normalize-space('{texto_pregunta}'))]/ancestor::div[@role='radiogroup']//div[@role='radio' and .//span[contains(normalize-space(string()), normalize-space('{opcion}'))]]"
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
    except:
        try:
            # Alternativa: buscar por texto exacto en span dentro del radio
            xpath = f"//div[contains(normalize-space(string()), normalize-space('{texto_pregunta}'))]/ancestor::div[@role='radiogroup']//span[normalize-space(string())=normalize-space('{opcion}')]/ancestor::div[@role='radio']"
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        except:
            # Último recurso: click con JavaScript en el radio que contiene el texto
            xpath = f"//div[contains(normalize-space(string()), normalize-space('{texto_pregunta}'))]/ancestor::div[@role='radiogroup']//div[@role='radio' and .//span[contains(normalize-space(string()), normalize-space('{opcion}'))]]"
            elemento = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", elemento)

def enviar_respuesta(respuesta):
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://docs.google.com/forms/d/e/1FAIpQLSeznE0EpeR-xT3481SwcMQRdeGZ1CBxVc6HuYDppe2E1TkgFg/viewform?usp=header")

        # Esperar a que cargue el formulario
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@role='list']")))

        # Responder a cada pregunta
        for i, (question, options) in enumerate(QUESTIONS):
            choice = respuesta[f'question{i+1}']
            seleccionar_radio_especifico(driver, question, choice)
            print(f"Seleccionado para '{question[:50]}...': {choice}")

        # Enviar formulario
        submit = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Enviar']"))
        )
        submit.click()

        print("Respuesta enviada")
        time.sleep(2)

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if driver:
            driver.quit()

def leer_csv_y_enviar(nombre_archivo):
    with open(nombre_archivo, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for fila in reader:
            enviar_respuesta(fila)
            time.sleep(3)  # Pausa entre envíos

if __name__ == "__main__":
    leer_csv_y_enviar("interviewpro_responses.csv")
