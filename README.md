# goes-utils
Utilities for building imagery and videos from GOES-16 data on S3

## Installation

This expects ffmpeg to be installed on your system.

```
$ virtaulenv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

## Included scripts

### nc2png.py

This script takes a local GOES netCDF4 (.nc) file and outputs a true color PNG file.

Usage:

```
python nc2png.py [-h] netcdf_path png_path
```

### video_generator.py

This script, given an start date and end date, downloads GOES data from S3, converts them to PNGs, and creates a video file of the imagesequence.

Usage:

```
$ python video_generator.py [-h] --start-datetime 'YYYY-MM-DD HH:00' --end-datetime 'YYYY-MM-DD HH:00'
                          [--data-dir DATA_DIR] [--processes PROCESSES] [--band {tc,1,2,3}]
                          [--product {ABI-L2-MCMIPF,ABI-L2-MCMIPC,ABI-L2-MCMIPM1,ABI-L2-MCMIPM2}]
                          [--log-level {INFO,DEBUG,WARN,ERROR}]
                          output_path

```

Notes: 

- Only full disk (ABI-L2-MCMIPF) and CONUS (ABI-L2-MCMIPC) are suported at the moment.
- Granularity is hours -- minutes must be 00 in the datetime arguments
- `--band` is not yet supported
- `--data-dir` will allow you to cache .nc and .png files to speed up subsequent runs



