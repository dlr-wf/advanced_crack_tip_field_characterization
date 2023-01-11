import os

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter1d

from crackpy.structure_elements.data_files import Nodemap
from crackpy.fracture_analysis.crack_tip import williams_stress_field
from crackpy.fracture_analysis.data_processing import CrackTipInfo, InputData
from crackpy.structure_elements.material import Material


plt.rcParams.update({
    "font.size": 16,
    "text.usetex": True,
    "font.family": "Computer Modern"
})


def make_polar(x, y):
    """takes cartesian coordinates and maps onto polar coordinates"""
    r = np.sqrt(x ** 2.0 + y ** 2.0)
    phi = np.arctan2(y, x)
    return r, phi


NODEMAP_PATH = 'Nodemaps'
NODEMAP_NAME = 'Nodemap_F10000_alpha0.5_w100_h120.0_esize0.125.txt'
PLOT_PATH = os.path.join('integral_evaluation', 'results', 'diagrams', 'approx_error')
if not os.path.exists(PLOT_PATH):
    os.makedirs(PLOT_PATH)

SIGMA = 'sigma_x'


alpha = float(NODEMAP_NAME.split('_alpha')[-1].split('_')[0])
width = float(NODEMAP_NAME.split('_w')[-1].split('_')[0])

crack_tip = CrackTipInfo(
    crack_tip_x=alpha * width,
    crack_tip_y=0,
    crack_tip_angle=0,
    left_or_right='right'
)

material = Material(E=72000, nu_xy=0.33)

# import and transform data
nodemap = Nodemap(NODEMAP_NAME, NODEMAP_PATH)
data = InputData(nodemap)
data.calc_stresses(material=material)
data.transform_data(crack_tip.crack_tip_x, crack_tip.crack_tip_y, crack_tip.crack_tip_angle)

# define ligament
ligament_x = np.linspace(0.1, 30, 100)
ligament_y = np.zeros_like(ligament_x)

# calculate stress from FE data
sigma_x_ligament = griddata((data.coor_x, data.coor_y), data.sig_x, (ligament_x, ligament_y))
sigma_y_ligament = griddata((data.coor_x, data.coor_y), data.sig_y, (ligament_x, ligament_y))
sigma_xy_ligament = griddata((data.coor_x, data.coor_y), data.sig_xy, (ligament_x, ligament_y))

df_fe = pd.DataFrame()
df_fe = df_fe.assign(Method=['FE'] * len(ligament_x))
df_fe = df_fe.assign(x=ligament_x)
df_fe = df_fe.assign(y=ligament_y)
df_fe = df_fe.assign(sigma_x=sigma_x_ligament)
df_fe = df_fe.assign(sigma_y=sigma_y_ligament)


units_dict = {
    1: 'MPa*mm^{1/2}',
    2: 'MPa',
    3: 'MPa*mm^{-1/2}',
    4: 'MPa*mm^{-1}',
    5: 'MPa*mm^{-3/2}',
    6: 'MPa*mm^{-2}',
    7: 'MPa*mm^{-5/2}',
    8: 'MPa*mm^{-3}',
    9: 'MPa*mm^{-7/2}',
    10: 'MPa*mm^{-4}'
}

chen_results = os.path.join('integral_evaluation', 'results', 'CT_parameter_study_int_method.csv')

df_res = pd.read_csv(chen_results)
df_res = df_res[df_res['Filename'] == NODEMAP_NAME]

df = pd.DataFrame(columns=['x', 'FE', 'Int', f'{SIGMA}_norm', 'N'])

for N in [1, 2, 3, 4, 5]:

    a = []
    b = []
    for n in range(1, N+1):
        A_n = df_res[f'a_{n} [{units_dict[n]}]'].mean()
        B_n = df_res[f'b_{n} [{units_dict[n]}]'].mean()
        a.append(A_n)
        b.append(B_n)

    # make polar coordinates
    r, phi = make_polar(x=ligament_x, y=ligament_y)

    # calculate stress field from williams coefficients
    sigma_xx, sigma_yy, sigma_xy = williams_stress_field(a, b, list(range(1, N+1)), phi, r)

    df_int = pd.DataFrame()
    df_int = df_int.assign(Method=['Int'] * len(ligament_x))
    df_int = df_int.assign(N=[N] * len(ligament_x))
    df_int = df_int.assign(x=ligament_x)
    df_int = df_int.assign(y=ligament_y)
    df_int = df_int.assign(sigma_x=sigma_xx)
    df_int = df_int.assign(sigma_y=sigma_yy)
    df_int = df_int.assign(sigma_xy=sigma_xy)

    df_pivot = pd.concat([df_fe, df_int], ignore_index=True)
    df_pivot = df_pivot.pivot(index='x', columns='Method', values=SIGMA)
    df_pivot[f'{SIGMA}_norm'] = (df_pivot['Int'] - df_pivot['FE']) / df_pivot['FE']
    df_pivot[f'{SIGMA}_norm_abs'] = df_pivot[f'{SIGMA}_norm'].abs()

    # smoothen plot
    df_pivot[f'{SIGMA}_norm_abs'] = gaussian_filter1d(df_pivot[f'{SIGMA}_norm'].abs().to_numpy(), sigma=3)

    df_pivot.reset_index(inplace=True)
    df_pivot['N'] = N

    df = pd.concat([df, df_pivot], ignore_index=True)

    df['r/a'] = df['x'] / crack_tip.crack_tip_x

# Plot
fig = plt.figure()
ax = plt.subplot(111)

plot = sns.lineplot(data=df, x='r/a', y=f'{SIGMA}_norm_abs', hue='N', style='N', palette='bright')
plot.set(yscale='log', title="")
plt.xlabel("$r/a$")
plt.ylabel("$|\\sigma_{x}^{N,norm}-1|$")
plt.ylim([1e-3, 100])

# Shrink current axis by 10%
box = ax.get_position()
ax.set_position([box.x0 + 0.05*box.width, box.y0, box.width * 0.85, box.height])

# Put a legend to the right of the current axis
ax.legend(title='$N=$', loc='center left', bbox_to_anchor=(1, 0.5))

plt.savefig(os.path.join(PLOT_PATH, f'CT_{NODEMAP_NAME[:-4]}_{SIGMA}_norm_log.png'), dpi=600)
plt.close()
# plt.show()
