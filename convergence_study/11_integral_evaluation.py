import os

from rich.progress import track
import pandas as pd

from crackpy.fracture_analysis.line_integration import IntegralProperties
from crackpy.structure_elements.material import Material
from crackpy.fracture_analysis.pipeline import FractureAnalysisPipeline
from crackpy.fracture_analysis.plot import PlotSettings
from crackpy.fracture_analysis.read import OutputReader

# Paths
FAT_OUTPUT_PATH = 'integral_evaluation'
if not os.path.exists(FAT_OUTPUT_PATH):
    os.makedirs(FAT_OUTPUT_PATH)

#######################################
# Create fracture analysis input file
#######################################
with open('fracture_analysis_input.txt', mode='w') as file:
    file.write('{:>60},{:>12},{:>17},{:>17},{:>12},{:>6},{:>12},{:>12}\n'.format(
        'Filename', 'Force', 'Crack Tip x [mm]', 'Crack Tip y [mm]', 'Crack Angle', 'Side', 'Width [mm]', 'Height [mm]'))
    for nodemap in os.listdir('Nodemaps'):
        print(nodemap)
        nodemap_splitted = nodemap[:-4].split('_')
        print(nodemap_splitted)
        force = float(nodemap_splitted[1][1:])
        alpha = float(nodemap_splitted[2][5:])
        width = float(nodemap_splitted[3][1:])
        height = float(nodemap_splitted[4][1:])
        esize = float(nodemap_splitted[5][5:])

        file.write('{:>60},{:>12.2f},{:>17.2f},{:>17.2f},{:>12.2f},{:>6},{:>12.1f},{:>12.1f}\n'.format(
            nodemap, force, alpha * width / 2, 0, 0, 'right', width, height))


########################################################################################################################
# Test different number of integration points
########################################################################################################################
DATA_PATH = 'integral_evaluation'
NUMBERS_OF_NODES = [25, 50, 100, 200]
for num_nodes in NUMBERS_OF_NODES:

    # Paths
    output_path = os.path.join(DATA_PATH, f'number_of_nodes_{num_nodes}')
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    int_props = IntegralProperties(
        number_of_paths=90,
        number_of_nodes=num_nodes,

        bottom_offset=-0,
        top_offset=0,

        integral_size_left=-2,
        integral_size_right=2,
        integral_size_top=2,
        integral_size_bottom=-2,

        paths_distance_top=0.5,
        paths_distance_left=0.5,
        paths_distance_right=0.5,
        paths_distance_bottom=0.5,

        mask_tolerance=3,

        buckner_williams_terms=[1, 2, 3, 4]
    )

    material = Material(E=72000, nu_xy=0.33, sig_yield=350)
    plot_sets = PlotSettings(ylim_down=-55, ylim_up=55, min_value=0, max_value=350, background='sig_vm', cmap='jet')

    pipeline = FractureAnalysisPipeline(
        material=material,
        nodemap_path='Nodemaps',
        input_file='fracture_analysis_input.txt',
        output_path=output_path,
        integral_properties=int_props,
        optimization_properties=None,
        plot_sets=plot_sets
    )
    pipeline.run(20)


########################################
# Create integral evaluation dataframe #
########################################
FOLDERS = [f'number_of_nodes_{num_nodes}' for num_nodes in NUMBERS_OF_NODES]
RESULTS_PATH = os.path.join(DATA_PATH, 'number_of_nodes_results')
if not os.path.exists(RESULTS_PATH):
    os.makedirs(RESULTS_PATH)

df = pd.DataFrame()
for folder in FOLDERS:
    TXT_PATH = os.path.join(DATA_PATH, folder, 'txt-files')

    for file in track(os.listdir(TXT_PATH)):

        # Get parameters from filename
        filename = ''.join(file.split('_right_Output'))
        force = float(file.split('_F')[-1].split('_')[0])
        alpha = float(file.split('_alpha')[-1].split('_')[0])
        width = float(file.split('_w')[-1].split('_')[0])
        height = float(file.split('_h')[-1].split('_')[0])
        esize = float(file.split('_esize')[-1].split('_')[0])

        # open file and read data
        reader = OutputReader()
        curr_df_A_n = reader.read_tag_data(path=TXT_PATH, filename=file, tag='Path_Williams_a_n')
        curr_df_B_n = reader.read_tag_data(path=TXT_PATH, filename=file, tag='Path_Williams_b_n')
        curr_df_SIFs = reader.read_tag_data(path=TXT_PATH, filename=file, tag='Path_SIFs')
        curr_df_paths = reader.read_tag_data(path=TXT_PATH, filename=file, tag='Path_Properties')
        curr_df = curr_df_A_n.join(curr_df_B_n).join(curr_df_paths).join(curr_df_SIFs)
        original_columns = list(curr_df.columns)

        # add columns with parameter data
        curr_df = curr_df.assign(**{'Filename': filename})
        curr_df = curr_df.assign(**{'F [N]': force})
        curr_df = curr_df.assign(**{'alpha': alpha})
        curr_df = curr_df.assign(**{'width [mm]': width})
        curr_df = curr_df.assign(**{'height [mm]': height})
        curr_df = curr_df.assign(**{'esize [mm]': esize})

        # make index a column and rename it to path
        curr_df.reset_index(inplace=True)
        curr_df = curr_df.rename(columns={'index': 'path'})

        # rearrange columns
        new_columns = ['Filename', 'F [N]', 'alpha', 'width [mm]', 'height [mm]', 'esize [mm]', 'path']
        curr_df = curr_df[new_columns + original_columns]

        # append to df
        if df.empty:
            df = curr_df
        else:
            df = pd.concat([df, curr_df], ignore_index=True)

