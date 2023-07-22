import logging
import subprocess

def run_uvicorn():
    uvicorn_command = "uvicorn main:app --reload"
    subprocess.run(uvicorn_command, shell=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_uvicorn()