"""
Image Steganography - Dissimulation de données dans des images
Utilise la technique LSB (Least Significant Bit) pour cacher des données
"""
import numpy as np
from PIL import Image
import os
from typing import Tuple, Optional


class ImageSteganography:
    """
    Stéganographie d'image via LSB
    
    Cache des données en modifiant les bits de poids faible des pixels
    Invisible à l'œil nu, très efficace pour l'exfiltration
    """
    
    def __init__(self):
        self.delimiter = b'<<<END>>>'  # Délimiteur de fin de données
    
    def embed_data(self, image_path: str, data: bytes, output_path: str) -> bool:
        """
        Cache des données dans une image
        
        Args:
            image_path: Image d'origine
            data: Données à cacher
            output_path: Image de sortie
        
        Returns:
            True si succès
        """
        try:
            # Chargement de l'image
            img = Image.open(image_path)
            img = img.convert('RGB')  # Conversion en RGB si nécessaire
            
            # Calcul de la capacité
            capacity = self.calculate_capacity(image_path)
            
            if len(data) + len(self.delimiter) > capacity:
                print(f"[ImageStego] ERROR: Data too large ({len(data)} bytes) for image capacity ({capacity} bytes)")
                return False
            
            # Ajout du délimiteur
            data_with_delimiter = data + self.delimiter
            
            # Conversion en array numpy
            img_array = np.array(img)
            height, width, channels = img_array.shape
            
            # Conversion des données en bits
            data_bits = ''.join(format(byte, '08b') for byte in data_with_delimiter)
            data_bits_len = len(data_bits)
            
            print(f"[ImageStego] Embedding {len(data)} bytes ({data_bits_len} bits) into image {width}x{height}")
            
            # Modification des LSB
            bit_index = 0
            embedded = False
            
            for i in range(height):
                for j in range(width):
                    for k in range(channels):
                        if bit_index < data_bits_len:
                            # Modification du LSB du pixel
                            pixel_value = img_array[i, j, k]
                            # Remplace le LSB par le bit de données
                            img_array[i, j, k] = (pixel_value & 0xFE) | int(data_bits[bit_index])
                            bit_index += 1
                        else:
                            embedded = True
                            break
                    if embedded:
                        break
                if embedded:
                    break
            
            # Sauvegarde de l'image
            output_img = Image.fromarray(img_array)
            output_img.save(output_path, quality=100)  # Qualité max pour préserver les données
            
            print(f"[ImageStego] ✓ Data embedded successfully in {output_path}")
            return True
            
        except Exception as e:
            print(f"[ImageStego] Embed error: {e}")
            return False
    
    def extract_data(self, image_path: str) -> Optional[bytes]:
        """
        Extrait les données cachées d'une image
        
        Args:
            image_path: Image contenant les données
        
        Returns:
            Données extraites ou None
        """
        try:
            # Chargement de l'image
            img = Image.open(image_path)
            img = img.convert('RGB')
            
            img_array = np.array(img)
            height, width, channels = img_array.shape
            
            print(f"[ImageStego] Extracting data from image {width}x{height}")
            
            # Extraction des LSB
            bits = []
            
            for i in range(height):
                for j in range(width):
                    for k in range(channels):
                        # Extraction du LSB
                        pixel_value = img_array[i, j, k]
                        bits.append(str(pixel_value & 1))
            
            # Conversion en bytes
            bit_string = ''.join(bits)
            bytes_data = []
            
            for i in range(0, len(bit_string), 8):
                byte_bits = bit_string[i:i+8]
                if len(byte_bits) == 8:
                    bytes_data.append(int(byte_bits, 2))
            
            data_bytes = bytes(bytes_data)
            
            # Recherche du délimiteur
            delimiter_pos = data_bytes.find(self.delimiter)
            
            if delimiter_pos != -1:
                extracted_data = data_bytes[:delimiter_pos]
                print(f"[ImageStego] ✓ Extracted {len(extracted_data)} bytes")
                return extracted_data
            else:
                print("[ImageStego] No delimiter found, extracting all data")
                return data_bytes[:1000]  # Limite arbitraire
            
        except Exception as e:
            print(f"[ImageStego] Extract error: {e}")
            return None
    
    def calculate_capacity(self, image_path: str) -> int:
        """
        Calcule la capacité de stockage d'une image (en bytes)
        
        Args:
            image_path: Chemin de l'image
        
        Returns:
            Capacité en bytes
        """
        try:
            img = Image.open(image_path)
            img = img.convert('RGB')
            width, height = img.size
            channels = 3  # RGB
            
            # 1 bit par pixel par canal
            total_bits = width * height * channels
            total_bytes = total_bits // 8
            
            return total_bytes
            
        except Exception as e:
            print(f"[ImageStego] Capacity calculation error: {e}")
            return 0
    
    def embed_file(self, image_path: str, file_to_hide: str, output_path: str) -> bool:
        """
        Cache un fichier complet dans une image
        
        Args:
            image_path: Image d'origine
            file_to_hide: Fichier à cacher
            output_path: Image de sortie
        
        Returns:
            True si succès
        """
        try:
            with open(file_to_hide, 'rb') as f:
                data = f.read()
            
            return self.embed_data(image_path, data, output_path)
            
        except Exception as e:
            print(f"[ImageStego] File embed error: {e}")
            return False
    
    def extract_to_file(self, image_path: str, output_file: str) -> bool:
        """
        Extrait les données d'une image vers un fichier
        
        Args:
            image_path: Image contenant les données
            output_file: Fichier de sortie
        
        Returns:
            True si succès
        """
        data = self.extract_data(image_path)
        
        if data:
            try:
                with open(output_file, 'wb') as f:
                    f.write(data)
                
                print(f"[ImageStego] ✓ Data written to {output_file}")
                return True
                
            except Exception as e:
                print(f"[ImageStego] Write error: {e}")
                return False
        
        return False


