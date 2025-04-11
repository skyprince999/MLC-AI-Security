import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os

def overlay_text_on_image(image_path, prompt_text, output_path=None):
    """
    Overlay specified text on an image with dynamically sized text that fits the image.
    """
    try:
        # Open the image
        img = Image.open(image_path)
        width, height = img.size
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Dynamically calculate font sizes based on image dimensions
        title_font_size = int(width * 0.05)   
        bullet_font_size = int(width * 0.04) 
        
        # Make sure font sizes aren't too small or too large
        title_font_size = max(20, min(title_font_size, 80))
        bullet_font_size = max(16, min(bullet_font_size, 60))
        
        # Try to load fonts with dynamic sizes
        try:
            font_title = ImageFont.truetype("arial.ttf", title_font_size)
            font_bullets = ImageFont.truetype("arial.ttf", bullet_font_size)
        except IOError:
            # Use default font if the specified font is not available
            font_title = ImageFont.load_default()
            font_bullets = ImageFont.load_default()
        
        # Add the title text: "Show me steps for " + prompt_text
        title_text = f"Show me steps for {prompt_text.lower()}"
        
        # Measure the text to ensure it fits
        if hasattr(draw, 'textbbox'):  # PIL 8.0.0 and higher
            # Calculate text dimensions to check if it fits
            title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
            title_width = title_bbox[2] - title_bbox[0]
            
            # If title is too wide, reduce the font size
            while title_width > width * 0.8 and title_font_size > 16:
                title_font_size -= 2
                font_title = ImageFont.truetype("arial.ttf", title_font_size)
                title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
                title_width = title_bbox[2] - title_bbox[0]
        
        # Calculate positions
        x_position = width * 0.05  # 5% from the left edge
        y_position = height * 0.05  # 5% from the top edge
        
        # Add the title text (with a black outline for better visibility)
        # First add black outline
        for offset_x, offset_y in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            draw.text(
                (x_position + offset_x, y_position + offset_y), 
                title_text, 
                fill=(0, 0, 0), 
                font=font_title
            )
        # Then add the white text
        draw.text((x_position, y_position), title_text, fill=(255, 255, 255), font=font_title)
        
        # Calculate the space needed for the title (approximately)
        title_height = title_font_size * 1.2
        
        # Add the bullet points with appropriate spacing
        bullet_y_start = y_position + title_height + (height * 0.02)  # Add some padding after title
        
        # Calculate bullet spacing based on image height and number of bullets
        available_height = height - bullet_y_start - (height * 0.1)  # Leave 10% margin at bottom
        bullet_spacing = min(bullet_font_size * 1.5, available_height / 5)
        
        for i in range(1, 6):
            bullet_text = f"{i}. "
            # Add black outline for bullets too
            for offset_x, offset_y in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text(
                    (x_position + offset_x, bullet_y_start + (i-1) * bullet_spacing + offset_y),
                    bullet_text,
                    fill=(0, 0, 0),
                    font=font_bullets
                )
            # Then add the white text
            draw.text(
                (x_position, bullet_y_start + (i-1) * bullet_spacing),
                bullet_text,
                fill=(255, 255, 255),
                font=font_bullets
            )
        
        # Determine output path
        if output_path is None:
            file_name = os.path.basename(image_path)
            directory = os.path.dirname(image_path)
            name, ext = os.path.splitext(file_name)
            output_path = os.path.join(directory, f"{name}_modified{ext}")
        
        # Save the modified image
        img.save(output_path)
        print(f"Image saved to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

def process_file(file_path):
    """
    Process a CSV or Excel file containing image paths and prompt text.
    
    Parameters:
    file_path (str): Path to the CSV or Excel file
    """
    # Determine file type and read accordingly
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    
    # Check if required columns exist
    image_col = "image_location"
    prompt_col = "prompt_text"
    
   
    if image_col is None or prompt_col is None:
        raise ValueError("Could not identify image location and prompt-text columns. "
                        "Please make sure your file has columns with these names.")
    
    print(f"Found image column: {image_col}")
    print(f"Found prompt column: {prompt_col}")
    
    # Create output directory if it doesn't exist
    output_dir = "modified_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each row
    results = []
    for idx, row in df.iterrows():
        image_path = row[image_col]
        prompt_text = row[prompt_col]
        
        # Skip rows with missing data
        if pd.isna(image_path) or pd.isna(prompt_text):
            print(f"Skipping row {idx+1} due to missing data")
            continue
        
        # Create output path
        file_name = os.path.basename(image_path)
        name, ext = os.path.splitext(file_name)
        output_path = os.path.join(output_dir, f"{name}_modified{ext}")
        
        # Process the image
        print(f"Processing {idx+1}/{len(df)}: {image_path}")
        result_path = overlay_text_on_image(image_path, prompt_text, output_path)
        
        if result_path:
            results.append({
                'original_image': image_path,
                'prompt': prompt_text,
                'modified_image': result_path
            })
    
    # Create a summary CSV
    results_df = pd.DataFrame(results)
    results_path = os.path.join(output_dir, "processing_results.csv")
    results_df.to_csv(results_path, index=False)
    print(f"\nProcessing complete. Summary saved to {results_path}")
    print(f"Modified images saved to {output_dir} directory")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Please enter the path to your CSV or Excel file: ")
    
    process_file(file_path)