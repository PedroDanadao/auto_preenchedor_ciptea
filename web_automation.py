"""
Web Automation Module
Handles all Selenium-based web automation for filling forms on various websites.
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


# CID options available for selection
CID_OPTIONS = [
    "cid10_F84_0",
    "cid10_F84_1",
    "cid10_F84_2",
    "cid10_F84_3",
    "cid10_F84_4",
    "cid10_F84_5",
    "cid10_F84_6",
    "cid10_F84_7",
    "cid10_F84_8",
    "cid10_F84_9",
    
    "cid11_6A02_0",
    "cid11_6A02_1",
    "cid11_6A02_2",
    "cid11_6A02_3",
    "cid11_6A02_4",
    "cid11_6A02_5",
    "cid11_6A02_Y",
    "cid11_6A02_Z",
]


def open_new_driver():
    """
    Initialize a new Chrome WebDriver with detached mode.
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def access_url_in_new_tab(driver, url):
    """
    Open a new tab and navigate to the specified URL.
    
    Args:
        driver: Selenium WebDriver instance
        url (str): URL to navigate to
    """
    driver.switch_to.new_window('tab')
    driver.get(url)


def get_best_guess_cids(cids):
    """
    Determine the best CID code from a list of CID codes.
    
    Args:
        cids (list): List of CID codes (e.g., ['10 F84.0', '11 6A02'])
        
    Returns:
        list: CIDs that best match the available options
    """
    cids_to_use = []
    for cid in cids:
        if cid.startswith('10') or cid.startswith("11"):
            cids_to_use.append(cid)

    if not cids_to_use:
        return []
    
    valid_cids = []
    
    for cid_to_use in cids_to_use:
        if cid_to_use.startswith('10'):
            if "84" not in cid_to_use:
                continue
            
            if '.' not in cid_to_use:
                cid_to_use += ".0"

            last_digit = cid_to_use.split('.')[1]

            try:
                last_digit_int = int(last_digit)
                if 0 <= last_digit_int <= 9:
                    valid_cids.append(CID_OPTIONS[last_digit_int])
            except ValueError:
                valid_cids.append(CID_OPTIONS[0])

        elif cid_to_use.startswith('11'):
            if "A02" not in cid_to_use:
                continue
            
            if '.' not in cid_to_use:
                cid_to_use += ".0"

            last_part = cid_to_use.split('.')[1]

            if last_part in ['0', '1', '2', '3', '4', '5']:
                valid_cids.append(CID_OPTIONS[10 + int(last_part)])
            elif last_part.upper() == 'Y':
                valid_cids.append(CID_OPTIONS[16])
            elif last_part.upper() == 'Z':
                valid_cids.append(CID_OPTIONS[17])

    return list(set(valid_cids)) if valid_cids else []


