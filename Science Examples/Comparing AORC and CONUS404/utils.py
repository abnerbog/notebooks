import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import LineString, MultiLineString
import matplotlib.gridspec as gridspec
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, Optional, Union, Any

def plot_watersheds_with_flowlines(watershed_files, figsize=(8, 18), buffer=5000):
    """
    Plot multiple watersheds with flowlines, flow direction arrows, basemaps, and total area annotations.

    Parameters:
    - watershed_files: dict of {title: {'watershed': path_to_shp, 'flowline': path_to_shp}}
    - figsize: tuple, size of the figure
    - buffer: int, buffer in map units around the bounding box of each watershed
    """
    # Load and reproject all shapefiles
    datasets = {}
    for name, files in watershed_files.items():
        ws = gpd.read_file(files["watershed"]).to_crs(epsg=3857)
        fl = gpd.read_file(files["flowline"]).to_crs(epsg=3857)
        datasets[name] = {'watershed': ws, 'flowline': fl}

    # Prepare figure with consistent panel size
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(nrows=len(datasets), ncols=1, height_ratios=[1]*len(datasets))

    for i, (title, data) in enumerate(datasets.items()):
        ax = fig.add_subplot(gs[i])
        ws = data['watershed']
        fl = data['flowline']

        # Plot watershed and flowlines
        ws.plot(ax=ax, facecolor='green', edgecolor='lightgray', alpha=0.6)
        fl.plot(ax=ax, color='blue', linewidth=2)

        # Flow direction arrows
        for geom in fl.geometry:
            if isinstance(geom, (LineString, MultiLineString)):
                lines = [geom] if isinstance(geom, LineString) else geom.geoms
                for line in lines:
                    coords = list(line.coords)
                    for j in range(0, len(coords) - 1, max(len(coords)//10, 1)):
                        x0, y0 = coords[j]
                        x1, y1 = coords[j + 1]
                        ax.annotate(
                            '', xy=(x1, y1), xytext=(x0, y0),
                            arrowprops=dict(
                                arrowstyle='->',
                                color='orange',
                                lw=2,
                                mutation_scale=15
                            ),
                            annotation_clip=False
                        )

        # Individual extent for zoomed view
        bounds = ws.total_bounds
        ax.set_xlim(bounds[0] - buffer, bounds[2] + buffer)
        ax.set_ylim(bounds[1] - buffer, bounds[3] + buffer)

        # Add basemap and grid
        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldTopoMap)
        ax.grid(True, linestyle='--', alpha=0.3)

        # Total area annotation
        if 'areasqkm' in ws.columns:
            total_area = ws['areasqkm'].sum()
            ax.text(
                0.01, 0.99, f"Total Area: {total_area:.2f} km²",
                transform=ax.transAxes, fontsize=12,
                verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7)
            )

        ax.set_title(title, fontsize=14)
        ax.axis('on')

    plt.tight_layout()
    plt.show()

# preparing data
def clip_watershed_data(
    gdfs: Dict[str, gpd.GeoDataFrame],
    ds_conus404: xr.Dataset,
    ds_aorc: xr.Dataset,
    start_date: str,
    end_date: str
) -> Dict[str, Dict[str, xr.Dataset]]:
    """
    Clips and selects time-sliced data for multiple watersheds from CONUS404 and AORC datasets.

    Args:
        gdfs (Dict[str, gpd.GeoDataFrame]): A dictionary where keys are watershed names
                                            and values are GeoDataFrames representing
                                            the watershed boundaries.
        ds_conus404 (xr.Dataset): The CONUS404 xarray Dataset.
        ds_aorc (xr.Dataset): The AORC xarray Dataset.
        start_date (str): The start date for time slicing (e.g., '2000-01-01').
        end_date (str): The end date for time slicing (e.g., '2000-12-31').

    Returns:
        Dict[str, Dict[str, xr.Dataset]]: A nested dictionary where the outer keys are
                                          watershed names, and the inner dictionary
                                          contains 'conus404' and 'aorc' keys, each
                                          mapping to their respective clipped and
                                          time-sliced xarray Datasets.
    """
    
    clipped_data = {}

    for watershed_name, gdf_clip in gdfs.items():
        print(f"Processing watershed: {watershed_name}")

        # Clip and select time for CONUS404 dataset
        ds_conus404_sel = ds_conus404.rio.clip(
            gdf_clip.geometry.values,
            gdf_clip.crs,
            all_touched=True,  # select all grid cells that touch the vector boundary
            drop=True,         # drop anything that is outside the clipped region
            invert=False,
            from_disk=True
        ).sel(time=slice(start_date, end_date))

        # Clip and select time for AORC dataset
        ds_aorc_sel = ds_aorc.rio.clip(
            gdf_clip.geometry.values,
            gdf_clip.crs,
            all_touched=True,
            drop=True,
            invert=False,
            from_disk=True
        ).sel(time=slice(start_date, end_date))

        clipped_data[watershed_name] = {
            'conus404': ds_conus404_sel,
            'aorc': ds_aorc_sel
        }
    return clipped_data