# export df as csv
df.to_csv(os.path.join(RESULTS_PATH, 'number_of_nodes_esize.csv'), index=False)


########################################################################################################################
# Test different tick sizes
########################################################################################################################

TICK_SIZES = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
for tick_size in TICK_SIZES:

    # Paths
    output_path = os.path.join(DATA_PATH, f'integral_tick_size_{tick_size}')
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    int_props = IntegralProperties(
        number_of_paths=90,
        integral_tick_size=tick_size,

        bottom_offset=-0,
        top_offset=0,

        integral_size_left=-2,
        integral_size_right=2,
        integral_size_top=2,
        integral_size_bottom=-2,

        paths_distance_top=0.5,
        paths_distance_left=0.5,
        paths_distance_right=0.5,
        paths_distance_bottom=0.5,

        mask_tolerance=3,

        buckner_williams_terms=[1, 2, 3, 4]
    )

    material = Material(E=72000, nu_xy=0.33, sig_yield=350)
    plot_sets = PlotSettings(ylim_down=-55, ylim_up=55, min_value=0, max_value=350, background='sig_vm', cmap='jet')

    pipeline = FractureAnalysisPipeline(
        material=material,
        nodemap_path='Nodemaps',
        input_file='fracture_analysis_input.txt',
        output_path=output_path,
        integral_properties=int_props,
        optimization_properties=None,
        plot_sets=plot_sets
    )
    pipeline.run(20)


########################################
# Create integral evaluation dataframe #
########################################
FOLDERS = [f'integral_tick_size_{tick_size}' for tick_size in TICK_SIZES]
RESULTS_PATH = os.path.join(DATA_PATH, 'tick_size_results')
if not os.path.exists(RESULTS_PATH):
    os.makedirs(RESULTS_PATH)

df = pd.DataFrame()
for folder in FOLDERS:
    TXT_PATH = os.path.join(DATA_PATH, folder, 'txt-files')

    for file in track(os.listdir(TXT_PATH)):

        # Get parameters from filename
        filename = ''.join(file.split('_right_Output'))
        force = float(file.split('_F')[-1].split('_')[0])
        alpha = float(file.split('_alpha')[-1].split('_')[0])
        width = float(file.split('_w')[-1].split('_')[0])
        height = float(file.split('_h')[-1].split('_')[0])
        esize = float(file.split('_esize')[-1].split('_')[0])

        # open file and read data
        reader = OutputReader()
        curr_df_A_n = reader.read_tag_data(path=TXT_PATH, filename=file, tag='Path_Williams_a_n')
        curr_df_B_n = reader.read_tag_data(path=TXT_PATH, filename=file, tag='Path_Williams_b_n')
        curr_df_SIFs = reader.read_tag_data(path=TXT_PATH, filename=file, tag='Path_SIFs')
        curr_df_paths = reader.read_tag_data(path=TXT_PATH, filename=file, tag='Path_Properties')
        curr_df = curr_df_A_n.join(curr_df_B_n).join(curr_df_paths).join(curr_df_SIFs)
        original_columns = list(curr_df.columns)

        # add columns with parameter data
        curr_df = curr_df.assign(**{'Filename': filename})
        curr_df = curr_df.assign(**{'F [N]': force})
        curr_df = curr_df.assign(**{'alpha': alpha})
        curr_df = curr_df.assign(**{'width [mm]': width})
        curr_df = curr_df.assign(**{'height [mm]': height})
        curr_df = curr_df.assign(**{'esize [mm]': esize})

        # make index a column and rename it to path
        curr_df.reset_index(inplace=True)
        curr_df = curr_df.rename(columns={'index': 'path'})

        # rearrange columns
        new_columns = ['Filename', 'F [N]', 'alpha', 'width [mm]', 'height [mm]', 'esize [mm]', 'path']
        curr_df = curr_df[new_columns + original_columns]

        # append to df
        if df.empty:
            df = curr_df
        else:
            df = pd.concat([df, curr_df], ignore_index=True)

# export df as csv
df.to_csv(os.path.join(RESULTS_PATH, 'integral_tick_size_esize.csv'), index=False)
