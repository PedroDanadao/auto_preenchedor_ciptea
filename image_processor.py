"""
Image Processing Module
Handles image file organization, PDF conversion, and collage creation.
"""

import os
from pathlib import Path
from PIL import Image
import img2pdf
import unidecode


# User data folder path
DATA_DIR = Path.home() / ".auto_preenchedor_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def organize_image_files(image_paths_dict, folder_name):
    """
    Make a copy of the images in image_paths_dict into the user's .auto_preenchedor_data folder,
    and create PDF files from them.
    
    Args:
        image_paths_dict (dict): Dictionary mapping image names to their file paths
        folder_name (str): Name of the folder to organize files into
        
    Returns:
        dict: Dictionary mapping image names to their new organized paths
    """
    organized_image_paths = {}
    image_names_to_convert_to_pdf = [
        "cpf_do_responsavel",
        "rg_do_responsavel",
        "cpf_do_menor",
        "rg_do_menor",
        "laudo_medico",
        "comprovante_residencia",
    ]

    # Clean the folder_name first, removing any bad characters from it and converting spaces to underscores
    folder_name = unidecode.unidecode(folder_name)
    folder_name = folder_name.strip().lower().replace(" ", "_")
    folder_name = folder_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_")

    folder_to_save = DATA_DIR / folder_name
    folder_to_save.mkdir(parents=True, exist_ok=True)

    # Clean up existing files in the folder
    for already_existing_file in folder_to_save.iterdir():
        already_existing_file.unlink()

    for image_name, image_path in image_paths_dict.items():
        if not os.path.isfile(image_path):
            print(f"Warning: File {image_path} does not exist. Skipping.")
            continue

        # Copy image to folder_to_save
        dest_image_path = folder_to_save / f"{image_name}{os.path.splitext(image_path)[1]}"
        with open(image_path, "rb") as src_file:
            with open(dest_image_path, "wb") as dest_file:
                dest_file.write(src_file.read())

        organized_image_paths[image_name] = str(dest_image_path)

        # Convert specific images to PDF
        if image_name in image_names_to_convert_to_pdf:
            pdf_path = dest_image_path.with_suffix(".pdf")
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(str(dest_image_path)))
            organized_image_paths[f"{image_name}_pdf"] = str(pdf_path)

    return organized_image_paths


def create_image_collage(image_paths, output_path, rows, cols, image_size=(200, 200)):
    """
    Creates a collage from a list of image paths.

    Args:
        image_paths (list): A list of file paths to the images
        output_path (str): The path to save the resulting collage image
        rows (int): The number of rows in the collage grid
        cols (int): The number of columns in the collage grid
        image_size (tuple, optional): The target size (width, height) for each image in the collage.
                                      Defaults to (200, 200)
    """
    if len(image_paths) != rows * cols:
        print("Warning: The number of images does not match the specified grid dimensions.")
        # This implementation will leave blank spaces if there are fewer images
        # or ignore extra images if there are more.

    # Calculate collage dimensions
    collage_width = cols * image_size[0]
    collage_height = rows * image_size[1]

    # Create a new blank image for the collage with a white background
    collage = Image.new('RGB', (collage_width, collage_height), color='white')

    # Iterate through the grid and paste images
    image_index = 0
    for r in range(rows):
        for c in range(cols):
            if image_index < len(image_paths):
                # Calculate the position for the current image
                x_offset = c * image_size[0]
                y_offset = r * image_size[1]

                try:
                    # Open and resize the image
                    img = Image.open(image_paths[image_index])
                    img = img.resize(image_size, Image.Resampling.LANCZOS)  # Use a high-quality resizer
                    
                    # Paste the image onto the collage
                    collage.paste(img, (x_offset, y_offset))

                except FileNotFoundError:
                    print(f"Error: Image not found at {image_paths[image_index]}. Skipping.")
                except Exception as e:
                    print(f"Error processing image {image_paths[image_index]}: {e}. Skipping.")
                
                image_index += 1

    # Save the final collage
    try:
        collage.save(output_path)
        print(f"Collage saved successfully to {output_path}")
    except Exception as e:
        print(f"Error saving collage: {e}")


def convert_image_to_pdf(image_path, output_pdf_path):
    """
    Converts a single image to a PDF file.
    
    Args:
        image_path (str): Path to the source image
        output_pdf_path (str): Path where the PDF should be saved
    """
    try:
        with open(output_pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_path))
        print(f"PDF saved successfully to {output_pdf_path}")
    except Exception as e:
        print(f"Error creating PDF for {image_path}: {e}")


def convert_images_to_pdfs(image_paths):
    """
    Converts a list of images to a list of PDF files.
    
    Args:
        image_paths (list): List of paths to image files
        
    Returns:
        list: List of paths to the created PDF files
    """
    pdf_paths = []
    for image_path in image_paths:
        pdf_path = image_path.replace(".jpg", ".pdf").replace(".png", ".pdf")
        convert_image_to_pdf(image_path, pdf_path)
        pdf_paths.append(pdf_path)
    return pdf_paths
