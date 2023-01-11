"""

    Simulations of MT-specimen with different element sizes.

    Needed:
        - ANSYS License

    Output:
        - Nodemaps (txt-files with nodal data)
        - Outputs (ANSYS outputs SIFs)
        - Plots (nodal von Mises stresses and meshes)

"""

import itertools
import os
import shutil
import time

from rich.progress import track

from ansys.mapdl.core import launch_mapdl
import ansys.mapdl.core.errors

from src.utils import delete_ansys_files


# Output folders
OUTPUT_PATH = 'Outputs'
NODEMAP_PATH = 'Nodemaps'
PLOT_PATH = 'Plots'
PYINPFILE = "02_pyinp.inp"

# Parameters
FORCES = [10000]
ALPHAS = [0.5]
WIDTHS = [200]
HEIGHTS = [200]
ESIZES = [0.1, 0.2, 0.4, 0.8]

if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)
if not os.path.exists(NODEMAP_PATH):
    os.makedirs(NODEMAP_PATH)
if not os.path.exists(PLOT_PATH):
    os.makedirs(PLOT_PATH)

for force, alpha, width, height, esize in track(list(itertools.product(FORCES, ALPHAS, WIDTHS, HEIGHTS, ESIZES))):

    experiment = f"F{force}_alpha{alpha}_w{width}_h{height}_esize{esize}"

    # Skip already calculated nodemaps
    experiment_nodemap = '_'.join(["Nodemap", experiment]) + '.txt'
    if experiment_nodemap in os.listdir(NODEMAP_PATH):
        continue

    while True:

        try:
            # Start MAPDL
            mapdl = launch_mapdl(run_location=os.getcwd(), nproc=5)

            # write input variables of parameter study
            with open(PYINPFILE, "w") as file:
                file.write(f"force={force}\n")
                file.write(f"alpha={alpha}\n")
                file.write(f"w={width}\n")
                file.write(f"h={height}\n")
                file.write(f"esize={esize}")

            inputfile = "00_main.inp"
            mapdl.input(inputfile)

            # Display results
            # mapdl.open_gui()
            mapdl.eplot(cpos='xy', savefig=os.path.join(PLOT_PATH, f'Elements_{experiment}.png'))
            mapdl.post_processing.plot_nodal_eqv_stress(
                cpos='xy', savefig=os.path.join(PLOT_PATH, f'VM_Stress_{experiment}.png')
            )

        except ansys.mapdl.core.errors.LockFileException:
            delete_ansys_files(ansys_folder=os.getcwd())
            continue

        except ansys.mapdl.core.errors.MapdlExitedError:
            print('Mapdl Session Terminated. Retrying...')
            continue

        except OSError:
            print('OSError. Retrying...')
            continue

        finally:
            mapdl.exit()
            time.sleep(5)
            delete_ansys_files(ansys_folder=os.getcwd())

        # Rename and reorganize files
        new_nodemap_name = '_'.join(["Nodemap", experiment]) + '.txt'
        os.rename("Nodemap.txt", new_nodemap_name)
        shutil.move(new_nodemap_name, NODEMAP_PATH)

        new_output_name = '_'.join(["Output", experiment]) + '.txt'
        os.rename("Output.txt", new_output_name)
        shutil.move(new_output_name, OUTPUT_PATH)

        new_vergleich_name = '_'.join(["Vergleich", experiment]) + '.txt'
        os.rename("Vergleich.txt", new_vergleich_name)
        shutil.move(new_vergleich_name, OUTPUT_PATH)

        break
