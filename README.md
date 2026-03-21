# Biomass Reference Map Generation using STAC and COPC

Links to the live notebooks:

1. [Biomass Reference Map Production](https://notebooksharing.space/view/d6a5b475c5c4f9700153bc83d0ac984ed410f1aefd69e74b155e4f2939eff9f5#displayOptions=)
2. [Visualization of Cloud-Optimized Earth Observation Data using Lonboard](https://notebooksharing.space/view/fc90d28c83a45753b66dad2d06683b106f0e341df42f3fe8abbd912f33f6cb11#displayOptions=)
3. [Validation of Meta canopy height over Barro Colorado Island, Panama](https://notebooksharing.space/view/f965981a251729dd58c7d747d752913f791577c6bf29b91f4cf7923405e21683#displayOptions=)
4. [BCI (Barro Colorado Island) Visualization using AGB, Photogrammetry, Trail, and 3D Point Cloud Datasets](https://notebooksharing.space/view/4b3160de355dffdafbb7130c8d21e171bfef5761687a08f66346ab3a0e7517ba#displayOptions=)

This tutorial is divided into four components based on the types of data and analysis workflows used:

1. Python script for LAS-to-COPC conversion: `convert_las_to_copc.py`
2. R notebook for Biomass Reference Map generation using COPC data ingested into MAAP STAC: `biomass_reference_map_v2.ipynb`
3. R notebook for validation of Meta canopy height over Barro Colorado Island, Panama: `Meta_CHM_validation.ipynb`
4. Python notebook for visualization of canopy cover LAS/COPC data together with the biomass map generated in (2) and additional contextual layers: `lonboard-viz.ipynb`

<br />

## Installation

Create the environment using the provided `environment.yml` file:

```bash
conda env create -f environment.yml
conda activate pdal-env

If needed, register the environment as a Jupyter kernel:

```bash
python -m ipykernel install --user --name pdal-env --display-name "Python (pdal-env)"

## Creating Executed Notebooks

To generate an executed notebook for sharing or publication, run:

```bash
jupyter nbconvert --to notebook --execute your_notebook.ipynb \
  --ExecutePreprocessor.kernel_name=pdal-env \
  --output your_notebook_executed.ipynb


You can list available kernels with:

```bash
jupyter kernelspec list