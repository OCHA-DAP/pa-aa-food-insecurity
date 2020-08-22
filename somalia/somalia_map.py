import numpy as np
import pandas as pd
import shapefile as shp
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('dark')
sns.despine()

region_name = {0: 'Awdal', 1: 'Bakool', 2: 'Banadir', 3: 'Bari', 4: 'Bay',
               5: 'Galgaduud', 6: 'Gedo', 7: 'Hiraan', 8: 'Juba Dhexe',
               9: 'Juba Hoose', 10: 'Mudug', 11: 'Nugaal', 12: 'Sanaag',
               13: 'Shabelle Dhexe', 14: 'Shabelle Hoose', 15: 'Sool',
               16: 'Togdheer', 17: 'Woqooyi Galbeed'}
region_number = {'Awdal': 0, 'Bakool': 1, 'Banadir': 2, 'Bari': 3, 'Bay': 4,
                 'Galgaduud': 5, 'Gedo': 6, 'Hiraan': 7, 'Juba Dhexe': 8,
                 'Juba Hoose': 9, 'Mudug': 10, 'Nugaal': 11, 'Sanaag': 12,
                 'Shabelle Dhexe': 13, 'Shabelle Hoose': 14, 'Sool': 15,
                 'Togdheer': 16, 'Woqooyi Galbeed': 17}
region_colours = {0: "#adddce", 1: "#a3b18a", 2: "#b6c69d", 3: "#cee0b1",
                  4: "#e5f9c5", 5: "#eaffc9", 6: "#588157", 7: "#649968",
                  8: "#74b279", 9: "#84cc89", 10: "#3a5a40", 11: "#457050",
                  12: "#558962", 13: "#65a374", 14: "#344e41", 15: "#507f6c",
                  16: "#406656", 17: "#609982"}
ipc_colours = {1: "#cdf8ce", 2: "#f8e61a", 3: "#e67c08", 4: "#c91d07",
               5: "#640901"}

# Downloaded country shapefile from: https://gadm.org/download_country_v3.html
shp_path = '../Prod/gadm36_SOM_shp/gadm36_SOM_1.shp'
sf = shp.Reader(shp_path)

# Tutorial from:
# https://towardsdatascience.com/mapping-geograph-data-in-python-610a963d2d7f
##############################################################################


# def plot_shape(id, s=None):
#     """ PLOTS A SINGLE SHAPE """
#     plt.figure()
#     ax = plt.axes()
#     ax.set_aspect('equal')
#     shape_ex = sf.shape(id)
#     x_lon = np.zeros((len(shape_ex.points), 1))
#     y_lat = np.zeros((len(shape_ex.points), 1))
#     for ip in range(len(shape_ex.points)):
#         x_lon[ip] = shape_ex.points[ip][0]
#         y_lat[ip] = shape_ex.points[ip][1]
#     plt.plot(x_lon, y_lat)
#     x0 = np.mean(x_lon)
#     y0 = np.mean(y_lat)
#     plt.text(x0, y0, s, fontsize=10)
#     # use bbox (bounding box) to set plot limits
#     plt.xlim(shape_ex.bbox[0], shape_ex.bbox[2])
#     return x0, y0

##############################################################################


def shapefl_to_df(shape_fl):
    """
    Convert a shape file to a Panda's dataframe
    """
    fields = [x[0] for x in sf.fields][1:]
    records = shape_fl.records()
    shape_points = [s.points for s in shape_fl.shapes()]
    df = pd.DataFrame(columns=fields, data=records)
    df = df.assign(coords=shape_points)
    return df


def fill_shape(shape_data, shape_id, axes, colour=None, name=True,
               f_col='black'):
    if not colour:
        colour = region_colours[shape_id]
    x_vals, y_vals = shape_coor(shape_data, shape_id)
    axes.fill(x_vals, y_vals, colour)
    if name:
        add_shape_name(plt, x_vals, y_vals, region_name[shape_id],
                       bx_colour=colour, font_col=f_col, bx_alpha=0.85)


def add_shape_name(a_plot, x_vals, y_vals, name, font_col='black',
                   bx_colour=None, bx_alpha=0.7):
    x0 = np.mean(x_vals)
    y0 = np.mean(y_vals)
    a_plot.text(x0, y0, name, fontsize=10, fontweight='heavy', color=font_col,
                bbox=dict(facecolor=bx_colour, alpha=bx_alpha))


def shape_coor(shape_data, loc_id):
    x = np.zeros((len(shape_data.points), 1))
    y = np.zeros((len(shape_data.points), 1))
    for ip in range(len(shape_data.points)):
        x[ip] = shape_data.points[ip][0]
        y[ip] = shape_data.points[ip][1]
    return x, y


def som_map_plot(shape_fl, ipc_show={}, names=False, fill=False,
                 fill_region=[], title='SOMALIA',
                 line_col='#627aa5', x_lim=None, y_lim=None, figsize=(7.3, 6)):
    '''
    Plot the Somalia regional map
    '''
    plt.figure(figsize=figsize)

    fig, ax = plt.subplots(figsize=figsize)
    loc_id = 0
    for shape in shape_fl.shapeRecords():
        region_colour = region_colours[loc_id]
        x_vals, y_vals = shape_coor(shape.shape, loc_id)
        if fill:
            ax.plot(x_vals, y_vals, 'k', color=line_col)
        else:
            ax.plot(x_vals, y_vals, 'k', color=region_colour)

        if names & (x_lim is None) & (y_lim is None):
            add_shape_name(plt, x_vals, y_vals, region_name[loc_id],
                           bx_colour=region_colour)
        loc_id += 1

    # Add region colours to the map
    if fill:
        for ident in region_name.keys():
            x_vals, y_vals = shape_coor(shape_fl.shape(ident), ident)
            ax.fill(x_vals, y_vals, region_colours[ident])

    # Show specific region colours
    if fill_region and not fill:
        for ident in fill_region:
            colour = region_colours[ident]
            fill_shape(shape_fl.shape(ident), ident, ax)

    # Add IPC region colours
    if ipc_show:
        for ident in ipc_show.keys():
            col_code = ipc_show[ident]
            colour = ipc_colours[col_code]
            if col_code == 5:
                font_colour = 'white'
            else:
                font_colour = 'black'
            fill_shape(shape_fl.shape(ident), ident, ax, colour=colour,
                       f_col=font_colour)

    plt.title(title, fontsize=20, fontweight='heavy', color="teal")
    plt.xticks([])
    plt.yticks([])

    if (x_lim is not None) & (y_lim is not None):
        plt.xlim(x_lim)
        plt.ylim(y_lim)


if __name__ == "__main__":

    print(sf.records())

    # Create a dataframe from the shapefile
    df = shapefl_to_df(sf)
    print('df.sample(5):\n', df.sample(5))

    key = {}
    for k, v in df.iterrows():
        key[v['NAME_1']] = k
    print('key:\n', key)

    # som_map_plot(sf, names=True)

    region_ipcs = {12: 4, 1: 3, 5: 5, 16: 2}
    fills = [1, 5, 12, 16]
    # som_map_plot(sf, names=True)
    # som_map_plot(sf, ipc_show=region_ipcs, fill=True)
    som_map_plot(sf, title="Test Map", fill_region=fills)

    plt.show()
