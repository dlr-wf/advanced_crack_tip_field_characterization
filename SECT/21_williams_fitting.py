import itertools
import os

import numpy as np
import pandas as pd
from crackpy.structure_elements.data_files import Nodemap

from rich.progress import track

from crackpy.fracture_analysis.data_processing import CrackTipInfo, InputData
from crackpy.structure_elements.material import Material
from crackpy.fracture_analysis.optimization import OptimizationProperties, Optimization

np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})

NODEMAP_PATH = 'Nodemaps'
material = Material(E=72000, nu_xy=0.33, sig_yield=350)
INPUT_FILE = 'fracture_analysis_input.txt'
OUTPUT_PATH = os.path.join('williams_fitting', 'csv-files')
if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)

# Get control file
input_df = pd.read_csv(INPUT_FILE, sep=",", skipinitialspace=True)

# Parameters [mm]
ANGLE_GAPS = [0, 10]
TICK_SIZES = [0.03]
RADII = [8.0]
DELTA_R = 2


for angle_gap, tick_size, r in track(list(itertools.product(ANGLE_GAPS, TICK_SIZES, RADII))):

    opt_props = OptimizationProperties(
        angle_gap=angle_gap,
        min_radius=r,
        max_radius=r + DELTA_R,
        tick_size=tick_size,
        terms=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    )

    options = {
        'angle_gap': angle_gap,
        'min_radius': r,
        'max_radius': r + DELTA_R,
        'tick_size': tick_size
    }

    # check if parameters were already computed
    outfile = f"angle{options['angle_gap']}_rmin{options['min_radius']}_" \
              f"rmax{options['max_radius']}_tick{options['tick_size']}.csv"
    if outfile in os.listdir(OUTPUT_PATH):
        print(f"Skipped {outfile}.")
        continue

    results_df = pd.DataFrame(columns=[
        'Filename', 'Error', 'r_min', 'r_max', 'angle_gap', 'tick_size',
        'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'a10',
        'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'b10'
    ])
    init_coeffs = None

    for index, data in input_df.iterrows():
        # print(f"{data['Filename']}")

        # get crack tip info from data
        ct = CrackTipInfo(
            crack_tip_x=data['Crack Tip x [mm]'],
            crack_tip_y=data['Crack Tip y [mm]'],
            crack_tip_angle=data['Crack Angle'],
            left_or_right=data['Side']
        )

        # get nodemap data and center to crack tip
        file = data['Filename']
        nodemap = Nodemap(file, NODEMAP_PATH)
        data = InputData(nodemap)
        data.calc_stresses(material)
        data.transform_data(ct.crack_tip_x, ct.crack_tip_y, ct.crack_tip_angle)

        successful = False
        res = None
        while not successful:
            opt = Optimization(data=data, material=material, options=opt_props)
            res = opt.optimize_williams_displacements(init_coeffs=init_coeffs)
            successful = res.success
            # print(res.success)
            # print(res.cost)
        # init_coeffs = res.x

        curr_res = {
            'Filename': [file],
            'Error': [res.cost],
            'r_min': [options['min_radius']],
            'r_max': [options['max_radius']],
            'angle_gap': [options['angle_gap']],
            'tick_size': [options['tick_size']],
            'a1': [res.x[0]],
            'a2': [res.x[1]],
            'a3': [res.x[2]],
            'a4': [res.x[3]],
            'a5': [res.x[4]],
            'a6': [res.x[5]],
            'a7': [res.x[6]],
            'a8': [res.x[7]],
            'a9': [res.x[8]],
            'a10': [res.x[9]],
            'b1': [res.x[10]],
            'b2': [res.x[11]],
            'b3': [res.x[12]],
            'b4': [res.x[13]],
            'b5': [res.x[14]],
            'b6': [res.x[15]],
            'b7': [res.x[16]],
            'b8': [res.x[17]],
            'b9': [res.x[18]],
            'b10': [res.x[19]]
        }
        results_df = pd.concat([results_df, pd.DataFrame(curr_res)], ignore_index=True)

    # save results to CSV
    results_df.to_csv(os.path.join(OUTPUT_PATH, outfile), index=False)


# Combine results into single CSV file
#################################################################################
ORIGIN = 'williams_fitting'
INPUT_PATH = os.path.join(ORIGIN, 'csv-files')
OUTPUT_PATH = os.path.join(ORIGIN, 'results')
if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)

df = pd.DataFrame()

for csv_file in os.listdir(INPUT_PATH):

    # read current csv file into dataframe
    curr_df = pd.read_csv(os.path.join(INPUT_PATH, csv_file))
    df = pd.concat([df, curr_df])


df['F [N]'] = df['Filename'].str.split('_F').str[-1].str.split('_').str[0].astype(float)
df['alpha'] = df['Filename'].str.split('_alpha').str[-1].str.split('_').str[0].astype(float)
df['width [mm]'] = df['Filename'].str.split('_w').str[-1].str.split('_').str[0].astype(float)
df['height [mm]'] = df['Filename'].str.split('_h').str[-1].str.split('_').str[0].astype(float)
df['esize [mm]'] = df['Filename'].str.split('_esize').str[-1].str.split('_').str[0].str[:-4].astype(float)

# export df as csv
df.to_csv(os.path.join(OUTPUT_PATH, 'SECT_parameter_study_fit_method.csv'), index=False)