def fill_cipteape_form(driver, data, file_paths, primeira_via=True):
    """
    Fill out the Cipteape form (either first or second via).
    
    Args:
        driver: Selenium WebDriver instance
        data (dict): Dictionary containing form data
        file_paths (dict): Dictionary containing paths to required files
        primeira_via (bool): If True, fill first via form; if False, fill second via form
    """
    if primeira_via:
        access_url_in_new_tab(driver, "https://cipteape.com.br/gestao/FormularioSolicitacao/Cadastro")
    else:
        access_url_in_new_tab(driver, "https://cipteape.com.br/gestao/FormularioSolicitacao/SegundaVia")

    wait = WebDriverWait(driver, 10)

    # Fill out the form fields using the data dictionary
    nome_menor_field = wait.until(EC.presence_of_element_located((By.NAME, "NomeBeneficiario")))
    nome_menor_field.send_keys(data.get("nome_do_menor", ""))

    cpf_menor_field = driver.find_element(By.NAME, "CpfBeneficiario")
    cpf_menor_field.send_keys(data.get("cpf_do_responsavel", ""))

    rg_menor_field = driver.find_element(By.NAME, "RgfBeneficiario")
    rg_menor_field.send_keys(data.get("rg_do_menor", ""))

    data_de_nascimento = data.get("data_de_nascimento_do_menor", "01/01/2010")
    data_de_nascimento_field = driver.find_element(By.NAME, "NascimentoBeneficiario")
    data_de_nascimento_field.clear()
    data_de_nascimento_field.send_keys(data_de_nascimento)

    email_field = driver.find_element(By.NAME, "EmailBeneficiario")
    email_field.send_keys(data.get("email", "test_email.com"))

    telefone_field = driver.find_element(By.NAME, "TelefoneBeneficiario")
    telefone_field.send_keys(data.get("telefone", "123456789"))

    cep_field = driver.find_element(By.NAME, "CepBeneficiario")
    cep_field.send_keys(data.get("cep", "12345-678"))

    endereco = data.get("endereço", "")
    endereco = endereco.replace(", ", " N ")
    endereco_field = driver.find_element(By.NAME, "EnderecoBeneficiario")
    endereco_field.send_keys(endereco)

    cidade_dropdown = driver.find_element(By.NAME, "CidadeBeneficiario")
    cidade_dropdown.send_keys(data.get("cidade", "RECIFE"))

    # Handle CID selection
    cids = data.get("cids", ["10:F84.0"])

    cids_to_use = get_best_guess_cids(cids)

    for cid_to_use in sorted(cids_to_use):
        cid_dropdown = driver.find_element(By.NAME, "cidSelect")
        if cid_to_use.startswith('cid10'):
            cid_dropdown.send_keys("CIDs 10 (10ª Revisão)")
        else:
            cid_dropdown.send_keys("CIDs 11 (11ª Revisão)")

        time.sleep(1)  # Wait for the dropdown to update based on selection
        cid_checkbox = driver.find_element(By.ID, cid_to_use)
        cid_checkbox.click()

    nome_do_responsavel_field = driver.find_element(By.NAME, "NomeResponsavel")
    nome_do_responsavel_field.send_keys(data.get("nome_do_responsavel", ""))

    cpf_responsavel_field = driver.find_element(By.NAME, "CpfResponsavel")
    cpf_responsavel_field.send_keys(data.get("cpf_do_responsavel", ""))

    rg_responsavel_field = driver.find_element(By.NAME, "RgResponsavel")
    rg_responsavel_field.send_keys(data.get("rg_do_responsavel", ""))

    # Upload files
    rg_resp_file_input = driver.find_element(By.ID, "idRImagemRg")
    rg_resp_file_input.send_keys(file_paths.get("rg_do_responsavel_pdf", ""))

    cpf_resp_file_input = driver.find_element(By.ID, "idRImagemCpf")
    cpf_resp_file_input.send_keys(file_paths.get("cpf_do_responsavel_pdf", ""))

    rg_benef_file_input = driver.find_element(By.ID, "idBImagemRg")
    rg_benef_file_input.send_keys(file_paths.get("rg_do_menor_pdf", ""))

    cpf_benef_file_input = driver.find_element(By.ID, "idBImagemCpf")
    cpf_benef_file_input.send_keys(file_paths.get("cpf_do_menor_pdf", ""))

    laudo_medico_file_input = driver.find_element(By.ID, "idImagemLaudoMedico")
    laudo_medico_file_input.send_keys(file_paths.get("laudo_medico_pdf", ""))

    residencia_file_input = driver.find_element(By.ID, "idImagemComprovanteResidencia")
    residencia_file_input.send_keys(file_paths.get("comprovante_residencia_pdf", ""))

    # Must be last due to image resizing
    imagem_3x4_file_input = driver.find_element(By.ID, "idImagemFoto")
    imagem_3x4_file_input.send_keys(file_paths.get("foto_3x4", ""))


