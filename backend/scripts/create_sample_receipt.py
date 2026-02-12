from PIL import Image, ImageDraw, ImageFont
import os

def create_receipt():
    # Make image larger for clarity
    img = Image.new('RGB', (600, 800), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Try to load Arial for Windows
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        header_font = ImageFont.truetype("arial.ttf", 32)
    except:
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()
    
    y = 50
    d.text((50, y), "TATA Croma Electronics", font=header_font, fill=(0, 0, 0))
    y += 50
    d.text((50, y), "GSTIN: 27AABCT1234", font=font, fill=(0, 0, 0))
    y += 40
    d.text((50, y), "-"*40, font=font, fill=(0, 0, 0))
    y += 40
    
    # Items clearly formatted
    items = [
        ("Milk", "2", "60.00"),
        ("Bread", "1", "40.00"),
        ("Eggs", "12", "120.00")
    ]
    
    for name, qty, price in items:
        # Format: Name    x Qty    Price
        line = f"{name:<15} x {qty:<5} {price:>8}"
        d.text((50, y), line, font=font, fill=(0, 0, 0))
        y += 40
        
    d.text((50, y), "-"*40, font=font, fill=(0, 0, 0))
    y += 40
    d.text((50, y), f"{'Total':<23} {'220.00'}", font=header_font, fill=(0, 0, 0))
    
    img.save("sample_receipt.jpg")
    print("Created sample_receipt.jpg (High Res)")

if __name__ == "__main__":
    create_receipt()
