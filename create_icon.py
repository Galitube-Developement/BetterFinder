import os
from PIL import Image

def create_icon_from_png(png_path, ico_path):
    """
    Creates an .ico file from a .png file with multiple resolutions
    
    Args:
        png_path: Path to the PNG file
        ico_path: Path where the ICO file should be saved
    """
    print(f"Creating icon from {png_path}...")
    
    if not os.path.exists(png_path):
        print(f"Error: The file {png_path} does not exist.")
        return False
    
    try:
        # Open the image
        img = Image.open(png_path)
        
        # Create versions in different sizes for a complete icon
        icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Save as ICO with different sizes
        img.save(ico_path, format='ICO', sizes=icon_sizes)
        
        print(f"Icon successfully created: {ico_path}")
        
        # Check the file size
        size = os.path.getsize(ico_path)
        print(f"Icon file size: {size} bytes")
        
        return True
    except Exception as e:
        print(f"Error creating the icon: {e}")
        return False

if __name__ == "__main__":
    # Paths for the files
    png_path = os.path.join("app", "resources", "BetterFinder-Icon.png")
    ico_path = os.path.join("app", "resources", "icon.ico")
    
    # Create the icon
    success = create_icon_from_png(png_path, ico_path)
    
    if success:
        print("Icon was successfully created and can now be used for the application and installer.")
    else:
        print("Error creating the icon.") 