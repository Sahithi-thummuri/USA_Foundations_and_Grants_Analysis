# Grants and Foundations
## Python extraction
### Background
This process was developed to process the XML files from the IRS website of all public and private foundations. The main focus with this code was to process the 990PF form from private foundations and extract the grants that they distributed. This code was designed to run on the IU high performance computer Carbonate and runs in parallel. 

### Requirments
You will need all of the libraries that the script uses to run it correctly. There is a `requirements.txt` that you should be able to use with pip to install the versions that were used. You will also need to have access to Carbonate if you want to use the script in parallel, while this isn't a hard requirement we found that it was easier to schedule the execution and continue to work on other things instead of having a personal computer running all night. 

### Needed changes
You will have to make sure that you change all file paths that are in the scripts to be specific to you. This might be a good enhancement to make it a little more dynamic. 
You will also have to change the `irs_990.script` file to email you as well as any path info there as well.

### Running the extraction
All you should have to do is run `sbatch irs_990.script` on the Carbonate system to schedule the python script with 10 running processes. If you already have the files downloaded and available then there is no need to download them again so just comment out those lines. 

## Merging the files
### Background
This file should be ran after you have processes all of the 990 XML files, right after the `irs_990.script` has finished running. This file will find all of the grantee and foundation files that the processes have created and merge them all into one master grantee file and one master foundation file. 

### Requirements
Only pandas is required and should be included in the `requirements.txt` file.

### Running the file
You should be able to run the file on it's own by using the command `python3 merge_files.py` 
