import os
from datetime import datetime
from commonlib.goes import retrieve_latest_scene, retrieve_scene_by_key, convert_scene_to_png

def main():
    # Set up directories
    data_dir = "./data"
    output_dir = "./output"
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Retrieve the latest scene key
    latest_scene_key = retrieve_latest_scene()
    
    if latest_scene_key is None:
        print("No recent scenes found.")
        return

    # Download the scene
    nc_file_path = retrieve_scene_by_key(latest_scene_key, data_dir=data_dir)

    # Generate output PNG filename
    current_time = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_png = os.path.join(output_dir, f"goes16_latest_{current_time}.png")

    # Convert the scene to PNG
    convert_scene_to_png(nc_file_path, output_png, date=current_time)

    print(f"Latest GOES-16 observation PNG generated: {output_png}")

if __name__ == "__main__":
    main()
