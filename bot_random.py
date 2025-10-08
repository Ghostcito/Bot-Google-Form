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

# Configuración del navegador (moved inside function to avoid scope issues)

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

def seleccionar_aleatoria(opciones, max_selecciones=None):
    """Selecciona 1 o múltiples opciones aleatorias"""
    if max_selecciones and len(opciones) > 1:
        num = random.randint(1, min(max_selecciones, len(opciones)))
        return " | ".join(random.sample(opciones, num))
    return random.choice(opciones)

def verificar_y_estabilizar_seleccion(driver, radio, texto_opcion):
    """Verifica si la selección se mantiene estable y la estabiliza si es necesario"""
    for intento in range(3):  # Máximo 3 intentos
        time.sleep(0.5)  # Esperar un poco
        if radio.get_attribute("aria-checked") == "true":
            print(f"✅ Radio seleccionado y estabilizado: '{texto_opcion}'")
            time.sleep(1)  # Esperar más para consolidar
            return True
        else:
            # Intentar hacer clic en el label asociado si existe
            try:
                label = radio.find_element(By.XPATH, ".//ancestor::label | .//following-sibling::label | .//preceding-sibling::label")
                if label:
                    label.click()
                    time.sleep(0.3)
                    if radio.get_attribute("aria-checked") == "true":
                        print(f"✅ Radio estabilizado con label: '{texto_opcion}'")
                        time.sleep(1)
                        return True
            except:
                pass
            # Si no, hacer clic en el radio nuevamente
            radio.click()
            time.sleep(0.3)
    print(f"❌ No se pudo estabilizar la selección para: '{texto_opcion}'")
    return False
    
def seleccionar_radio(driver, texto_opcion):
    """Función para seleccionar radio buttons en Google Forms"""
    try:
        # Estrategias de búsqueda priorizadas
        estrategias = [
            # 1. Por data-value (atributo más confiable)
            f"//div[@role='radio' and @data-value='{texto_opcion}']",

            # 2. Por estructura completa con clases específicas
            f"//div[contains(@class, 'uVccjd') and @data-value='{texto_opcion}']",

            # 3. Por texto exacto en el span dentro del radio
            f"//div[@role='radio']//span[normalize-space()='{texto_opcion}']/ancestor::div[@role='radio']",

            # 4. Por aria-label
            f"//div[@role='radio' and @aria-label='{texto_opcion}']",

            # 5. Por texto en el label contenedor
            f"//label[.//text()='{texto_opcion}']/ancestor::div[@role='radio']",

            # 6. Búsqueda por texto parcial (último recurso)
            f"//div[@role='radio']//*[contains(text(), '{texto_opcion}')]"
        ]

        for xpath in estrategias:
            try:
                # Esperar a que el elemento esté presente
                radio = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )

                # Scroll suave al centro de la pantalla
                driver.execute_script("""
                    arguments[0].scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'center'
                    });
                """, radio)

                # Esperar a que sea clickable
                radio = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )

                # Verificar estado actual del radio
                estado_actual = radio.get_attribute("aria-checked")

                if estado_actual != "true":
                    # Intentar click normal primero
                    try:
                        ActionChains(driver).move_to_element(radio).pause(0.2).click().perform()
                        time.sleep(0.3)  # Esperar a que se actualice el DOM
                    except:
                        # Si falla, usar JavaScript click
                        driver.execute_script("arguments[0].click();", radio)
                        time.sleep(0.3)  # Esperar a que se actualice el DOM
                    # Verificar y estabilizar la selección
                    if verificar_y_estabilizar_seleccion(driver, radio, texto_opcion):
                        return True
                    else:
                        # Segundo intento con click directo
                        radio.click()
                        time.sleep(0.5)  # Esperar después del segundo click
                        if verificar_y_estabilizar_seleccion(driver, radio, texto_opcion):
                            return True
                else:
                    print(f"🔷 Radio ya estaba seleccionado: '{texto_opcion}'")
                    return True

            except Exception:
                continue  # Intentar con la siguiente estrategia

        # Si ninguna estrategia funcionó
        print(f"❌ No se pudo encontrar el radio para: '{texto_opcion}'")
        print("Probando búsqueda exhaustiva...")

        # Último intento: buscar todos los radios y comparar textos
        try:
            radios = driver.find_elements(By.XPATH, "//div[@role='radio']")
            for r in radios:
                try:
                    if texto_opcion.lower() in r.text.lower():
                        driver.execute_script("arguments[0].scrollIntoView();", r)
                        r.click()
                        print(f"✅ [Búsqueda exhaustiva] Seleccionado: '{texto_opcion}'")
                        return True
                except:
                    continue
        except Exception as e:
            print(f"Error en búsqueda exhaustiva: {str(e)}")

        print(f"🔥 No se pudo seleccionar el radio: '{texto_opcion}'")
        return False

    except Exception as e:
        print(f"Error grave al seleccionar radio: {str(e)}")
        return False
    

def enviar_respuesta():
    # Configuración del navegador
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://docs.google.com/forms/d/e/1FAIpQLSc5McoC3j1rmr3wY9r8PtW2QPZggwnhVEgd346rNCrEpDsQ0Q/viewform?usp=header")

        # Esperar a que cargue el formulario
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@role='list']")))
        print("Formulario cargado, comenzando a responder...")

        # Responder a cada pregunta
        for question, options in QUESTIONS:
            choice = random.choice(options)
            print(f"Intentando seleccionar para '{question}': {choice}")
            try:
                seleccionar_radio(driver, choice)
                print(f"Seleccionado para '{question}': {choice}")
                time.sleep(0.5)  # Pausa adicional entre selecciones para estabilidad
            except Exception as e:
                print(f"Error al seleccionar para '{question}': {str(e)}")
                continue

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

# Enviar 20 respuestas
for i in range(20):
    enviar_respuesta()
    time.sleep(3)  # Pausa entre envíos

print("🎉 Proceso completado!")
