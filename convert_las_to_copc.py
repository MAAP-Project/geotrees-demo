import pdal 
import glob
import os

# Replace this by path to las files
path = "./data/ALS_ground_copc/outputs/norm/*.las"

list_files = glob.glob(path)
list_files = sorted(list_files)

for f in list_files:
    # print(f)
    
    copc_filename = f.replace('.las', '.copc.laz')
    try:
        if os.path.exists(copc_filename):
            # print("already present - {}".format(copc_filename))
            pass

        else:

            pipeline = pdal.Reader.las(filename=f) | pdal.Writer.copc(filename=copc_filename)
            pipeline.execute()
    except:
        print(f)