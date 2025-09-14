import logging
import os
import subprocess
import sys

# --- Configuration ---
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

VENV_PATH = "venv_creative"
REQUIREMENTS_FILE = "requirements_creative.txt"
HOMEBREW_URL = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"

# System dependencies required by Python packages (key: package name,
# value: brew formula)
SYS_DEPS = {
    "py3exiv2": "boost",
    # Add other known system dependencies here
}

# --- Doctor Script ---


def check_command(command):
    """Checks if a command - line tool is available."""
    return (
        subprocess.run(["which", command], capture_output=True, text=True).returncode
        == 0
    )


def check_prerequisites():
    """Checks for essential tools like Homebrew."""
    logging.info("Step 1: Checking for system prerequisites...")
    if not check_command("brew"):
        logging.error(
            "Homebrew is not installed. It is required to install system libraries."
        )
        logging.info(
            "Please install Homebrew by running the following command, then run this script again:"
        )
        print(f'\\n/bin/bash -c "$(curl -fsSL {HOMEBREW_URL})"\\n')
        return False
    logging.info("✅ Homebrew is installed.")
    return True


def check_system_libraries():
    """Checks if required system libraries are installed via Homebrew."""
    logging.info("Step 2: Checking for required system libraries...")
    missing_libs = []
    for pkg, formula in SYS_DEPS.items():
        logging.info(f"-> Checking for '{formula}' (required by '{pkg}')...")
        result = subprocess.run(
            ["brew", "list", formula], capture_output=True, text=True
        )
        if result.returncode != 0:
            missing_libs.append(formula)

    if missing_libs:
        logging.error("The following required system libraries are missing.")
        logging.info(
            "Please install them by running this command, then run this script again:"
        )
        print(f"\\nbrew install {' '.join(missing_libs)}\\n")
        return False

    logging.info("✅ All required system libraries are installed.")
    return True


def setup_venv():
    """Creates or verifies the virtual environment."""
    logging.info(f"Step 3: Setting up virtual environment at '{VENV_PATH}'...")
    if not os.path.exists(VENV_PATH):
        try:
            subprocess.run([sys.executable, "-m", "venv", VENV_PATH], check=True)
            logging.info("✅ Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to create virtual environment: {e}")
            return False
    else:
        logging.info("-> Virtual environment already exists.")
    return True


def install_dependencies():
    """Installs Python packages from the requirements file."""
    logging.info(
        f"Step 4: Installing creative dependencies from '{REQUIREMENTS_FILE}'..."
    )
    pip_executable = os.path.join(VENV_PATH, "bin", "pip")

    # It is critical to first upgrade pip inside the new venv
    subprocess.run([pip_executable, "install", "--upgrade", "pip"], check=True)

    try:
        command = [pip_executable, "install", "-r", REQUIREMENTS_FILE]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Stream output in real - time
        for line in iter(process.stdout.readline, ""):
            print(line, end="")
        for line in iter(process.stderr.readline, ""):
            sys.stderr.write(line)

        process.wait()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

        logging.info("✅ Creative dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Failed to install dependencies. pip exited with status {
                e.returncode}."
        )
        logging.error(
            f"Please check the error messages above. You may need to modify '{REQUIREMENTS_FILE}' to resolve version conflicts \
    or remove incompatible packages like 'open3d'."
        )
        return False


def main():
    """Main function to run the environment doctor."""
    logging.info("--- Starting TRAE.AI Creative Environment Doctor ---")

    if not check_prerequisites():
        return

    if not check_system_libraries():
        return

    if not setup_venv():
        return

    if not install_dependencies():
        logging.error("❌ Creative environment setup failed.")
        return

    logging.info("\\n--- ✅ Creative Environment is Ready! ---")
    logging.info("You can now test the video and avatar features.")


if __name__ == "__main__":
    main()