def plot_watershed_data(
    watershed_name: str,
    clipped_data_watersheds: Dict[str, Dict[str, xr.Dataset]], # Clipped data contains only xarray Datasets
    gdfs_watersheds: Dict[str, gpd.GeoDataFrame], # Separate input for GeoDataFrames
    variable_of_interest: str,
    time_index: int = 0,
    cmap: str = 'viridis',
    chunk_compute: Optional[Union[str, Dict[str, Any]]] = None
):
    """
    Creates a two-panel plot to compare a variable from CONUS404 and AORC datasets
    for a single watershed at a specific time step.

    Args:
        clipped_data_watersheds (Dict[str, Dict[str, xr.Dataset]]): # Updated name
            The full dictionary containing clipped CONUS404 and AORC datasets
            for all watersheds, as returned by `clip_watershed_data`.
        gdfs_watersheds (Dict[str, gpd.GeoDataFrame]): # Updated name
            A dictionary where keys are watershed names and values are GeoDataFrames representing
            the watershed boundaries. Used for plotting the watershed outlines.
        watershed_name (str): # Updated name
            The name of the specific watershed to plot
            (e.g., 'Tuolumne River', 'Cottonwood Canyon'). This key must exist
            in both `clipped_data_watersheds` and `gdfs_watersheds`.
        variable_of_interest (str): The name of the variable to plot (e.g., 'RAINRATE', 'TMP').
        time_index (int): The index of the time step to plot (default is 0, the first time step).
        cmap (str): Colormap to use for the plots (default is 'viridis').
        chunk_compute (Optional[Union[str, Dict[str, Any]]]): Optional chunking
            configuration to apply before calling .compute(). Can be 'auto', a dictionary
            like {'time': 720, 'y': -1, 'x': -1}, or None to use existing chunks.
    """
    if watershed_name not in clipped_data_watersheds: # Updated name
        print(f"Error: Watershed '{watershed_name}' not found in provided clipped data.")
        return
    if watershed_name not in gdfs_watersheds: # Updated name
        print(f"Error: Watershed '{watershed_name}' not found in provided GeoDataFrames (gdfs_watersheds).")
        return

    # Extract data for the single watershed
    clipped_data_single_watershed = clipped_data_watersheds[watershed_name] # Updated name
    ds_conus404_sel = clipped_data_single_watershed['conus404']
    ds_aorc_sel = clipped_data_single_watershed['aorc']
    gdf_clip = gdfs_watersheds[watershed_name] # Updated name
    # watershed_name is already the input parameter, no need to reassign


    # Determine cbar_label and title_prefix based on variable_of_interest
    variable_metadata = {
        'RAINRATE': {'label': 'Precipitation (mm/hr)', 'title': 'Precipitation'},
        'TMP': {'label': 'Temperature (K)', 'title': 'Temperature'},
        # Add more mappings here for other variables as needed
    }

    # Get metadata, or use a default if not found
    metadata = variable_metadata.get(variable_of_interest, {
        'label': f'{variable_of_interest} (units unknown)',
        'title': variable_of_interest
    })
    cbar_label = metadata['label']
    title_prefix = metadata['title']


    # Ensure the variable exists in the dataset
    if variable_of_interest not in ds_conus404_sel.data_vars:
        print(f"Error: Variable '{variable_of_interest}' not found in CONUS404 for {watershed_name}. Cannot plot.")
        return
    if variable_of_interest not in ds_aorc_sel.data_vars:
        print(f"Error: Variable '{variable_of_interest}' not found in AORC for {watershed_name}. Cannot plot.")
        return

    # Apply chunking before computing if chunk_compute is provided
    conus404_data_to_compute = ds_conus404_sel[variable_of_interest].isel(time=time_index)
    aorc_data_to_compute = ds_aorc_sel[variable_of_interest].isel(time=time_index)

    if chunk_compute is not None:
        # Apply chunking to the relevant data array before computing
        conus404_data_to_compute = conus404_data_to_compute.chunk(chunk_compute)
        aorc_data_to_compute = aorc_data_to_compute.chunk(chunk_compute)
        print(f"Applying chunking {chunk_compute} for computation of {watershed_name}.")


    # Compute the data for the selected time index
    try:
        t0_conus = conus404_data_to_compute.compute()
        t0_aorc = aorc_data_to_compute.compute()
    except IndexError:
        print(f"Error: Time index {time_index} out of bounds for {watershed_name}. Cannot plot.")
        return
    except Exception as e:
        print(f"Error computing data for {watershed_name} and variable {variable_of_interest}: {e}. Cannot plot.")
        return

    # Determine common color scale limits
    vmin = float('inf')
    vmax = float('-inf')

    if t0_conus.size > 0:
        vmin = min(vmin, t0_conus.min().item())
        vmax = max(vmax, t0_conus.max().item())
    else:
        print(f"Warning: CONUS404 data for {watershed_name} is empty at time index {time_index}. Skipping for vmin/vmax calculation.")

    if t0_aorc.size > 0:
        vmin = min(vmin, t0_aorc.min().item())
        vmax = max(vmax, t0_aorc.max().item())
    else:
        print(f"Warning: AORC data for {watershed_name} is empty at time index {time_index}. Skipping for vmin/vmax calculation.")
    
    if vmin == float('inf') or vmax == float('-inf'):
        print("Could not determine valid color scale limits. Check data values or ensure spatial overlap.")
        return

    time_value_str = pd.to_datetime(t0_conus.time.values).strftime('%Y-%m-%d %H:%M')

    # Create subplots for a single watershed (1 row, 2 columns)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

    plot_handles = [] # To collect plot objects for the shared colorbar

    # Plot CONUS404
    ax_conus = axes[0]
    p_conus = t0_conus.plot(
        ax=ax_conus, vmin=vmin, vmax=vmax, cmap=cmap, add_colorbar=False
    )
    gdf_clip.plot(ax=ax_conus, facecolor='none', edgecolor='k', linewidth=1.5)
    ax_conus.set_title(f'{watershed_name}\nCONUS404 {title_prefix} at {time_value_str}')
    ax_conus.set_xlabel('')
    ax_conus.set_ylabel('')

    # Plot AORC
    ax_aorc = axes[1]
    p_aorc = t0_aorc.plot(
        ax=ax_aorc, vmin=vmin, vmax=vmax, cmap=cmap, add_colorbar=False
    )
    gdf_clip.plot(ax=ax_aorc, facecolor='none', edgecolor='k', linewidth=1.5)
    ax_aorc.set_title(f'{watershed_name}\nAORC {title_prefix} at {time_value_str}')
    ax_aorc.set_xlabel('')
    ax_aorc.set_ylabel('')

    # Add plot handles for colorbar
    if p_conus: plot_handles.append(p_conus)
    if p_aorc: plot_handles.append(p_aorc)

    # Shared colorbar
    if plot_handles:
        fig.colorbar(plot_handles[-1], ax=axes, orientation='vertical', fraction=0.02, pad=0.02,
                     label=cbar_label)
    
    plt.show()
    