class AdvancedSteganography:
    """
    Techniques stéganographiques avancées
    """
    
    @staticmethod
    def embed_multi_channel(image_path: str, data: bytes, output_path: str, 
                           bits_per_channel: int = 2) -> bool:
        """
        Embeds data using multiple LSBs per channel
        
        Args:
            image_path: Source image
            data: Data to hide
            output_path: Output image
            bits_per_channel: Number of LSBs to use (1-4)
        
        Returns:
            True if successful
        """
        try:
            img = Image.open(image_path).convert('RGB')
            img_array = np.array(img)
            height, width, channels = img_array.shape
            
            # Calculate capacity
            total_bits = width * height * channels * bits_per_channel
            capacity = total_bits // 8
            
            if len(data) > capacity:
                print(f"[AdvancedStego] Data too large: {len(data)} > {capacity} bytes")
                return False
            
            # Convert data to bits
            data_bits = ''.join(format(byte, '08b') for byte in data)
            
            # Create bitmask for LSBs
            mask = (1 << bits_per_channel) - 1
            clear_mask = 0xFF ^ mask
            
            bit_index = 0
            
            for i in range(height):
                for j in range(width):
                    for k in range(channels):
                        if bit_index + bits_per_channel <= len(data_bits):
                            # Extract bits_per_channel bits
                            bits_to_embed = data_bits[bit_index:bit_index + bits_per_channel]
                            bits_value = int(bits_to_embed, 2)
                            
                            # Clear and set LSBs
                            pixel_value = img_array[i, j, k]
                            img_array[i, j, k] = (pixel_value & clear_mask) | bits_value
                            
                            bit_index += bits_per_channel
            
            # Save
            output_img = Image.fromarray(img_array)
            output_img.save(output_path, quality=100)
            
            print(f"[AdvancedStego] ✓ Embedded {len(data)} bytes using {bits_per_channel} bits/channel")
            return True
            
        except Exception as e:
            print(f"[AdvancedStego] Error: {e}")
            return False
    
    @staticmethod
    def generate_carrier_image(width: int = 800, height: int = 600, 
                               output_path: str = 'carrier.png') -> bool:
        """
        Génère une image porteuse avec du bruit aléatoire
        
        Args:
            width: Largeur
            height: Hauteur
            output_path: Chemin de sortie
        
        Returns:
            True si succès
        """
        try:
            # Génération d'une image avec du bruit aléatoire
            img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
            
            img = Image.fromarray(img_array)
            img.save(output_path)
            
            print(f"[AdvancedStego] ✓ Generated carrier image: {output_path}")
            return True
            
        except Exception as e:
            print(f"[AdvancedStego] Generation error: {e}")
            return False


if __name__ == '__main__':
    # Test de la stéganographie
    print("=== Image Steganography Test ===\n")
    
    # Génération d'une image de test
    print("1. Generating test carrier image...")
    AdvancedSteganography.generate_carrier_image(
        width=400, 
        height=300, 
        output_path='/tmp/test_carrier.png'
    )
    
    # Test d'embedding
    print("\n2. Testing data embedding...")
    stego = ImageSteganography()
    
    test_data = b"This is a secret message hidden in the image using LSB steganography! " * 5
    
    success = stego.embed_data(
        '/tmp/test_carrier.png',
        test_data,
        '/tmp/test_stego.png'
    )
    
    if success:
        print("✓ Embedding successful")
        
        # Calcul de capacité
        capacity = stego.calculate_capacity('/tmp/test_carrier.png')
        print(f"\nImage capacity: {capacity} bytes ({capacity / 1024:.2f} KB)")
        print(f"Data embedded: {len(test_data)} bytes")
        print(f"Usage: {(len(test_data) / capacity) * 100:.2f}%")
    
    # Test d'extraction
    print("\n3. Testing data extraction...")
    extracted = stego.extract_data('/tmp/test_stego.png')
    
    if extracted:
        print(f"✓ Extracted {len(extracted)} bytes")
        print(f"Match: {extracted == test_data}")
        print(f"Preview: {extracted[:50]}...")
    
    print("\n✓ Test complete")
    print("\nUsage examples:")
    print("  stego = ImageSteganography()")
    print("  stego.embed_file('cover.png', 'secret.txt', 'stego.png')")
    print("  stego.extract_to_file('stego.png', 'extracted.txt')")
