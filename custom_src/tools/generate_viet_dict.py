import os

def generate_vietnamese_dict():
    # Base dictionary from PaddleOCR
    base_dict_path = os.path.join("ppocr", "utils", "dict", "latin_dict.txt")
    if not os.path.exists(base_dict_path):
        base_dict_path = os.path.join("ppocr", "utils", "dict", "ppocrv5_latin_dict.txt")
        
    out_dict_path = os.path.join("ppocr", "utils", "dict", "vi_custom_dict.txt")
    
    # Read base characters
    characters = set()
    try:
        with open(base_dict_path, "r", encoding="utf-8") as f:
            for line in f:
                ch = line.strip('\n')
                if ch:
                    characters.add(ch)
    except FileNotFoundError:
        print(f"Cannot find base dict at {base_dict_path}")
        return

    # Vietnamese specific characters (uppercase and lowercase)
    viet_chars = [
        'à', 'á', 'ả', 'ã', 'ạ', 'ă', 'ằ', 'ắ', 'ẳ', 'ẵ', 'ặ', 'â', 'ầ', 'ấ', 'ẩ', 'ẫ', 'ậ',
        'è', 'é', 'ẻ', 'ẽ', 'ẹ', 'ê', 'ề', 'ế', 'ể', 'ễ', 'ệ',
        'ì', 'í', 'ỉ', 'ĩ', 'ị',
        'ò', 'ó', 'ỏ', 'õ', 'ọ', 'ô', 'ồ', 'ố', 'ổ', 'ỗ', 'ộ', 'ơ', 'ờ', 'ớ', 'ở', 'ỡ', 'ợ',
        'ù', 'ú', 'ủ', 'ũ', 'ụ', 'ư', 'ừ', 'ứ', 'ử', 'ữ', 'ự',
        'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ', 'đ',
        'À', 'Á', 'Ả', 'Ã', 'Ạ', 'Ă', 'Ằ', 'Ắ', 'Ẳ', 'Ẵ', 'Ặ', 'Â', 'Ầ', 'Ấ', 'Ẩ', 'Ẫ', 'Ậ',
        'È', 'É', 'Ẻ', 'Ẽ', 'Ẹ', 'Ê', 'Ề', 'Ế', 'Ể', 'Ễ', 'Ệ',
        'Ì', 'Í', 'Ỉ', 'Ĩ', 'Ị',
        'Ò', 'Ó', 'Ỏ', 'Õ', 'Ọ', 'Ô', 'Ồ', 'Ố', 'Ổ', 'Ỗ', 'Ộ', 'Ơ', 'Ờ', 'Ớ', 'Ở', 'Ỡ', 'Ợ',
        'Ù', 'Ú', 'Ủ', 'Ũ', 'Ụ', 'Ư', 'Ừ', 'Ứ', 'Ử', 'Ữ', 'Ự',
        'Ỳ', 'Ý', 'Ỷ', 'Ỹ', 'Ỵ', 'Đ'
    ]
    
    for ch in viet_chars:
        characters.add(ch)
        
    # Standard numbers and punctuation
    punctuations = list('!"#$%&\'()*+,-./0123456789:;<=>?@[\\]^_`{|}~ ')
    for ch in punctuations:
        characters.add(ch)

    # Convert to list and ensure space is at the very first line (common paddleocr convention)
    chars_list = list(characters)
    if ' ' in chars_list:
        chars_list.remove(' ')
        chars_list = [' '] + sorted(chars_list)
    else:
        chars_list = [' '] + sorted(chars_list)

    with open(out_dict_path, "w", encoding="utf-8") as f:
        for ch in chars_list:
            f.write(ch + "\n")
            
    print(f"Generated Vietnamese dictionary with {len(chars_list)} characters at {out_dict_path}")

if __name__ == "__main__":
    generate_vietnamese_dict()
