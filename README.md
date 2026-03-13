# KiCad Rule Converter v1.0

![KiCad Version](https://img.shields.io/badge/KiCad-v10.0-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

**KiCad Rule Converter v1.0** is an External Action Plugin for the KiCad PCB Editor. It provides a user-friendly GUI to seamlessly convert Altium Designer Design Rule files (`.RUL`) into KiCad Custom Design Rules (`.kicad_dru`). It also allows for transferring existing `.kicad_dru` files to other KiCad projects.

Designed by Muzaffer Nizam.

## ✨ Features

* **GUI-Based Operation:** Easy-to-use interface built with `wxPython`.
* **Automated Conversion:** Parses Altium `.RUL` syntax (Clearance, Width, RoutingVias, etc.) and translates it into KiCad's s-expression custom rule format.
* **Robust File Reader:** Prevents crashes caused by different file encodings (UTF-8, UTF-16 BOM, Windows-1254, etc.).
* **Rule Mapping & Logging:** Automatically identifies rules that cannot be directly converted (e.g., Polygon Connect, Solder Mask Expansions) and displays them in a built-in table with suggestions on where to define them manually in KiCad.
* **CSV Export:** Export the list of unconverted rules to a `.csv` file for easy tracking and manual implementation.

## 🚀 Installation (KiCad v10)

1. **Download the Plugin:**
   Download the Python script (e.g., `rule_converter.py`) and the `icon.png` file from this repository.

2. **Locate your KiCad Plugins Folder:**
   Depending on your operating system, find the KiCad v10 scripting plugins directory:
   * **Windows:** `C:\Users\<Your_Username>\Documents\KiCad\10.0\scripting\plugins\`
   * **Linux:** `~/.local/share/kicad/10.0/scripting/plugins/`
   * **macOS:** `~/Documents/KiCad/10.0/scripting/plugins/`
   
   *(Note: If the `scripting` or `plugins` folders do not exist, create them manually.)*

3. **Copy the Files:**
   Place both the Python script and `icon.png` directly into the `plugins` folder. Ensure they are in the same directory so the icon loads correctly.

4. **Refresh Plugins:**
   * Open the **KiCad PCB Editor**.
   * Go to the top menu and select **Tools -> External Plugins -> Refresh Plugins**.
   * The "Rule Manager GUI" icon will now appear in your top toolbar.

## 🛠️ How to Use

1. **Launch the Plugin:** Click the Rule Manager icon in the KiCad PCB Editor toolbar.
2. **Select Source File:** Click the "Browse" button next to "Source File" and select your Altium `.RUL` file (or an existing `.kicad_dru` file you want to copy).
3. **Select Target Directory:** Click the "Browse" button next to "Target KiCad Project Directory" and choose the folder of your current KiCad project. (The plugin automatically detects the current open board directory by default).
4. **Convert:** Click the **"Convert / Transfer"** button.
5. **Review Unconverted Rules:** If certain Altium rules require manual definition in KiCad (like Zone Properties or Net Classes), they will be listed in the table along with instructions on where to set them.
6. **Export to CSV (Optional):** Click the **"Export to CSV"** button to save the unconverted rules list for your records.
7. **Verify in KiCad:** Close the plugin and go to **File -> Board Setup -> Custom Rules** in KiCad to see your newly generated rules!

## 📝 License
This project is open-source. Feel free to fork, modify, and contribute!