def fill_intermunicipal_form(driver, data):
    """
    Fill out the PE Livre Acesso Intermunicipal form.
    
    Args:
        driver: Selenium WebDriver instance
        data (dict): Dictionary containing form data
    """
    access_url_in_new_tab(driver, "https://www.sjdh.pe.gov.br/cadastro-pe-livre-acesso-intermunicipal")

    wait = WebDriverWait(driver, 10)

    # Fill out the form fields using the data dictionary
    nome_resp_field = wait.until(EC.presence_of_element_located((By.NAME, "wpforms[fields][2]")))
    nome_resp_field.send_keys(data.get("nome_da_mae_do_menor", ""))

    nome_menor_field = driver.find_element(By.NAME, "wpforms[fields][1]")
    nome_menor_field.send_keys(data.get("nome_do_menor", ""))

    cpf_menor_field = driver.find_element(By.NAME, "wpforms[fields][22]")
    cpf_menor_field.send_keys(data.get("cpf_do_menor", ""))

    rg_menor_field = driver.find_element(By.NAME, "wpforms[fields][4]")
    rg_menor_field.send_keys(data.get("rg_do_menor", ""))

    # Parse and fill birth date
    data_de_nascimento = data.get("data_de_nascimento_do_menor", "01/01/2010")
    dia_de_nascimento = data_de_nascimento.split("/")[0]
    mes_de_nascimento = data_de_nascimento.split("/")[1]
    ano_de_nascimento = data_de_nascimento.split("/")[2]

    # Remove leading zeros
    if dia_de_nascimento.startswith("0"):
        dia_de_nascimento = dia_de_nascimento[1:]
    if mes_de_nascimento.startswith("0"):
        mes_de_nascimento = mes_de_nascimento[1:]

    dia_de_nascimento_field = driver.find_element(By.NAME, "wpforms[fields][5][date][d]")
    dia_de_nascimento_field.send_keys(dia_de_nascimento)

    mes_de_nascimento_field = driver.find_element(By.NAME, "wpforms[fields][5][date][m]")
    mes_de_nascimento_field.send_keys(mes_de_nascimento)

    ano_de_nascimento_field = driver.find_element(By.NAME, "wpforms[fields][5][date][y]")
    ano_de_nascimento_field.send_keys(ano_de_nascimento)

    # Fill address fields
    endereco = data.get("endereço", "")
    endereco = endereco.replace(", ", " N ")
    endereco_field = driver.find_element(By.NAME, "wpforms[fields][32][address1]")
    endereco_field.send_keys(endereco)

    cidade_field = driver.find_element(By.NAME, "wpforms[fields][32][city]")
    cidade_field.send_keys("Recife")

    estado_field = driver.find_element(By.NAME, "wpforms[fields][32][state]")
    estado_field.send_keys("Pernambuco")

    cep_field = driver.find_element(By.NAME, "wpforms[fields][32][postal]")
    cep_field.send_keys(data.get("cep", ""))

    telefone_field = driver.find_element(By.NAME, "wpforms[fields][30]")
    telefone_field.send_keys(data.get("telefone", ""))

    email_field = driver.find_element(By.NAME, "wpforms[fields][9]")
    email_field.send_keys(data.get("email", ""))

    # Handle cookie banner
    try:
        cookie_accept_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cli-plugin-button")))
        cookie_accept_button.click()
        time.sleep(1)  # Wait for banner to disappear
    except Exception as e:
        print(f"Cookie banner not found or already dismissed: {e}")

    # Click the radio button for disability type
    radio_field = driver.find_element(By.ID, "wpforms-8767-field_6_3")
    driver.execute_script("arguments[0].scrollIntoView(true);", radio_field)
    time.sleep(0.5)
    radio_field.click()


def attach_intermunicipal_files(driver, file_paths_dict, use_vem=False):
    """
    Attach required files to the intermunicipal form.
    
    Args:
        driver: Selenium WebDriver instance
        file_paths_dict (dict): Dictionary containing paths to files to attach
    """
    wait = WebDriverWait(driver, 10)

    def attach_file(file_path, element_name):
        if not file_path:
            return
        
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}. Skipping attachment for {element_name}.")
            return
        
        file_input = wait.until(EC.presence_of_element_located((By.NAME, element_name)))
        file_input.send_keys(file_path)

    rg_menor_file_path = file_paths_dict.get("rg_menor_pdf", "")
    attach_file(rg_menor_file_path, "wpforms_8767_10")

    cpf_menor_file_path = file_paths_dict.get("cpf_menor_pdf", "")
    attach_file(cpf_menor_file_path, "wpforms_8767_11")

    residencia_file_path = file_paths_dict.get("comprovante_residencia_pdf", "")
    attach_file(residencia_file_path, "wpforms_8767_12")

    foto_3x4_file_path = file_paths_dict.get("foto_3x4", "")
    attach_file(foto_3x4_file_path, "wpforms_8767_7")

    if not use_vem:
        laudo_medico_file_path = file_paths_dict.get("laudo_medico_pdf", "")
        attach_file(laudo_medico_file_path, "wpforms_8767_27")
    else:
        sim_radial_button = wait.until(EC.presence_of_element_located((By.ID, "wpforms-8767-field_28_1")))
        sim_radial_button.click()
        time.sleep(0.5)
        vem_file_path = file_paths_dict.get("vem_jpg", "")
        attach_file(vem_file_path, "wpforms_8767_29")

    rg_responsavel_file_path = file_paths_dict.get("rg_do_responsavel_pdf", "")
    attach_file(rg_responsavel_file_path, "wpforms_8767_15")

    cpf_responsavel_file_path = file_paths_dict.get("cpf_do_responsavel_pdf", "")
    attach_file(cpf_responsavel_file_path, "wpforms_8767_16")
