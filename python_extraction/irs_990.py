from irsx.settings import INDEX_DIRECTORY
import os
import sys
import re
import requests
import pandas as pd
from irsx.xmlrunner import XMLRunner
import math

# Function to get the info of the grantees
def get_grantee_info(rows, business_name, business_ein, tax_period, amended_return, return_timestamp, file_name):
  # store the output in this dict
  output = []
  # this section is for grants paid for the current year
  if 'PFGrntOrCntrbtnPdDrYr' in rows.keys():
    # loop through the grant records
    for row in rows['PFGrntOrCntrbtnPdDrYr']:
      # initialize the variables
      name = ''
      address = ''
      city = ''
      state = ''
      zip_code = ''
      purpose = ''
      amount = ''
      # check to see if the fields exists or now and assign the value
      if 'GrntOrCntrbtnPdDrYr_RcpntPrsnNm' in row.keys():
        name = row['GrntOrCntrbtnPdDrYr_RcpntPrsnNm']
      elif 'RcpntBsnssNm_BsnssNmLn1Txt' in row.keys():
        name = row['RcpntBsnssNm_BsnssNmLn1Txt']

      if 'RcpntUSAddrss_AddrssLn1Txt' in row.keys():
        address = row['RcpntUSAddrss_AddrssLn1Txt']
        city = row['RcpntUSAddrss_CtyNm']
        state = row['RcpntUSAddrss_SttAbbrvtnCd']
        # zip code needs to be at least five digits so put in leading zeros if not
        zip_code = row['RcpntUSAddrss_ZIPCd'].zfill(5)

      if 'GrntOrCntrbtnPdDrYr_GrntOrCntrbtnPrpsTxt' in row.keys():
        purpose = row['GrntOrCntrbtnPdDrYr_GrntOrCntrbtnPrpsTxt']

      if 'GrntOrCntrbtnPdDrYr_Amt' in row.keys():
        amount = row['GrntOrCntrbtnPdDrYr_Amt']

      # create the dictionary object and set the Paid key to True 
      # Future_Pay is for the next section so set to False
      outputdata = { 'ein': business_ein,
      'Foundation_Name':business_name,
      'Amended': amended_return,
      'Created': return_timestamp,
      'Grantee': name,
      'Address': address,
      'City': city,
      'State': state,
      'Zip': zip_code,
      'Purpose': purpose,
      'Amount': amount,
      'Paid': 'True',
      'Future_Pay': 'False',
      'Tax_Year': tax_period,
      'File_Name': file_name
      }
      # add the dictionary to the list
      output.append(outputdata)

  # Check to see if the future grants section is present
  if 'PFGrntOrCntrApprvFrFt' in rows.keys():
    # loop through the grants
    for row in rows['PFGrntOrCntrApprvFrFt']:
      # initialize the variables
      name = ''
      address = ''
      city = ''
      state = ''
      zip_code = ''
      purpose = ''
      amount = ''
      # check to see if the keys are present and assign value
      if 'GrntOrCntrApprvFrFt_RcpntPrsnNm' in row.keys():
        name = row['GrntOrCntrApprvFrFt_RcpntPrsnNm']
      elif 'RcpntBsnssNm_BsnssNmLn1Txt' in row.keys():
        name = row['RcpntBsnssNm_BsnssNmLn1Txt']

      if 'RcpntUSAddrss_AddrssLn1Txt' in row.keys():
        address = row['RcpntUSAddrss_AddrssLn1Txt']
        city = row['RcpntUSAddrss_CtyNm']
        state = row['RcpntUSAddrss_SttAbbrvtnCd']
        # zip code needs to be at least five digits so put in leading zeros if not
        zip_code = row['RcpntUSAddrss_ZIPCd'].zfill(5)

      if 'GrntOrCntrApprvFrFt_GrntOrCntrbtnPrpsTxt' in row.keys():
        purpose = row['GrntOrCntrApprvFrFt_GrntOrCntrbtnPrpsTxt']
      
      if 'GrntOrCntrApprvFrFt_Amt' in row.keys():
        amount = row['GrntOrCntrApprvFrFt_Amt']
     
      # create the dictionary object and set the Paid key to False 
      # Future_Pay is set to True
      outputdata = { 'ein': business_ein,
      'Foundation_Name':business_name,
      'Amended': amended_return,
      'Created': return_timestamp,
      'Grantee': name,
      'Address': address,
      'City': city,
      'State': state,
      'Zip': zip_code,
      'Purpose': purpose,
      'Amount': amount,
      'Paid': 'False',
      'Future_Pay': 'True',
      'Tax_Year': tax_period,
      'File_Name': file_name
      }
      # add the dictionary to the list
      output.append(outputdata)
  # this section is for logging files of foundations that didn't give out any grants
  #else:
      #outputdata = {
      #'ein': business_ein,
      #'Foundation_Name':business_name,
      #'Amended': amended_return,
      #'Created': return_timestamp,
      #'Grantee': '',
      #'Address': '',
      #'City': '',
      #'State': '',
      #'Zip': '',
      #'Purpose': '',
      #'Amount': '',
      #'Paid': 'False',
      #'Future_Pay': 'False',
      #'Tax_Year': tax_period,
      #'File_Name': file_name
      #}
      #output.append(outputdata)
  return output

