from PIL import Image
import pytesseract

def extract_text(filename):
    img = Image.open(filename)
    return pytesseract.image_to_string(img)