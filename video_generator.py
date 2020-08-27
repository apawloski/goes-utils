from commonlib.goes import find_scenes_in_date_range, retrieve_scene_by_key, convert_scene_to_png

import argparse
from datetime import datetime
import itertools
import logging
import os
import subprocess
import tempfile

import ffmpeg
import tqdm

from multiprocessing import Pool, current_process, set_start_method, get_context

def main():
    parser = argparse.ArgumentParser(description='Produces a video of GOES scenes between argument start and end datetimes.')
    parser.add_argument('output_path',
                        help='Location for output video file')
    parser.add_argument('--start-datetime', required=True,
                        metavar="'YYYY-MM-DD HH:00'",
                        help='Start in YYYY-MM-DD HH:MM format')
    parser.add_argument('--end-datetime', required=True,
                        metavar="'YYYY-MM-DD HH:00'",
                        help='End in YYYY-MM-DD HH:MM format')
    parser.add_argument('--data-dir', default="./data",
                        help='Desired location of intermediate data')
    parser.add_argument('--processes', type=int, default=1,
                        help='Number of processes to use for scene conversion')
    parser.add_argument('--dpi', type=int, default=600,
                        help='Resolution in DPI')
    parser.add_argument('--band', default="true-color",
                        choices=['tc', '1', '2', '3'],
                        help="Not yet supported")
    parser.add_argument('--satellite', default="noaa-goes16",
                        choices=['noaa-goes16', 'noaa-goes17'],
                        help="Which satellite to use")
    parser.add_argument('--product', default="ABI-L2-MCMIPF",
                        choices=['ABI-L2-MCMIPF', 'ABI-L2-MCMIPC',
                                 'ABI-L2-MCMIPM1', 'ABI-L2-MCMIPM2'],
                        help="Which product to be used -- ONLY ABI-L2-MCMIPF and ABI-L2-MCMIPC supported")
    parser.add_argument('--log-level', default="INFO",
                        choices=["INFO", "DEBUG", "WARN", "ERROR"],
                        help="Log level")
    global args
    args = parser.parse_args()
    logging.basicConfig(level=map_log_level(args.log_level))

    # Search for scenes in time range
    start_dt = datetime.strptime(args.start_datetime, "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(args.end_datetime, "%Y-%m-%d %H:%M")
    if end_dt > start_dt:
        logging.debug(f"Finding scenes between {start_dt} and {end_dt}")
        nc_scenes_list = find_scenes_in_date_range(start_dt,
                                                   end_dt,
                                                   bucket=args.satellite,
                                                   product=args.product)
    else:
        logging.error("Error: Start Date must be before End Date. Exiting.")
        return

    # Download each scene and convert to png
    logging.debug(f"Farming processing to {args.processes} processes")
    pool = Pool(processes=args.processes)
    with get_context('spawn').Pool(processes=args.processes,
                                   initializer=init,
                                   initargs=(args,)) as pool:
        multi_png_paths = list(tqdm.tqdm(pool.imap_unordered(handle_scenes, nc_scenes_list),
                                     total=len(nc_scenes_list)))
    pool.close()
    pool.join()
    png_scenes_list = list(itertools.chain.from_iterable(multi_png_paths))
    png_scenes_list.sort()
    logging.debug("Finished multiprocessing")
    
    # Use ffmpeg to string PNGs into video
    convert_pngs_to_video(png_scenes_list, args.output_path)
    
    return


def convert_pngs_to_video(png_scenes_list, output_path):
    with tempfile.TemporaryDirectory() as dirpath:
        # symlink the pngs so we can use a * glob
        for png in png_scenes_list:
            basename = os.path.basename(png)
            os.symlink(png, os.path.join(dirpath, basename))

        png_links_glob = os.path.join(dirpath, '*.png')
        stream = ffmpeg.input(png_links_glob, pattern_type='glob', framerate=25)
        if args.product != 'ABI-L2-MCMIPC':
            # FD or Mesoscale don't need special filters
            stream = ffmpeg.output(stream,
                                   output_path,
                                   crf=20,
                                   preset='slower',
                                   movflags='faststart')
                       #        pix_fmt='yuv420p') # This works for full disk but breaks CONUS
        else:
            # This is CONUS
            stream = ffmpeg.output(stream,
                                   output_path,
                                   crf=20,
                                   preset='slower',
                                   movflags='faststart',
                                   vf='pad=ceil(iw/2)*2:ceil(ih/2)*2',
                                   pix_fmt='yuv420p'
            )
        ffmpeg.run(stream, overwrite_output=True)
    return


def map_log_level(level):
    return {
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'WARN': logging.WARN,
        'ERROR': logging.ERROR
    }[level]


def handle_scenes(scene):
    png_paths = []
#    logging.debug(f"{current_process().name} Retrieving scene: {scene}")
    local_nc_path = retrieve_scene_by_key(scene, data_dir=args.data_dir, bucket=args.satellite)
    png_path = f"{local_nc_path}.{args.dpi}dpi.png"

    if os.path.isfile(png_path):
 #       logging.debug(f"{current_process().name} Using cached png file at {png_path}")
        pass
    else:
 #       logging.debug(f"{current_process().name} Converting {local_nc_path} to {png_path}")
        # Derive timestamp from filename
        # OR_ABI-L2-MCMIPF-M3_G16_s20181910545433_e20181910556200_c20181910556288.nc
        end_scan = os.path.basename(scene).split('_')[-1]
        dt_string = end_scan[1:15]
        dt = datetime.strptime(dt_string, "%Y%j%H%M%S%f")
        convert_scene_to_png(local_nc_path, png_path, date=f"{dt} UTC", dpi=args.dpi)
        subprocess.call(f"convert -contrast -normalize {png_path} {png_path}", shell=True)
    png_paths.append(png_path)
    return png_paths

def init(n):
    global args
    args = n

if __name__ == "__main__":
#    set_start_method("spawn")
    main()
