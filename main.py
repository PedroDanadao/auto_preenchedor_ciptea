"""
Auto Preenchedor - Main Module
Automated form filling system that processes images, extracts data, and fills web forms.
"""

import json
import pprint
from image_processor import organize_image_files, create_image_collage
from data_extractor import get_image_text, get_data_from_text
from web_automation import (
    open_new_driver,
    fill_cipteape_form,
    fill_intermunicipal_form,
    attach_intermunicipal_files
)


def process_images_and_extract_data(image_files_dict, person_name):
    """
    Process images, organize them, and extract data from a collage.
    
    Args:
        image_files_dict (dict): Dictionary mapping image types to file paths
        person_name (str): Name of the person for folder organization
        
    Returns:
        tuple: (organized_files dict, extracted_data dict)
    """
    # Organize and convert images
    print(f"Organizing files for {person_name}...")
    organized_files = organize_image_files(image_files_dict, person_name)
    
    print("\nOrganized files:")
    pprint.pprint(organized_files)
    
    # Create collage from specific images for data extraction
    collage_images = [
        image_files_dict.get("cpf_do_menor"),
        image_files_dict.get("cpf_do_responsavel"),
        image_files_dict.get("laudo_medico"),
        image_files_dict.get("comprovante_residencia"),
    ]
    
    # Filter out None values
    collage_images = [img for img in collage_images if img]
    
    if len(collage_images) >= 4:
        collage_path = organized_files.get("cpf_do_menor", "").replace("cpf_do_menor", "documents_collage")
        create_image_collage(collage_images, collage_path, rows=2, cols=2, image_size=(1000, 1000))
        
        # Extract text from collage
        print("\nExtracting text from collage...")
        full_text = get_image_text(collage_path)
        
        # Parse data from text
        print("\nParsing data from extracted text...")
        data = get_data_from_text(full_text)
        
        return organized_files, data
    else:
        print("Warning: Not enough images to create collage. Skipping data extraction.")
        return organized_files, None


def fill_forms_automatically(data, organized_files):
    """
    Open browser and fill all forms automatically.
    
    Args:
        data (dict): Extracted user data
        organized_files (dict): Dictionary of organized file paths
    """
    if not data:
        print("No data available. Cannot fill forms.")
        return
    
    print("\nOpening browser and filling forms...")
    driver = open_new_driver()
    
    try:
        # Fill Cipteape forms
        print("Filling Cipteape primeira via form...")
        fill_cipteape_form(driver, data, organized_files, primeira_via=True)
        
        print("Filling Cipteape segunda via form...")
        fill_cipteape_form(driver, data, organized_files, primeira_via=False)
        
        # Fill intermunicipal form
        print("Filling intermunicipal form...")
        fill_intermunicipal_form(driver, data)
        
        # Attach files
        print("Attaching files to intermunicipal form...")
        attach_intermunicipal_files(driver, organized_files)
        
        print("\n✓ All forms filled successfully!")
        print("\nPlease review the forms in the browser before submitting.")
        
        input("Press Enter to close the browser and end the program...")
        driver.quit()
        
    except Exception as e:
        print(f"\n✗ Error filling forms: {e}")
        print("Browser will remain open for manual inspection.")


def main():
    """
    Main function - Example usage of the auto preenchedor system.
    """
    # Example: Define image files
    image_files_dict = {
        "cpf_do_responsavel": r"C:\Users\Pedro\Desktop\personal\cadastro\cpf_rg_resp.jpg",
        "rg_do_responsavel": r"C:\Users\Pedro\Desktop\personal\cadastro\cpf_rg_resp.jpg",
        "cpf_do_menor": r"C:\Users\Pedro\Desktop\personal\cadastro\cpf_rg.jpg",
        "rg_do_menor": r"C:\Users\Pedro\Desktop\personal\cadastro\cpf_rg.jpg",
        "laudo_medico": r"C:\Users\Pedro\Desktop\personal\cadastro\laudo.jpg",
        "comprovante_residencia": r"C:\Users\Pedro\Desktop\personal\cadastro\residencia.jpg",
        "foto_3x4": r"C:\Users\Pedro\Desktop\personal\cadastro\3x4.jpg",
    }
    
    person_name = "José De Açunsão"
    
    # Process images and extract data
    organized_files, data = process_images_and_extract_data(image_files_dict, person_name)
    
    # Optionally: Save extracted data for later use
    if data:
        with open("extracted_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("\n✓ Data saved to extracted_data.json")
    
    # Fill forms (uncomment to run)
    # fill_forms_automatically(data, organized_files)


def load_and_fill_from_saved_data():
    """
    Alternative workflow: Load previously extracted data and fill forms.
    Useful for testing or when data extraction was done separately.
    """
    # Load saved data
    with open("data_example.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Define organized files manually or load from a saved configuration
    organized_files = {
        "rg_do_responsavel_pdf": r"C:\Users\Pedro\Desktop\personal\cadastro\cpf_rg_resp.pdf",
        "foto_3x4": r"C:\Users\Pedro\Desktop\personal\cadastro\3x4.jpg",
        "cpf_rg_pdf": r"C:\Users\Pedro\Desktop\personal\cadastro\cpf_rg.pdf",
    }
    
    # Fill forms
    fill_forms_automatically(data, organized_files)


if __name__ == "__main__":
    # Run the main workflow
    main()
    
    # Alternative: Use previously saved data
    # load_and_fill_from_saved_data()
