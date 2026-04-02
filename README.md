<div align="center">
  <img src="icon.png" width="250" alt="Universal Scrambler Logo">
</div>

# Universal Video Scrambler

Hey there! This is a simple tool to visually scramble and unscramble videos and images using a randomized key. It's great for keeping your media files private.

### ⚠️ Notice about Windows Defender & Antiviruses
If you download the compiled `.exe` version of this tool, Windows Defender (or other antivirus software) might flag it as a virus, Trojan, or malware dropper. **This is a false positive.** 

Because this executable is built using Nuitka—a tool that packages an entire Python environment into a single file and extracts it to a temporary hidden folder when you double-click it—antiviruses get suspicious of its behavior. It also lacks an expensive corporate digital signature. You can safely add it to your antivirus exclusions, or if you prefer, you can just run it directly from the Python source code!

### 🛠️ How to run from the Python source code
If you don't want to use the `.exe` or want to see exactly how the code works, running it from the source is super easy:

1. Download and install **Python** on your computer. *(Important: Make sure to check the box that says "Add Python to PATH" during the installation).*
2. Open your terminal or command prompt inside the project folder.
3. Install the required background libraries by running this command:
   ```bash
   pip install Flask opencv-python numpy imageio-ffmpeg
   ```
4. Once the installation finishes, you can start the program by double-clicking the `Start_Scrambler.bat` file. Alternatively, you can run this command in your terminal:
   ```bash
   python main.py
   ```
5. A local server will start, and your web browser will automatically open the interface. Enjoy!
