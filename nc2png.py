from commonlib.goes import *

import argparse

def main():
    parser = argparse.ArgumentParser(description='Converts a single GOES netCDF file to a single PNG.')
    parser.add_argument('netcdf_path',
                        help='Location of .nc file')
    parser.add_argument('png_path',
                        help='Desired location of output .png')
    args = parser.parse_args()
    
    print(f"Converting netCDF {args.netcdf_path} into PNG {args.png_path}")
    convert_scene_to_png(args.netcdf_path, args.png_path)
    print("Done!")
    
if __name__ == "__main__":
    main()
