from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

import sys

# Configuración para evitar errores de Unicode en Windows
sys.stdout.reconfigure(encoding='utf-8')

# Configuración del navegador
options = webdriver.ChromeOptions()
options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option('excludeSwitches', ['enable-logging'])

# Datos basados en el Excel (respuestas posibles para cada pregunta)
RESPUESTAS = {
    "edad": lambda: str(random.randint(20, 28)),
    "frecuencia": ["Nunca","Rara vez", "Una vez al mes", "Una vez a la semana"],
    "motivacion": [
        "Obtener energía rápidamente",
        "Saciar el hambre", 
        "El sabor",
        "La practicidad", 
        "Realizar ejercicio o deporte",
    ],
    "tipos_barra": [
        "Barra proteica (ingredientes como proteínas, frutos secos, etc.)",
        "Barra con tubérculos (ingredientes como yacón, camote, etc.)",
        "Barra energética comercial (como las de supermercado)"        
    ],
    "importancia_natural": ["Muy importante","Importante","Nada importante", "Poco importante" ],
    "conoce_yacon": ["Sí", "No"],
    "prefiere_yacon": ["Sí", "No"],
    "valora": [
        "El sabor",
        "Los ingredientes naturales",        
        "El precio",
        "El valor nutricional",
        "Una marca reconocida",
        "Beneficios para la salud (mejora digestión, energía sostenida, etc.)"
    ],
    "beneficios": [
        "Sentirse con más energía",
        "Mejorar el rendimiento físico",
        "Mejorar la digestión",
        "Controlar el apetito"
    ],
    "presentacion": ["Empaque individual", "Caja con varias barras", "No tengo preferencia"],
    "lugares_venta": [
        "Supermercados",
        "Tiendas naturales",
        "Farmacias",
        "Gimnasios",
        "En línea (e-commerce)"
    ],
    "precio": ["Menos de S/2", "Entre S/2 y S/4", "Más de S/4", "Depende del tamaño y calidad"]
}

def seleccionar_aleatoria(opciones, max_selecciones=None):
    """Selecciona 1 o múltiples opciones aleatorias"""
    if max_selecciones and len(opciones) > 1:
        num = random.randint(1, min(max_selecciones, len(opciones)))
        return " | ".join(random.sample(opciones, num))
    return random.choice(opciones)
    
def seleccionar_checkbox(driver, texto_opcion):
    """Función mejorada para seleccionar checkboxes en Google Forms"""
    try:
        # Esperar a que la página esté completamente cargada
        time.sleep(1)
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

def seleccionar_radio(driver, texto_opcion):
    
    try:
        # Esperar un breve momento para asegurar que el elemento esté listo
        time.sleep(0.5)
        
        # Intentar con el método tradicional primero
        try:
            element = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//div[@role='radio' and .//span[text()='{texto_opcion}']]")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
            return
        except:
            pass
        
        # Método alternativo si falla el primero
        try:
            labels = driver.find_elements(By.XPATH, f"//span[contains(text(), '{texto_opcion}')]")
            for label in labels:
                try:
                    radio = label.find_element(By.XPATH, "./ancestor::div[@role='radio']")
                    driver.execute_script("arguments[0].scrollIntoView();", radio)
                    radio.click()
                    return
                except:
                    continue
        except:
            pass
        
        raise Exception(f"No se pudo encontrar el radio button para: {texto_opcion}")
        
    except Exception as e:
        print(f"Error al seleccionar radio button '{texto_opcion}': {str(e)}")
        raise

def enviar_respuesta():
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://docs.google.com/forms/d/e/1FAIpQLScw-6dLWwXk6jCm31IELgYYRga9ca_IfRbRbnpnXOQAOVrVAQ/viewform?usp=dialog")

        # Esperar a que cargue el formulario
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@role='list']")))

        # 1. Edad - Solución mejorada
        edad = RESPUESTAS["edad"]()
        edad_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='text' or @type='number']"))
        )
        edad_field.clear()
        edad_field.send_keys(edad)

        # 2. Frecuencia de consumo
        frecuencia = seleccionar_aleatoria(RESPUESTAS["frecuencia"])
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{frecuencia}')]").click()

        # 3. Motivación (selección múltiple)
        motivaciones = seleccionar_aleatoria(RESPUESTAS["motivacion"], max_selecciones=3)
        for mot in motivaciones.split(" | "):
            seleccionar_checkbox(driver, mot)

        # 4. Tipos de barra conocidos
        tipo_barra = seleccionar_aleatoria(RESPUESTAS["tipos_barra"])
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{tipo_barra}')]").click()

        # 5. Importancia de ingredientes naturales
        importancia = seleccionar_aleatoria(RESPUESTAS["importancia_natural"])
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{importancia}')]").click()

        # 6. Conoce el yacón?
        conoce_yacon = seleccionar_aleatoria(RESPUESTAS["conoce_yacon"])
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{conoce_yacon}')]").click()

        # 7. Preferiría yacón en lugar de azúcar?
        prefiere_yacon = seleccionar_aleatoria(RESPUESTAS["prefiere_yacon"])
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{prefiere_yacon}')]").click()

        # 8. Qué valora más (selección múltiple)
        valores = seleccionar_aleatoria(RESPUESTAS["valora"], max_selecciones=4)
        for mot in valores.split(" | "):
            seleccionar_checkbox(driver, mot)

        # 9. Beneficios esperados (selección múltiple)
        beneficios = seleccionar_aleatoria(RESPUESTAS["beneficios"], max_selecciones=3)
        for mot in beneficios.split(" | "):
            seleccionar_checkbox(driver, mot)

        # 10. Presentación preferida
        presentacion = seleccionar_aleatoria(RESPUESTAS["presentacion"])
        driver.find_element(By.XPATH, f"//div[contains(@data-value, '{presentacion}')]").click()

        # 11. Lugares de venta preferidos (selección múltiple)
        lugares = seleccionar_aleatoria(RESPUESTAS["lugares_venta"], max_selecciones=3)
        for mot in lugares.split(" | "):
            seleccionar_checkbox(driver, mot)

        # 12. Precio dispuesto a pagar
        precio = seleccionar_aleatoria(RESPUESTAS["precio"])
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

# Enviar 5 respuestas aleatorias
for i in range(5):
    enviar_respuesta()
    time.sleep(3)  # Pausa entre envíos

print("🎉 Proceso completado!")

respuestas_csv = leer_csv("respuestas.csv")