from PIL import Image
import pytesseract



def popo(filename):
    img = Image.open(filename)
    return pytesseract.image_to_string(img)