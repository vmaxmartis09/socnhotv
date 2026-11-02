import subprocess
import os
import shutil
import sys

def main():
    tmp_dir = r"C:\concat_tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    src_msi = r"./bin\download\Concat-0.2.7-windows-x86_64.msi"
    dest_msi = os.path.join(tmp_dir, "concat.msi")
    
    print(f"Copying {src_msi} to {dest_msi}...")
    shutil.copyfile(src_msi, dest_msi)
    
    out_dir = os.path.join(tmp_dir, "extracted")
    os.makedirs(out_dir, exist_ok=True)
    
    cmd = f'msiexec.exe /a "{dest_msi}" /qn TARGETDIR="{out_dir}"'
    print("Running:", cmd)
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("Exit code:", res.returncode)
    
    files = []
    for root, dirs, filenames in os.walk(out_dir):
        for f in filenames:
            files.append(os.path.join(root, f))
    print(f"Extracted {len(files)} files:")
    for f in files[:20]:
        print("  -", f)

if __name__ == "__main__":
    main()
