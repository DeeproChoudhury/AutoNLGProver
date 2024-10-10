import subprocess

def start_server():

    directory = "/home/dc755/Portal-to-ISAbelle/"
    command = 'sbt "runMain pisa.server.PisaOneStageServer8000"'

    process = subprocess.Popen(command, shell=True, cwd=directory)

    return process


if __name__ == "__main__":
    process = start_server()

    print("Server has been started.")