import os
import sys
import subprocess

def main():
    try:
        # Get WMI process details
        output = subprocess.check_output("wmic process where \"name='python.exe'\" get processid,commandline,executablepath", shell=True).decode('utf-8', errors='ignore')
        print("Active Python Processes:")
        print(output)
        
        pids_to_kill = []
        for line in output.splitlines():
            line_strip = line.strip()
            if not line_strip or "ProcessId" in line_strip:
                continue
            
            # Find the PID (which is the last token in the wmic line if we parse it)
            parts = line_strip.split()
            pid = parts[-1]
            if not pid.isdigit():
                continue
                
            cmdline = line_strip.lower()
            # If the process is running from our workspace or venv, kill it!
            if "voice_agent" in cmdline or "jobjocky" in cmdline or "uvicorn" in cmdline:
                print(f"Selecting for kill: PID {pid} -> {line_strip[:120]}")
                pids_to_kill.append(pid)
        
        # Kill the processes
        for pid in pids_to_kill:
            try:
                subprocess.run(f"taskkill /F /T /PID {pid}", shell=True)
                print(f"Killed process {pid} and its children.")
            except Exception as e:
                print(f"Failed to kill {pid}: {e}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