def parse_files(files, i, year):
  grantees = []
  total_990 = 0
  total_990_pf = 0
  #xml_files = []
  foundations = []
  for index, row in files.iterrows():
    try:
      parsed_filing = xml_runner.run_filing(row['OBJECT_ID'])
      schedule_list = parsed_filing.list_schedules()
      business_name = ''# row['TAXPAYER_NAME']
      business_ein = '' #row['EIN']
      tax_period = '' #row['TAX_PERIOD']
      return_timestamp = ''
      return_type = ''
      if 'ReturnHeader990x' in schedule_list:
        # assign some initial values from the input csv
        parsed_sked = parsed_filing.get_parsed_sked('ReturnHeader990x')
        tax_period = parsed_sked[0]['schedule_parts']['returnheader990x_part_i']['RtrnHdr_TxYr']
        business_name = parsed_sked[0]['schedule_parts']['returnheader990x_part_i']['BsnssNm_BsnssNmLn1Txt']
        business_ein = parsed_sked[0]['schedule_parts']['returnheader990x_part_i']['Flr_EIN'].zfill(9)
        return_timestamp = parsed_sked[0]['schedule_parts']['returnheader990x_part_i']['RtrnHdr_RtrnTs']
        return_type = parsed_sked[0]['schedule_parts']['returnheader990x_part_i']['RtrnHdr_RtrnCd']
      else:
        # log if the file has no header and what file it was
        print('no header', row['OBJECT_ID'])
      # if we have a 990PF we can process it
      if ('IRS990PF' in parsed_filing.list_schedules()):
        amended_return = ''
        # check to see if it is an amended return
        if 'AmnddRtrnInd' in parsed_filing.get_parsed_sked('IRS990PF')[0]['schedule_parts']['pf_part_0']:
          amended_return = parsed_filing.get_parsed_sked('IRS990PF')[0]['schedule_parts']['pf_part_0']['AmnddRtrnInd']
        # collect the foundation info
        foundation = {
          'ein':business_ein,
          'business_name':business_name,
          'tax_period':tax_period,
          'return_created': return_timestamp,
          'return_type': return_type,
          'amended_return': amended_return,
          'file_name': row['OBJECT_ID']+'_public.xml'
        }
        # add the dictionary to the list
        foundations.append(foundation)
        # process the rest of the file by first extracting the grantees
        response = get_grantee_info(parsed_filing.get_parsed_sked('IRS990PF')[0]['groups'],business_name,business_ein, tax_period, amended_return, return_timestamp, row['OBJECT_ID']+'_public.xml')
        # add all the responses together
        grantees = grantees + response
        # add one to the processed 990pf count
        total_990_pf += 1
      else:
        # add one to the non 990pf count
        total_990 += 1
    # log any error to a log
    except Exception as e:      
      with open(f'./{year}_log.csv','a') as log:
        log.write(f"{row['OBJECT_ID']},{year},{e}\n")
  #print(f"total 990: {total_990}")
  #print(f"total 990PF: {total_990_pf}")

  #xml_files_df = pd.DataFrame(xml_files)
  #xml_files_df.to_csv('/N/slate/bmowens/grants_and_foundations/xml_'+str(year)+'_990_'+str(i)+'.csv', index=False)
  # load the foundations into a dataframe and save it to a csv
  foundations_df = pd.DataFrame(foundations)
  foundations_df.to_csv('/N/slate/bmowens/grants_and_foundations/foundations_990_'+str(i)+'.csv', index=False)
  # load the grantees into a dataframe and save it to a csv
  df = pd.DataFrame(grantees)
  df.to_csv('/N/slate/bmowens/grants_and_foundations/grantees_'+str(year)+'_990_'+str(i)+'.csv', index=False)
 
# function to download all of the zip files for a particular year
def get_xml_files(year):
    # the starting file count is always 1
    count = 1
    # flag variable to stop downloading 
    valid_file = True
    # get the page that has all of the links to download
    download_page = requests.get("https://www.irs.gov/charities-non-profits/form-990-series-downloads")
    # as long as there is a file to download 
    while valid_file:
        # check to see if the url that we want to download is available
        if download_page.text.find(f"https://apps.irs.gov/pub/epostcard/990/xml/{year}/download990xml_{year}_{count}.zip") != -1:
            # get the zip file
            print(f"downloading file {count} for year {year}")
            get_request = requests.get(f"https://apps.irs.gov/pub/epostcard/990/xml/{year}/download990xml_{year}_{count}.zip", stream=True)
            # as we stream the file write it in chunks to disk
            with open(f"/N/slate/bmowens/grants_and_foundations/{year}_{count}_990.zip", 'wb') as fd:
                for chunk in get_request.iter_content(chunk_size=128):
                    fd.write(chunk)
            # when we are done downloading the file increment the counter and do it again        
            count += 1
        # if we didn't find the link we are looking for then we have downloaded all
        # available zip files from the IRS for that year    
        else:
            valid_file = False

# XMLRunner is our form parser object
xml_runner = XMLRunner()
# what year of zip files are we processing
# 2020 doesn't contain any 2020 tax files only 2019,2018, and 2017 
year = 2020

# if we need to download the files call this function
get_xml_files(year)
# we need to unzip the files from the IRS
os.system("unzip -q -o '*.zip' -d ./xml_files/XML")
print(f'process: {sys.argv[2]} of {sys.argv[1]}')
# create a list of all the files available to process
xml_files = os.listdir('./xml_files/XML/')
for i in range(len(xml_files)):
  xml_files[i] = re.sub('_public\.xml', '', xml_files[i])
# if we are running on Carbonate then we can process the files in parallel
# we need to divide up the work between all of the processes
start = math.floor((len(xml_files)/int(sys.argv[1])) * (int(sys.argv[2]) -1))
end = math.floor((len(xml_files)/int(sys.argv[1])) * (int(sys.argv[2])))
# create a dataframe to use in parsing the files
files_df = pd.DataFrame(data=xml_files, columns=['OBJECT_ID'])
parse_files(files_df.iloc[start:end,:],sys.argv[2], year)
