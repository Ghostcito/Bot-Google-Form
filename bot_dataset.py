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

def leer_csv(respuestas):
    """Lee el archivo CSV y devuelve una lista de diccionarios con las respuestas"""
    respuestas = []
    with open(respuestas, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            respuestas.append(row)
    return respuestas

def mapear_respuestas(respuesta_csv):
    """Mapea las respuestas del CSV al formato esperado por el formulario"""
    return {
        "edad": respuesta_csv["¿Cuál es su edad? "].strip(" años").strip(),
        "frecuencia": respuesta_csv["¿Con qué frecuencia consume barras energéticas? "],
        "motivacion": respuesta_csv["¿Qué lo motiva a consumir barras energéticas?"].split(";"),
        "tipos_barra": respuesta_csv["¿Qué tipos de barra conoce?"],
        "importancia_natural": respuesta_csv["¿Qué tan importante es para usted que una barra energética sea natural? "],
        "conoce_yacon": respuesta_csv["¿Conoce el yacón?"],
        "como_endulzante": "Sí, prefiero yacón" if respuesta_csv["¿Preferiría una barra energética endulzada con yacón en lugar de azúcar refinada o edulcorantes artificiales?"] == "Si" else "No, prefiero azúcar",
        "valora": respuesta_csv["¿Qué valora más al elegir una barra energética?  (Puede marcar más de una opción) "].split(";"),
        "beneficios": respuesta_csv["¿Cuáles son los beneficios que espera obtener al consumir una barra energética?   (Puede marcar más de una opción) "].split(";"),
        "presentacion": respuesta_csv["¿Qué presentación prefiere para consumir una barra energética? "],
        "lugares_venta": respuesta_csv["¿Le gustaría encontrar este tipo de barra en…? (Puede marcar más de una opción) "].split(";"),
        "precio": respuesta_csv[" ¿Cuánto estaría dispuesto a pagar por una barra energética elaborada con ingredientes naturales y endulzada con yacón?  "]
    }

def seleccionar_checkbox(driver, texto_opcion):
    """Función para seleccionar checkboxes en Google Forms"""
    try:
        # Esperar a que la página esté completamente cargada
        time.sleep(1)
        
        # Primero intentamos con el método más común
        try:
            checkbox = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//div[@role='checkbox' and .//span[text()='{texto_opcion}']")
                )
            )
            ActionChains(driver).move_to_element(checkbox).click().perform()
            return
        except:
            pass
        
        # Método alternativo 1
        try:
            label = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//span[text()='{texto_opcion}']/ancestor::div[@role='listitem']")
                )
            )
            checkbox = label.find_element(By.XPATH, ".//div[@role='checkbox']")
            driver.execute_script("arguments[0].scrollIntoView();", checkbox)
            checkbox.click()
            return
        except:
            pass
        
        raise Exception(f"No se pudo encontrar el checkbox para: {texto_opcion}")
        
    except Exception as e:
        print(f"Error al seleccionar checkbox '{texto_opcion}': {str(e)}")
        raise
    
def seleccionar_radio_especifico(driver, texto_pregunta, opcion):
    """Selecciona un radio button específico anclado a una pregunta"""
    try:
        # Estrategia 1: Buscar por data-value exacto dentro del grupo de la pregunta
        xpath = f"//div[contains(text(), '{texto_pregunta}')]/ancestor::div[@role='radiogroup']//div[@data-value='{opcion}']"
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
    except:
        try:
            # Estrategia 2: Buscar por texto visible dentro del grupo
            xpath = f"//div[contains(text(), '{texto_pregunta}')]/ancestor::div[@role='radiogroup']//span[text()='{opcion}']/ancestor::div[@role='radio']"
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        except:
            # Estrategia 3: JavaScript como último recurso
            xpath = f"//div[contains(text(), '{texto_pregunta}')]/ancestor::div[@role='radiogroup']//div[@data-value='{opcion}']"
            elemento = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", elemento)

def enviar_respuesta(respuesta):
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://docs.google.com/forms/d/e/1FAIpQLScPVdlwZ_YHxMA8jsEr5Xe4x23QX6SHaEGkwGeJ-i7vnlXcVQ/viewform?usp=header")

        # Esperar a que cargue el formulario
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@role='list']")))

        # 1. Edad
        edad = respuesta["edad"]
        edad_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='text' or @type='number']"))
        )
        edad_field.clear()
        edad_field.send_keys(edad)

        # 2. Frecuencia de consumo (radio button)
        frecuencia = respuesta["frecuencia"]
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{frecuencia}')]").click()

        # 3. Motivación (SOLO 1 checkbox)
        motivacion = respuesta["motivacion"][0]  # Tomamos la primera opción si hay múltiples
        seleccionar_checkbox(driver, motivacion)

        # 4. Tipos de barra conocidos (radio button)
        tipo_barra = respuesta["tipos_barra"]
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{tipo_barra}')]").click()

        # 5. Importancia de ingredientes naturales (radio button)
        importancia = respuesta["importancia_natural"]
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{importancia}')]").click()

        # 6. Conoce el yacón? (radio button)
        conoce_yacon = respuesta["conoce_yacon"]
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{conoce_yacon}')]").click()

        # 7. Preferiría yacón en lugar de azúcar? (radio button)
        como_endulzante = respuesta["como_endulzante"]
        print(f"Seleccionando opción de endulzante: {como_endulzante}")
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{como_endulzante}')]").click()

        # 8. Qué valora más (SOLO 1 checkbox)
        valor = respuesta["valora"][0]  # Tomamos la primera opción si hay múltiples
        seleccionar_checkbox(driver, valor)

        # 9. Beneficios esperados (SOLO 1 checkbox)
        beneficio = respuesta["beneficios"][0]  # Tomamos la primera opción si hay múltiples
        seleccionar_checkbox(driver, beneficio)

        # 10. Presentación preferida (radio button)
        presentacion = respuesta["presentacion"]
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{presentacion}')]").click()

        # 11. Lugares de venta preferidos (SOLO 1 checkbox)
        lugar = respuesta["lugares_venta"][0]  # Tomamos la primera opción si hay múltiples
        seleccionar_checkbox(driver, lugar)

        # 12. Precio dispuesto a pagar (radio button)
        precio = respuesta["precio"]
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{precio}')]").click()

        # Enviar formulario
        submit = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Enviar']"))
        )
        submit.click()

        print(f"Respuesta enviada - Edad: {edad}, Frecuencia: {frecuencia}")
        time.sleep(2)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()

# Proceso principal adaptado para el formulario PRUEBA con dos preguntas

def enviar_respuesta_simple(respuesta):
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://docs.google.com/forms/d/e/1FAIpQLScPVdlwZ_YHxMA8jsEr5Xe4x23QX6SHaEGkwGeJ-i7vnlXcVQ/viewform?usp=header")

        # Esperar a que cargue el formulario
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@role='list']")))

        # 1. EDAD? (radio button)
        edad = respuesta["EDAD?"]
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{edad}')]").click()

        # 2. QUE PREFIERE? (radio button)
        preferencia = respuesta["QUE PREFIERE?"]
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{preferencia}')]").click()

        # Enviar formulario
        submit = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Enviar']"))
        )
        submit.click()

        print(f"Respuesta enviada - EDAD: {edad}, QUE PREFIERE: {preferencia}")
        time.sleep(2)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()

def leer_csv_y_enviar(nombre_archivo):
    with open(nombre_archivo, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for fila in reader:
            enviar_respuesta_simple(fila)
            time.sleep(3)

if __name__ == "__main__":
    leer_csv_y_enviar("respuestas_prueba.csv")
