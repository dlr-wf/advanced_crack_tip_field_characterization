import os


def delete_ansys_files(ansys_folder):
    # Delete overhead Ansys files
    files = os.listdir(ansys_folder)
    delete_endings = ('.out', '_.inp', '.db', '.DSP', '.esav', '.mntr', '.iges', '.page', '.sh',
                      '.lock', '.rst', '.err', '.esav', '.full', '.stat', '.log', 'anstmp')
    for ansys_file in files:
        if ansys_file.endswith(delete_endings):
            os.remove(ansys_file)
