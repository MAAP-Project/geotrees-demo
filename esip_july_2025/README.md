# Cloud-Optimized LiDAR: Processing & Visualization Tutorial

This repository provides a hands-on tutorial for processing and visualizing **LiDAR data** using cloud-native formats such as **Cloud-Optimized Point Clouds (COPCs)** and **Cloud-Optimized GeoTIFFs (COGs)**.  

The workflow demonstrates:
1. **LAS → COPC Conversion** (Data Preparation)  
2. **Benchmarking LAS vs COPC** (Efficiency Check)  
3. **Canopy Height Model (CHM) Generation** (Science Product)  
4. **Interactive Visualization** using **Lonboard** & **TiTiler**

Access the notebook online [here](https://notebooksharing.space/view/d9d5aa949a8f4b6e47b60e507f7f6449717f3fcc7ffd38eb05f351f9fccd9785#displayOptions=). 

---

## **Getting Started**

### **Run on Binder (Recommended)**

Click the badge below to launch the tutorial directly in your browser:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/USERNAME/REPONAME/HEAD?filepath=cloud_optimized_lidar_full_merged.ipynb)

*(Replace `USERNAME/REPONAME` with your GitHub repo details.)*

---

### **Local Setup (Optional)**

1. Clone the repository:
   ```bash
   git clone https://github.com/USERNAME/REPONAME.git
   cd REPONAME
   
### **Create the Conda environment**

```bash
conda env create -f environment_final_explicit.yml
conda activate cloud-optimized-lidar

### **Launch JupyterLab**

```bash
jupyter lab

### Authors
Dr. Rajat Shinde – NASA IMPACT / University of Alabama in Huntsville

Dr. Alex Mandel – Development Seed

Chuck Daniels – Development Seed

### Acknowledgments
NASA-ESA MAAP Science Working Group, Development Seed, and contributors to PDAL, Lonboard, and TiTiler.

### License
This tutorial is for educational and research use. Cite appropriately if used.


