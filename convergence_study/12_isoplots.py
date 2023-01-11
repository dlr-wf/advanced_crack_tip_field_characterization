import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def normalize_williams(coeff: float, crack_length: float, sigma_nominell: float, n: int):
    coeff_norm = coeff / sigma_nominell * (np.pi * crack_length) ** (n/2 - 1)
    return coeff_norm


plt.rcParams.update({
    "font.size": 16,
    "text.usetex": True,
    "font.family": "Computer Modern"
})
units_dict = {
    'a_1': 'MPa*mm^{1/2}',
    'a_2': 'MPa',
    'a_3': 'MPa*mm^{-1/2}',
    'a_4': 'MPa*mm^{-1}'
}
units_tex = {
    'a_1': 'MPa \\cdot mm^{1/2}',
    'a_2': 'MPa',
    'a_3': 'MPa \\cdot mm^{-1/2}',
    'a_4': 'MPa \\cdot mm^{-1}'
}
units_quantiles = {
    'a_1': 0.1,
    'a_2': 1,
    'a_3': 1,
    'a_4': 2
}
THICKNESS_PLATE = 2  # mm


#############################################
# Number of nodes / Element size comparison #
#############################################
RESULTS_PATH = os.path.join('integral_evaluation', 'number_of_nodes_results')
OUT_PATH = os.path.join(RESULTS_PATH, 'diagrams')
if not os.path.exists(OUT_PATH):
    os.makedirs(OUT_PATH)

df = pd.read_csv(os.path.join(RESULTS_PATH, 'number_of_nodes_esize.csv'))

df = df[df['NumOfNodes'] != 25]  # remove 25 nodes case


for coeff in units_dict:
    df["sigma_nominell"] = df["F [N]"] / df["width [mm]"] / THICKNESS_PLATE
    n = int(coeff.split('_')[-1])
    df[f"{coeff}_norm"] = df[f"{coeff} [{units_dict[coeff]}]"] / df["sigma_nominell"] * (np.pi * df["alpha"] * df["width [mm]"])**(n/2-1)
    
    df_limit = df[df['LineXR'] >= 40]
    conv_limits = df_limit.groupby(['Filename', 'NumOfNodes', 'esize [mm]'])[f"{coeff}_norm"].mean()
    df = df.set_index(['Filename', 'NumOfNodes', 'esize [mm]'])
    df[f'Limit {coeff}'] = conv_limits
    df = df.reset_index()
    df_fil = df.filter(items=['Filename', 'NumOfNodes', 'esize [mm]', 'LineXR', f"{coeff}_norm", f'Limit {coeff}'])
    
    df_fil[f"Deviation from limit {coeff} in %"] = (df_fil[f"{coeff}_norm"] - df_fil[f'Limit {coeff}']) / df_fil[f'Limit {coeff}'] * 100
    
    # Find integration path closest to the crack tip and such that for all paths further away from the crack tip
    # the deviation from the limit is smaller than x%
    percent_quantil = units_quantiles[coeff]
    df_fil_2 = df_fil[df_fil[f"Deviation from limit {coeff} in %"].abs() >= percent_quantil]
    distances = df_fil_2.groupby(['Filename', 'NumOfNodes', 'esize [mm]'])['LineXR'].max() + 0.5
    df_fil = df_fil.set_index(['Filename', 'NumOfNodes', 'esize [mm]'])
    df_fil['Convergence distance [mm]'] = distances
    df_fil = df_fil.reset_index()
    
    df_fil['Convergence distance [mm]'] = df_fil[f'Convergence distance [mm]'].apply(lambda x: 2.0 if np.isnan(x) else x)
    
    # Convergence distance to r/a
    df_fil['Convergence distance r/a'] = df_fil['Convergence distance [mm]'] / 50
    
    df_final = df_fil[df['LineXR'] == 2.0]
    
    # Plot
    fig = plt.figure()
    ax = fig.add_subplot(111)

    min = df_final['Convergence distance r/a'].values.min()
    max = df_final['Convergence distance r/a'].values.max()
    #steps = np.min([(max - min) * 2 + 1, 10])
    contour_vector = np.linspace(min, max, 10, endpoint=True)
    label_vector = np.linspace(min, max, 10, endpoint=True)
    #label_vector = np.round(label_vector, 2)
    #contour_vector = np.linspace(0, 1, 100, endpoint=True)
    #label_vector = np.linspace(0, 1, 11, endpoint=True)
    #label_vector = np.round(label_vector, 1)
    
    plot = ax.tricontourf(df_final['NumOfNodes'].values, df_final['esize [mm]'].values,
                          df_final['Convergence distance r/a'].values,
                          contour_vector, extend='max')
    fig.colorbar(plot, ticks=label_vector, label=f'$r^*/a$ for $q={percent_quantil} \%$')
    
    ax.set_title(f"${coeff}$")
    ax.set_xlabel("$P$")
    ax.set_ylabel("$l_{\\rm e}$ [$mm$]")
    
    plt.savefig(os.path.join(OUT_PATH, f'isoplot_{coeff}.png'), dpi=600)
    plt.close()
