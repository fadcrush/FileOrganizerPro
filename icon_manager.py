"""
Folder Icon Manager for FileOrganizer Pro 2.0
Handles custom folder icons for organized categories
"""

import os
import ctypes
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import struct

class FolderIconManager:
    """Manages custom folder icons for organized directories"""
    
    def __init__(self, icons_directory=None):
        self.icons_dir = Path(icons_directory) if icons_directory else Path(__file__).parent / "icons"
        self.icons_dir.mkdir(exist_ok=True)
        
        # Category icon mappings
        self.category_icons = {
            'Images': 'camera.ico',
            'Videos': 'video.ico',
            'Documents': 'document.ico',
            'Audio': 'audio.ico',
            'Archives': 'archive.ico',
            'Code': 'code.ico',
            'Spreadsheets': 'spreadsheet.ico',
            'Presentations': 'presentation.ico',
            'Executables': 'executable.ico',
            'Fonts': 'font.ico',
            'Others': 'misc.ico',
            'Duplicates': 'duplicate.ico'
        }
        
        # Ensure default icons exist
        self.create_default_icons()
    
    def create_default_icons(self):
        """Create default category icons if they don't exist"""
        
        # Icon specifications: (color, symbol/text)
        icon_specs = {
            'camera.ico': ('#4CAF50', '📷'),
            'video.ico': ('#2196F3', '🎬'),
            'document.ico': ('#FF9800', '📄'),
            'audio.ico': ('#9C27B0', '🎵'),
            'archive.ico': ('#795548', '📦'),
            'code.ico': ('#607D8B', '</>'),
            'spreadsheet.ico': ('#4CAF50', '📊'),
            'presentation.ico': ('#F44336', '📊'),
            'executable.ico': ('#9E9E9E', '⚙'),
            'font.ico': ('#673AB7', 'Aa'),
            'misc.ico': ('#757575', '📁'),
            'duplicate.ico': ('#FF5722', '⚠')
        }
        
        for icon_name, (color, symbol) in icon_specs.items():
            icon_path = self.icons_dir / icon_name
            if not icon_path.exists():
                self.create_simple_icon(icon_path, color, symbol)
    
    def create_simple_icon(self, output_path, color, symbol):
        """Create a simple colored icon with symbol"""
        try:
            # Create 256x256 image
            img = Image.new('RGBA', (256, 256), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw folder shape
            # Folder body
            draw.rectangle([(20, 80), (236, 220)], fill=color, outline='black', width=3)
            
            # Folder tab
            draw.rectangle([(20, 60), (100, 80)], fill=color, outline='black', width=3)
            
            # Add symbol/text
            try:
                # Try to use a font
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Center the symbol
            bbox = draw.textbbox((0, 0), symbol, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (256 - text_width) // 2
            y = (220 - text_height) // 2 + 40
            
            draw.text((x, y), symbol, fill='white', font=font)
            
            # Save as ICO (multiple sizes)
            self.save_as_ico(img, output_path)
            
        except Exception as e:
            print(f"Error creating icon {output_path}: {e}")
    
    def save_as_ico(self, img, output_path):
        """Save image as .ico file with multiple sizes"""
        try:
            # Create multiple sizes
            sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
            images = []
            
            for size in sizes:
                resized = img.resize(size, Image.Resampling.LANCZOS)
                images.append(resized)
            
            # Save as ICO
            images[0].save(
                output_path,
                format='ICO',
                sizes=[(img.width, img.height) for img in images],
                append_images=images[1:]
            )
        except Exception as e:
            print(f"Error saving ICO: {e}")
            # Fallback: save just the main size
            img.save(output_path, format='ICO')
    
    def set_folder_icon(self, folder_path, icon_name=None, category=None):
        """Set custom icon for a folder on Windows"""
        
        if not os.name == 'nt':
            print("Folder icons only supported on Windows")
            return False
        
        folder_path = Path(folder_path)
        
        # Determine icon file
        if icon_name:
            icon_file = self.icons_dir / icon_name
        elif category:
            icon_file = self.icons_dir / self.category_icons.get(category, 'misc.ico')
        else:
            return False
        
        if not icon_file.exists():
            print(f"Icon file not found: {icon_file}")
            return False
        
        try:
            # Create desktop.ini
            desktop_ini = folder_path / "desktop.ini"
            
            with open(desktop_ini, 'w', encoding='utf-8') as f:
                f.write("[.ShellClassInfo]\n")
                f.write(f"IconResource={icon_file},0\n")
                f.write(f"InfoTip=Organized by FileOrganizer Pro\n")
            
            # Set file attributes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            FILE_ATTRIBUTE_SYSTEM = 0x04
            FILE_ATTRIBUTE_READONLY = 0x01
            
            # Hide desktop.ini
            ctypes.windll.kernel32.SetFileAttributesW(
                str(desktop_ini),
                FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
            )
            
            # Make folder read-only (required for custom icon)
            current_attrs = ctypes.windll.kernel32.GetFileAttributesW(str(folder_path))
            if current_attrs != -1:
                ctypes.windll.kernel32.SetFileAttributesW(
                    str(folder_path),
                    current_attrs | FILE_ATTRIBUTE_READONLY
                )
            
            # Refresh Windows Explorer
            self.refresh_explorer()
            
            return True
            
        except Exception as e:
            print(f"Error setting folder icon: {e}")
            return False
    
    def refresh_explorer(self):
        """Refresh Windows Explorer to show icon changes"""
        try:
            SHChangeNotify = ctypes.windll.shell32.SHChangeNotify
            SHCNE_ASSOCCHANGED = 0x08000000
            SHCNF_FLUSH = 0x1000
            SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_FLUSH, None, None)
        except:
            pass
    
    def apply_category_icons(self, organized_folder):
        """Apply icons to all category folders"""
        organized_folder = Path(organized_folder)
        success_count = 0
        
        for category in self.category_icons.keys():
            category_folder = organized_folder / category
            if category_folder.exists() and category_folder.is_dir():
                if self.set_folder_icon(category_folder, category=category):
                    success_count += 1
                    
                    # Also apply to year subfolders if they exist
                    for subfolder in category_folder.iterdir():
                        if subfolder.is_dir() and subfolder.name.isdigit():
                            # Year folder
                            self.set_folder_icon(subfolder, category=category)
        
        return success_count
    
    def create_preview_icon(self, folder_path, output_icon_path):
        """Generate preview icon showing folder contents (first 4 images)"""
        try:
            folder_path = Path(folder_path)
            
            # Get first 4 images
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            images = []
            
            for file in folder_path.iterdir():
                if file.suffix.lower() in image_extensions:
                    images.append(file)
                    if len(images) >= 4:
                        break
            
            if not images:
                return False
            
            # Create 256x256 base
            icon = Image.new('RGB', (256, 256), color='white')
            
            if len(images) == 1:
                # Single image, center it
                img = Image.open(images[0])
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                x = (256 - img.width) // 2
                y = (256 - img.height) // 2
                icon.paste(img, (x, y))
            else:
                # Grid layout
                positions = [(10, 10), (138, 10), (10, 138), (138, 138)]
                for i, img_path in enumerate(images[:4]):
                    try:
                        img = Image.open(img_path)
                        img.thumbnail((118, 118), Image.Resampling.LANCZOS)
                        icon.paste(img, positions[i])
                    except:
                        continue
            
            # Save as ICO
            self.save_as_ico(icon, output_icon_path)
            return True
            
        except Exception as e:
            print(f"Error creating preview icon: {e}")
            return False
    
    def remove_folder_icon(self, folder_path):
        """Remove custom icon from folder"""
        try:
            folder_path = Path(folder_path)
            desktop_ini = folder_path / "desktop.ini"
            
            if desktop_ini.exists():
                # Remove hidden/system attributes
                ctypes.windll.kernel32.SetFileAttributesW(str(desktop_ini), 0)
                desktop_ini.unlink()
            
            # Remove read-only from folder
            current_attrs = ctypes.windll.kernel32.GetFileAttributesW(str(folder_path))
            if current_attrs != -1:
                FILE_ATTRIBUTE_READONLY = 0x01
                ctypes.windll.kernel32.SetFileAttributesW(
                    str(folder_path),
                    current_attrs & ~FILE_ATTRIBUTE_READONLY
                )
            
            self.refresh_explorer()
            return True
            
        except Exception as e:
            print(f"Error removing folder icon: {e}")
            return False


# Test the icon manager
if __name__ == "__main__":
    icon_manager = FolderIconManager()
    print(f"Icon manager initialized. Icons directory: {icon_manager.icons_dir}")
    print(f"Created {len(list(icon_manager.icons_dir.glob('*.ico')))} default icons")