######## metrics

#### Correlation Starts
def compute_pixelwise_correlation(ds1, ds2, threshold=1e-6, min_valid_obs=2):
    """
    Compute pixelwise Pearson correlation between two time-series gridded datasets.
    Filters out pixels with constant or fully-NaN time series.
    
    Parameters:
        ds1, ds2 : xarray.DataArray
            Input data arrays with dimensions [time, y, x].
        threshold : float
            Minimum standard deviation to consider a pixel valid.
        min_valid_obs : int
            Minimum number of valid observations per pixel.

    Returns:
        xarray.DataArray
            Pixelwise correlation values (same spatial dimensions as input).
    """
    # 1. Remove pixels that are all NaN over time in either dataset
    valid_pixel_mask = (ds1.notnull() & ds2.notnull()).any(dim='time')
    ds1 = ds1.where(valid_pixel_mask)
    ds2 = ds2.where(valid_pixel_mask)

    # 2. Identify per-pixel valid observations
    valid_obs = ds1.notnull() & ds2.notnull()
    n_obs = valid_obs.sum(dim='time')
    sufficient_obs = n_obs >= min_valid_obs

    # 3. Compute anomalies
    ds1_mean = ds1.mean(dim='time', skipna=True)
    ds2_mean = ds2.mean(dim='time', skipna=True)
    ds1_anom = ds1 - ds1_mean
    ds2_anom = ds2 - ds2_mean

    # 4. Compute std deviation
    std1 = ds1_anom.std(dim='time', skipna=True, ddof=0)
    std2 = ds2_anom.std(dim='time', skipna=True, ddof=0)

    # 5. Build final valid mask
    good_std = (std1 > threshold) & (std2 > threshold)
    valid_mask = sufficient_obs & good_std

    # 6. Apply final mask before correlation
    ds1_anom = ds1_anom.where(valid_mask)
    ds2_anom = ds2_anom.where(valid_mask)

    # 7. Compute correlation
    numerator = (ds1_anom * ds2_anom).mean(dim='time', skipna=True)
    denominator = std1 * std2
    corr = (numerator / denominator).where(valid_mask)

    # 8. Remove any remaining inf or NaN
    return corr.where(np.isfinite(corr))


