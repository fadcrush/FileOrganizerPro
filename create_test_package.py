"""
Create test package for friends - Quick distribution

Creates a simple ZIP file with executable and instructions.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import zipfile


def create_simple_executable():
    """Create basic executable without license system (for testing)"""

    print("=" * 60)
    print("Creating Test Package for Friends")
    print("=" * 60)
    print()

    # Check PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    print("Building executable (this takes 2-3 minutes)...")
    print()

    # Simple PyInstaller command - no complexity
    cmd = [
        "pyinstaller",
        "--name", "FileOrganizerPro",
        "--onefile",
        "--windowed",
        "--clean",
        "--add-data", f"src{os.pathsep}src",
        "--hidden-import", "PIL._tkinter_finder",
        "file_organizer_pro_scifi.py"
    ]

    try:
        subprocess.check_call(cmd)
        print()
        print("✓ Executable created successfully!")
        print()
    except subprocess.CalledProcessError:
        print("❌ Build failed. See error above.")
        return False

    return True


def create_readme():
    """Create simple README for testers"""

    readme_content = """
# FileOrganizer Pro - Beta Test Version

Thanks for testing FileOrganizer Pro!

## Quick Start (30 seconds)

1. **Run the app**
   - Double-click: FileOrganizerPro.exe
   - Wait a few seconds for it to load

2. **Try the command palette**
   - Press: Ctrl+K
   - Type: "settings"
   - Try switching between Dark/Light mode

3. **Test the search**
   - Click "Search" tab
   - Browse to a folder with files
   - Search for something
   - Try different filters

4. **Test organization**
   - Click "Organize" tab
   - Browse to a test folder
   - Select "Category → Year"
   - Enable "DRY RUN" (preview mode)
   - Click "Start Organization"

## What to Test

Please test these features and let me know if anything breaks:

### Critical Features
- [ ] App launches without errors
- [ ] Can switch between Dark/Light theme
- [ ] Can search for files
- [ ] Can organize files (try DRY RUN first!)
- [ ] Settings save between sessions

### Things to Try
- [ ] Command palette (Ctrl+K)
- [ ] Exclude folders in settings
- [ ] Different file types (images, documents, videos)
- [ ] Large folders (1000+ files)

## Feedback Needed

Please tell me:

1. **Did it crash?** If yes, when?
2. **Was anything confusing?** What?
3. **What did you like?** Features you enjoyed
4. **What's missing?** Features you expected
5. **Would you pay $49 for this?** Honest answer!

## Known Issues

- First launch might be slow (10-15 seconds)
- Some antivirus software may flag it (false positive)
- Windows might show "Unknown Publisher" warning (it's safe)

## Contact

Send feedback to: [YOUR EMAIL HERE]

Thanks for helping make this better! 🚀

---

**Note:** This is a beta test version. Some features may have bugs.
Your data is safe - use DRY RUN mode to preview before organizing!
"""

    with open("dist/README_BETA.txt", "w") as f:
        f.write(readme_content)

    print("✓ Beta README created")


def create_test_zip():
    """Create ZIP package for distribution"""

    print()
    print("Creating ZIP package...")

    zip_name = "FileOrganizerPro_BetaTest.zip"

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add executable
        zipf.write("dist/FileOrganizerPro.exe", "FileOrganizerPro.exe")

        # Add README
        zipf.write("dist/README_BETA.txt", "README_BETA.txt")

    # Get file size
    size_mb = os.path.getsize(zip_name) / (1024 * 1024)

    print(f"✓ ZIP created: {zip_name} ({size_mb:.1f} MB)")
    print()

    return zip_name


def main():
    """Main build process"""

    # Step 1: Build executable
    if not create_simple_executable():
        return

    # Step 2: Create README
    create_readme()

    # Step 3: Create ZIP
    zip_file = create_test_zip()

    print("=" * 60)
    print("✓ Test Package Ready!")
    print("=" * 60)
    print()
    print(f"Package: {zip_file}")
    print()
    print("How to share with friends:")
    print()
    print("1. Upload to:")
    print("   • Google Drive (share link)")
    print("   • Dropbox (share link)")
    print("   • WeTransfer (wetransfer.com)")
    print("   • Send.firefox.com (up to 2.5GB)")
    print()
    print("2. Send them the link")
    print()
    print("3. Ask for feedback on:")
    print("   • Did it work?")
    print("   • Was it useful?")
    print("   • Would they pay $49?")
    print()
    print("Pro tip: Track who tests what in a spreadsheet!")
    print()


if __name__ == '__main__':
    main()
