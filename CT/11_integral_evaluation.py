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
            nodemap, force, alpha * width, 0, 0, 'right', width, height))


#######################################
#         Fracture Analysis           #
#######################################
int_props = IntegralProperties(
    number_of_paths=10,
    number_of_nodes=200,

    bottom_offset=-0,
    top_offset=0,

    integral_size_left=-8,
    integral_size_right=8,
    integral_size_top=8,
    integral_size_bottom=-8,

    paths_distance_top=0.2,
    paths_distance_left=0.2,
    paths_distance_right=0.2,
    paths_distance_bottom=0.2,

    mask_tolerance=3,

    buckner_williams_terms=[1, 2, 3, 4, 5]
)

material = Material(E=72000, nu_xy=0.33, sig_yield=350)
plot_sets = PlotSettings(min_value=0, max_value=350, background='sig_vm', cmap='jet')

pipeline = FractureAnalysisPipeline(
    material=material,
    nodemap_path='Nodemaps',
    input_file='fracture_analysis_input.txt',
    output_path=FAT_OUTPUT_PATH,
    integral_properties=int_props,
    optimization_properties=None,
    plot_sets=plot_sets
)
pipeline.run(20)

########################################
# Create integral evaluation dataframe #
########################################
OUTPUT_PATH = 'integral_evaluation'
TXT_PATH = os.path.join(OUTPUT_PATH, 'txt-files')
RESULTS_PATH = os.path.join(OUTPUT_PATH, 'results')
if not os.path.exists(RESULTS_PATH):
    os.makedirs(RESULTS_PATH)

df = pd.DataFrame()
reader = OutputReader()

for file in track(os.listdir(TXT_PATH)):

    # Get parameters from filename
    filename = ''.join(file.split('_right_Output'))
    force = float(file.split('_F')[-1].split('_')[0])
    alpha = float(file.split('_alpha')[-1].split('_')[0])
    width = float(file.split('_w')[-1].split('_')[0])
    height = float(file.split('_h')[-1].split('_')[0])
    esize = float(file.split('_esize')[-1].split('_')[0])

    # open file and read data
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
df.to_csv(os.path.join(RESULTS_PATH, 'CT_parameter_study_int_method.csv'), index=False)
