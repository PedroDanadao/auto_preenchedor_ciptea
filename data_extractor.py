"""
Data Extraction Module
Handles AI-based text extraction from images and data parsing using Google's Generative AI.
"""

import os
import ast
from pathlib import Path
from brazilcep import get_address_from_cep
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai

# Load environment variables from user's .auto_preenchedor_data folder
env_path = Path.home() / ".auto_preenchedor_data" / ".env"
if env_path.exists():
    load_dotenv(env_path)


def get_image_text(image_path, api_key=None):
    """
    Extract all text from an image using Google's Generative AI.
    
    Args:
        image_path (str): Path to the image file
        api_key (str, optional): Google Generative AI API key. If not provided, will use GOOGLE_API_KEY from environment.
        
    Returns:
        str: Extracted text from the image
    """
    # Use provided API key or get from environment
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY", "")
    
    if not api_key:
        raise ValueError("Google API Key not provided and not found in environment variables. Please configure it using the API Key button.")
    
    image = Image.open(image_path)
    prompt = "Extract all the text in this image and provide it as plain text."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-pro")
    response = model.generate_content([image, prompt])

    print(response.text)
    return response.text


def get_data_from_text(text, api_key=None):
    """
    Extract structured data from text using Google's Generative AI.
    
    Args:
        text (str): Raw text containing user information
        api_key (str, optional): Google Generative AI API key. If not provided, will use GOOGLE_API_KEY from environment.
        
    Returns:
        dict: Dictionary containing extracted user data with keys:
            - nome_do_responsavel
            - nome_do_menor
            - nome_da_mae_do_menor
            - cpf_do_responsavel
            - rg_do_responsavel
            - cpf_do_menor
            - rg_do_menor
            - data_de_nascimento_do_menor
            - endereço
            - cep
            - cids
    """
    # Use provided API key or get from environment
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY", "")
    
    if not api_key:
        raise ValueError("Google API Key not provided and not found in environment variables. Please configure it using the API Key button.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-pro")

    text_input = """
    User Information:
    nome_do_responsavel: maria
    nome_do_menor: joao
    nome_da_mae_do_menor: ana silva
    cpf_do_responsavel: 123.456.789-00
    rg_do_responsavel: 12.345.678-9(se não tiver rg, usar o cpf_do_responsavel)
    cpf_do_menor: 987.654.321-00
    rg_do_menor: 98.765.432-1(se não tiver rg, usar o cpf_do_menor)
    data_de_nascimento_do_menor: DD/MM/YYYY
    endereço: rua abc, 123(só rua e número)
    cep: 12345-678
    cids: [10 F84.0, 11 6A02](podem ser 10 F84.0, 10 F84.1 ... 10 F84.9 ou FA02.0, FA02.1 ... FA02.5, FA02.Y, FA02.Z)
    """

    prompt = f"Extraia um dicionário python com as chaves nome_do_responsavel, nome_do_menor, nome_da_mae_do_menor, cpf_do_responsavel, rg_do_responsavel, cpf_do_menor, rg_do_menor, data_de_nascimento_do_menor, endereço, cep, cid dessa forma:\n\n{text_input}\n\ com base no seguinte texto:\n\n{text}\n\nResponda apenas com uma string que possa ser usada num literal_eval do python para gerar o dicionário."

    response = model.generate_content(prompt)
    extracted_dict_str = response.text.strip()
    extracted_dict_str = extracted_dict_str.split("{")[1].split("}")[0].replace("\n", " ").strip().replace("\\", "")
    extracted_dict_str = "{" + extracted_dict_str + "}"

    # Attempt to parse the string into a dictionary
    try:
        # Use ast.literal_eval for safe evaluation of string representation of Python literals
        extracted_dict = ast.literal_eval(extracted_dict_str)
        print(extracted_dict)

        street_cep = get_street_from_cep(extracted_dict.get("cep", ""))

        if street_cep:
            numero = extracted_dict.get("endereço", "").split(",")[1].strip() if "," in extracted_dict.get("endereço", "") else ""
            full_address = f"{street_cep}, {numero}".strip(", ")
            extracted_dict["endereço"] = full_address
        return extracted_dict
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing dictionary from LLM response: {e}")
        print(f"Raw LLM response: {extracted_dict_str}")
        return None
    

def get_street_from_cep(cep):
    """
    Use the brazilcep library to get the street address from a given CEP.
    """
    try:
        cep = cep.replace("-", "").strip()
        dados_cep = get_address_from_cep(cep)
        return dados_cep.get("street", "")
    except Exception as e:
        print(f"Error fetching street from CEP {cep}: {e}")
        return None
