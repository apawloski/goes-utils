from commonlib.goes import *

import argparse
from datetime import datetime
import itertools
import logging
from multiprocessing import Pool, current_process
import os
import tempfile

import ffmpeg

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
    parser.add_argument('--band', default="true-color",
                        choices=['tc', '1', '2', '3'],
                        help="Not yet supported")
    parser.add_argument('--product', default="ABI-L2-MCMIPF",
                        choices=['ABI-L2-MCMIPF', 'ABI-L2-MCMIPC',
                                 'ABI-L2-MCMIPM1', 'ABI-L2-MCMIPM2'],
                        help="Which product to be used -- ONLY ABI-L2-MCMIPF and ABI-L2-MCMIPC supported")
    parser.add_argument('--log-level', default="INFO",
                        choices=["INFO", "DEBUG", "WARN", "ERROR"],
                        help="Log level")
    args = parser.parse_args()
    logging.basicConfig(level= map_log_level(args.log_level))
    
    global DATA_DIR
    DATA_DIR = args.data_dir

    # Search for scenes in time range
    start_dt = datetime.strptime(args.start_datetime, "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(args.end_datetime, "%Y-%m-%d %H:%M")
    if end_dt > start_dt:
        logging.debug(f"Finding scenes between {start_dt} and {end_dt}")
        nc_scenes_list = find_scenes_in_date_range(start_dt, end_dt, product=args.product)        
    else:
        logging.error("Error: Start Date must be before End Date. Exiting.")
        return

    # Download each scene and convert to png
    logging.debug(f"Farming processing to {args.processes} processes")
    chunks = [nc_scenes_list[i::args.processes] for i in range(args.processes)]
    pool = Pool(processes=args.processes)
    multi_png_paths = pool.map(handle_scenes, chunks)
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
        stream = ffmpeg.output(stream,
                               output_path,
                               crf=20,
                               preset='slower',
                               movflags='faststart')
#                               pix_fmt='yuv420p') # This works for full disk but breaks CONUS
        ffmpeg.run(stream, overwrite_output=True)
    return

def map_log_level(level):
    return {
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'WARN': logging.WARN,
        'ERROR': logging.ERROR
    }[level]

def handle_scenes(scenes):
    png_paths = []
    for scene in scenes:
        logging.info(f"Processing {scene}")
        logging.debug(f"{current_process().name} Retrieving scene: {scene}")
        local_nc_path = retrieve_scene_by_key(scene, data_dir=DATA_DIR)
        png_path = f"{local_nc_path}.png"

        if os.path.isfile(png_path):
            logging.debug(f"{current_process().name} Using cached png file at {png_path}")
        else:
            logging.debug(f"{current_process().name} Converting {local_nc_path} to {png_path}")
            convert_scene_to_png(local_nc_path, png_path)
            
        png_paths.append(png_path)
    return png_paths

if __name__ == "__main__":
    main()