def plot_pixelwise_correlation(ds1, ds2, vmin=None, vmax=None, min_std=1e-6, min_valid_obs=2):
    corr = compute_pixelwise_correlation(ds1, ds2, threshold=min_std, min_valid_obs=min_valid_obs)

    # Safe percentile range estimation
    corr_flat = corr.values.flatten()
    corr_flat = corr_flat[np.isfinite(corr_flat)]
    if vmin is None:
        vmin = np.nanpercentile(corr_flat, 2)
    if vmax is None:
        vmax = np.nanpercentile(corr_flat, 98)

    # Plot correlation map
    fig, ax = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [4, 1]})
    im = corr.plot(ax=ax[0], cmap='RdBu_r', vmin=vmin, vmax=vmax,
                   cbar_kwargs={'label': 'Pearson Correlation'})
    ax[0].set_title('Pixelwise Temporal Correlation (CONUS404 vs AORC)')
    ax[0].grid(True)

    # Histogram
    ax[1].hist(corr_flat, bins=30, color='slategray', edgecolor='black')
    ax[1].set_title('Distribution')
    ax[1].set_xlabel('Correlation')
    ax[1].set_ylabel('Pixel Count')
    ax[1].set_ylim(top=ax[1].get_ylim()[1] * 1.1)

    plt.tight_layout()
    plt.show()
    
    return corr

#### Correlation Ends

#### Other metrics
def compute_mean(ds):
    return ds.mean(dim=['y', 'x'])

def compute_std(ds):
    return ds.std(dim=['y', 'x'])

def compute_iqr(ds):
    q75 = ds.quantile(0.75, dim=['y', 'x'])
    q25 = ds.quantile(0.25, dim=['y', 'x'])
    return q75 - q25

def compute_bias(ds1, ds2):
    return (ds1 - ds2).mean(dim='time')

def compute_rmse(ds1, ds2):
    return ((ds1 - ds2) ** 2).mean(dim='time') ** 0.5

def plot_spatial_stats(mean1, mean2, std1, std2, iqr1, iqr2, label1='CONUS404', label2='AORC'):
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # Mean
    mean1.plot(ax=axes[0], label=label1)
    mean2.plot(ax=axes[0], label=label2)
    axes[0].set_title("Spatial Mean")
    axes[0].legend()

    # STD
    std1.plot(ax=axes[1], label=label1)
    std2.plot(ax=axes[1], label=label2)
    axes[1].set_title("Spatial Standard Deviation")
    axes[1].legend()

    # IQR
    iqr1.plot(ax=axes[2], label=label1)
    iqr2.plot(ax=axes[2], label=label2)
    axes[2].set_title("Spatial Interquartile Range (IQR)")
    axes[2].legend()

    plt.xlabel("Time")
    plt.tight_layout()
    plt.show()