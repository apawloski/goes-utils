# Helper functions for finding GOES netCDF4 files and doing things with them

import datetime
import os
from pathlib import Path

import boto3
from netCDF4 import Dataset
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np

s3 = boto3.client("s3")


def convert_datetime_to_goes_date(dt):
    """Converts datetime to GOES friendly date string"""
    return


def retrieve_scene_by_key(key, data_dir="./data",
                          bucket="noaa-goes16"):
    """Checks cache and then S3 for scene. Downloads (if necessary) and returns location of scene."""
    # TODO: Implement caching
    
    output_path = f"{data_dir}/{key}"

    # If the file does not exist, go get it from S3
    if os.path.isfile(output_path):
        print(f"Using cached nc file at {output_path}")
    else:
        outputdir = os.path.dirname(output_path)
        Path(outputdir).mkdir(parents=True, exist_ok=True)

        s3.download_file(bucket, key, output_path)
    
    return output_path


def find_scenes_in_date_range(start_date, end_date,
                              bucket="noaa-goes16",
                              product='ABI-L2-MCMIPF'):
    """Returns a list of scene keys observed between start and end date. Expects arguments as datetimes"""
    scenes_list = []

    delta = end_date - start_date
    # Floating point to int risk..
    for j in range(0, int(delta.total_seconds()), 3600):
        # Derive S3 location from datetime
        scene_date = start_date + datetime.timedelta(seconds=j)
        scene_date = scene_date.timetuple()
        scene_prefix = f"{product}/{scene_date.tm_year}/{scene_date.tm_yday}/{scene_date.tm_hour:02}/"

        # Append objects at S3 location
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=scene_prefix,
            MaxKeys=100)
        for found_scene in response.get('Contents'):
            scenes_list.append(found_scene['Key'])

    return scenes_list


def convert_scene_to_png(input_nc, output_png, date=None):
    """Converts netCDF4 to a true color PNG file"""
    g16nc = Dataset(input_nc, 'r')
    band1 = g16nc.variables['CMI_C01'][:]
    
    # Get the Blue, Red, and Veggie bands + gamma correct
    ref_blue = np.ma.array(np.sqrt(g16nc.variables['CMI_C01'][:]), mask=band1.mask)
    ref_red = np.ma.array(np.sqrt(g16nc.variables['CMI_C02'][:]), mask=band1.mask)
    ref_veggie = np.ma.array(np.sqrt(g16nc.variables['CMI_C03'][:]), mask=band1.mask)

    # Make the green band using a linear relationship
    ref_green = np.ma.copy(ref_veggie)
    gooddata = np.where(ref_veggie.mask == False)
    ref_green[gooddata] = 0.48358168 * ref_red[gooddata] + 0.45706946 * ref_blue[gooddata] + 0.06038137 * ref_veggie[gooddata]

    # Prepare the Clean IR band by converting brightness temperatures to greyscale values
    cleanir = g16nc.variables['CMI_C13'][:]
    cir_min = 90.0
    cir_max = 313.0
    cleanir_c = (cleanir - cir_min) / (cir_max - cir_min)
    cleanir_c = np.maximum(cleanir_c, 0.0)
    cleanir_c = np.minimum(cleanir_c, 1.0)
    cleanir_c = 1.0 - np.float64(cleanir_c)

    # Make an alpha mask so off Earth alpha = 0
    mask = np.where(band1.mask == True)
    alpha = np.ones(band1.shape)
    alpha[mask] = 0.0
    blended = np.dstack([np.maximum(ref_red, cleanir_c), np.maximum(ref_green, cleanir_c), np.maximum(ref_blue, cleanir_c), alpha])

    # Plot it! Without axis & labels
    fig = plt.figure(figsize=(6,6),dpi=300)
    plt.imshow(blended)
    ax = plt.gca()
    plt.axis('off')

    plt.gca().text(0,0, date,
        horizontalalignment='left',
        verticalalignment='top',
        color="white",
        size=4,
        weight='normal')

    fig.savefig(output_png, facecolor='black', transparent=True, bbox_inches='tight', pad_inches=.1)
    plt.close(fig)
    return
