from ReadWriteMemory import ReadWriteMemory
import PySimpleGUI as sg
import time
import keyboard
import os
import threading
import requests
import zipfile
import shutil

current_version = '1.1.0'

def update_program():
    # URL del repositorio de GitHub
    repo_url = 'https://github.com/WizGery/WizSacred'

    # Obtener información del último lanzamiento del repositorio
    releases_url = f'{repo_url}/releases/latest'
    response = requests.get(releases_url)
    if response.status_code == 200:
        latest_release = response.json()
        latest_version = latest_release['tag_name']

        # Comparar la versión actual con la última versión disponible
        if current_version < latest_version:
            print(f'Nueva versión disponible: {latest_version}')
            assets = latest_release['assets']

            # Descargar y extraer los archivos actualizados
            for asset in assets:
                asset_url = asset['browser_download_url']
                response = requests.get(asset_url, stream=True)
                if response.status_code == 200:
                    with open(asset['name'], 'wb') as file:
                        response.raw.decode_content = True
                        shutil.copyfileobj(response.raw, file)

                    # Extraer el archivo ZIP
                    with zipfile.ZipFile(asset['name'], 'r') as zip_ref:
                        zip_ref.extractall()

                    # Limpiar los archivos descargados
                    os.remove(asset['name'])

            print('Actualización completada.')
        else:
            print('El programa está actualizado.')
    else:
        print('No se pudo obtener información de actualización.')

def clear_console():
    os.system('cls')

health_max = 0
health_percentage = 0

base_address = 0x00400000
static_address_offset = 0x006D5C40
pointer_static_address = base_address + static_address_offset
health_offsets = (0x04, 0x04, 0x3AC, 0x4D8)

rwm = ReadWriteMemory()
process = rwm.get_process_by_name("Sacred.exe")
process.open()
health_pointer = process.get_pointer(pointer_static_address, offsets=health_offsets)

# Definir la interfaz gráfica
layout = [
    [sg.Checkbox('Auto Heal', key='-AUTOHEAL-', enable_events=True)],
    [sg.Text('Porcentaje de vida para el AUTOHEAL:')],
    [sg.Slider(range=(0, 100), default_value=25, orientation='h', key='-PERCENTAGE-', enable_events=True)],
    [sg.Checkbox('GODMODE', key='-GODMODE-', enable_events=True)],
    [sg.Button('Salir')]
]

# Crear la ventana
window = sg.Window('WizSacred', layout)

def health(valor):
    health = process.read(health_pointer)
    global health_max
    if health == 9999:
        health_max = 100
    elif health >= health_max:
        health_max = health
    health_percentage = (health*100) / health_max

    if valor == 'max_hp':
        return health_max
    elif valor == 'hp':
        return health
    elif valor == 'hp_percentage':
        return health_percentage
    else:
        return None

def printer_test():
    clear_console()
    print('Vida actual: '+str(health('hp')))
    print('Vida máxima: '+str(health('max_hp')))
    print('Porcentaje vida: '+str(health('hp_percentage'))+' %')

# Función que se ejecuta en un hilo separado para la actualización de la consola
def godmode():
    while True:
        if god_mode_active:
            process.write(health_pointer, 9999)
        time.sleep(0.1)

# Crear y ejecutar el hilo para la actualización de la consola
godmode_thread = threading.Thread(target=godmode)
godmode_thread.daemon = True
godmode_thread.start()

# Variable para indicar si Auto Heal está activado
auto_heal_active = False
god_mode_active = False

# Variable para almacenar el porcentaje de vida para el AUTOHEAL
auto_heal_percentage = 25

# Función que se ejecuta en un hilo separado para Auto Heal
def auto_heal_thread():
    global auto_heal_active
    global auto_heal_percentage

    while True:
        if auto_heal_active:
            # Obtener el valor actual de hp_percentage
            hp_percentage = health('hp_percentage')

            # Verificar si hp_percentage es igual o inferior a auto_heal_percentage
            if hp_percentage is not None and hp_percentage <= auto_heal_percentage:
                # Simular la pulsación de la tecla "space"
                keyboard.press('space')
                time.sleep(.05)
                keyboard.release('space')

        time.sleep(0.1)

# Crear y ejecutar el hilo para Auto Heal
auto_heal_thread = threading.Thread(target=auto_heal_thread)
auto_heal_thread.daemon = True
auto_heal_thread.start()

# Bucle principal de la interfaz gráfica
while True:
    printer_test()
    event, values = window.read(timeout=100)  # Agregar timeout para evitar bloqueo
    if event == sg.WINDOW_CLOSED or event == 'Salir':
        break
    # Verificar si la casilla de Auto Heal está marcada
    if event == '-AUTOHEAL-':
        auto_heal_active = values['-AUTOHEAL-']
        if auto_heal_active:
            print("Auto Heal activado")
        else:
            print("Auto Heal desactivado")
    if event == '-GODMODE-':
        god_mode_active = values['-GODMODE-']
        if god_mode_active:
            print("God Mode activado")
        else:
            print("God Mode desactivado")
    # Verificar si el porcentaje de vida para el AUTOHEAL ha cambiado
    if event == '-PERCENTAGE-':
        auto_heal_percentage = values['-PERCENTAGE-']

# Cerrar la ventana al salir
window.close()
