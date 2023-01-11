import os

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


plt.rcParams.update({
    "font.size": 16,
    "text.usetex": True,
    "font.family": "Computer Modern"
})

units_dict = {
    1: 'MPa*mm^{1/2}',
    2: 'MPa',
    3: 'MPa*mm^{-1/2}',
    4: 'MPa*mm^{-1}',
    5: 'MPa*mm^{-3/2}'
}

RESULTS_PATH = os.path.join('integral_evaluation', 'results')
OUT_PATH = os.path.join(RESULTS_PATH, 'diagrams', 'alpha_vs_williams')
if not os.path.exists(OUT_PATH):
    os.makedirs(OUT_PATH)

df = pd.read_csv(os.path.join(RESULTS_PATH, 'SECT_parameter_study_int_method.csv'))

# Add h/w as geometry discriptor
df['h/w'] = df['height [mm]'] / df['width [mm]']

# Add normalized Williams coefficients
thickness = 2
for n in [1, 2, 3, 4, 5]:
    df[f'$a_{n}$'] = df[f"a_{n} [{units_dict[n]}]"] / (df["F [N]"] / (df['width [mm]'] * thickness)) / (df['width [mm]'])**(1-n/2)


# Fix some parameters
FORCE = 10000
H_DURCH_W = 1
ESIZE = 0.125

# Filter dataframe
df = df[df['F [N]'] == FORCE]
df = df[df['h/w'] == H_DURCH_W]
df = df[df['esize [mm]'] == ESIZE]

values_list = [f"$a_{n}$" for n in [1, 2, 3, 4, 5]]
df_melted = df.melt(id_vars=['alpha'], value_vars=values_list,
                    var_name="coefficient", value_name="normed Williams coefficient")

fig = plt.figure()
plot = sns.lineplot(data=df_melted, x='alpha', y="normed Williams coefficient",
                    hue="coefficient", style='coefficient', marker='o', ci='sd',
                    legend="full")
plot.set(xlabel='$\\alpha=a/W$')
plot.set(ylabel='$a_n$')
plt.legend(title=None)
# plt.ylim(-5, 2)
plt.savefig(os.path.join(OUT_PATH, f"Alpha_vs_Williams_HW{H_DURCH_W}_F{FORCE}_ESIZE{ESIZE}.png"), dpi=600)
plt.close()
