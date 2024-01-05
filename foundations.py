import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopy as gp
import geopandas as gpd
import pgeocode
from geopy import Nominatim
nomi = pgeocode.Nominatim('us')

raw = pd.read_csv(
    '/Users/llee/Desktop/School/Foundations/2019 Matches for Data Visualizations and Network Analyses_2022.11.11.csv', 
    converters={'Grantee Zip': str, 'f_zip':str, 'g_zipcode_990':str}
    )

raw.columns = ["_".join(x.split(" ")).lower() for x in raw.columns.tolist()]


# Name, state, zip code, ein, NTEE for foundations & grantees
grantee_info = raw[
    ['ein',
    'g_state_990',
    'g_zipcode_990',
    'g_ntee_full',
    'amount']
    ].drop_duplicates().groupby(
    ['ein',
    'g_state_990',
    'g_zipcode_990',
    'g_ntee_full']
    ).agg(
        'sum' ## get total amount of money received for an organization
        ).reset_index().rename(
            columns={
                'g_state_990':'state',
                'g_zipcode_990':'zip',
                'ein':'ein',
                'g_ntee_full':'ntee'}).drop_duplicates().assign(node_type = 'grantee')

foundation_info = raw[
    ['foundation_ein',
    'f_state',
    'f_zip',
    'f_ntee_full',
    'amount']
    ].drop_duplicates().groupby(
        ['foundation_ein',
        'f_state',
        'f_zip',
        'f_ntee_full']
        ).agg(
            'sum' ## get total amount of money given for an organization
            ).apply(
                lambda x: x*-1 ## designate that the money is going out of an entity by making it negative
                ).reset_index().rename(
                    columns = {
                        'f_state':'state',
                        'f_zip':'zip',
                        'foundation_ein':'ein',
                        'f_ntee_full':'ntee'}).drop_duplicates().assign(node_type = 'foundation')

all_nodes = pd.concat([grantee_info,foundation_info]).drop_duplicates().reset_index(drop = True) ## concatenate grantee & foundation information into an all node dataframe
all_zipcodes = all_nodes['zip'].unique() ## get all unique zip codes in data 
zipcodes_information = nomi.query_postal_code( ## query all unique zip codes in data to get lat, lon, etc
    all_zipcodes
    ).rename(
        columns = {
            'postal_code':'zip', 
            'state_code':'queried_state'})[
                ['zip',
                'place_name',
                'queried_state',
                'latitude',
                'longitude']
                ]

## extract zip codes that weren't found from first round (raw input) -- most had > 5 digits, so truncate to standard 5 and try those                
zips_not_found = zipcodes_information[pd.isnull(zipcodes_information.queried_state)].assign(trunc_zip = lambda x: x.zip.str[:5])[['zip','trunc_zip']] 

truncated_zips_not_found = zips_not_found.trunc_zip.unique() #get all unique 5 digit zip codes that weren't found the first time around
zips_not_found_information = nomi.query_postal_code(truncated_zips_not_found).rename(columns = {'postal_code':'trunc_zip', 'state_code':'queried_state'})[['trunc_zip','place_name','queried_state','latitude','longitude']] #query info on truncated zips

round1_found_only = zipcodes_information[~pd.isnull(zipcodes_information.queried_state)] # from first round of search, get only records that were found
round2_found = zips_not_found.merge(zips_not_found_information)[['zip','place_name','queried_state','latitude','longitude']] #from the second round, merge found information back to their raw zip code
all_zip_information = pd.concat([round1_found_only,round2_found]) #combine all of the zip code info

q = all_nodes.merge( ## merge the zip code information to the nodes
    all_zip_information
    ).astype(
        {'state':'str',
        'queried_state':'str'}
        ).assign(
            state_match = lambda x: ((x.state.str.lower() == x.queried_state.str.lower())) ## check to see that the state that the zip code search found is the same as what's recorded in the data for each node
            )

nodes_zip_match = q[q.state_match == True].rename(columns = {'amount':'total_amount'}) #select only records that have matching states

nodes_zip_match['ind'] = nodes_zip_match.sort_values(['latitude','longitude','ein']).groupby(['latitude','longitude'])[['ein']].cumcount() #index of each individual ein in group of lat/lon

coordinate_count = nodes_zip_match.groupby(['latitude','longitude'])[['ein']].agg('count').reset_index() # total count of eins that share each coordinate pair
## coordinates and required rotation to jitter points (necessary because there are multiple entities w/ the same geocoding since we're using zip code. if we can use the coordinates of an actual address then this isn't needed)
coords = coordinate_count.assign(angle = lambda x: (360/x.ein))[['latitude','longitude','angle']] 
jitter_distance = 0.01

n_jittered = nodes_zip_match.merge(
    coords
    ).assign(
        latitude_jittered = lambda x: (x.latitude + (jitter_distance * np.sin(np.radians(x.angle * x.ind)))),
        longitude_jittered = lambda x: (x.longitude + (jitter_distance * np.cos(np.radians(x.angle * x.ind)))))

# get edgelist from raw data

edges = raw[
    ['ein',
    'foundation_ein', 
    'amount',
    'recordid',
    'g_state_990',
    'f_state']
    ].rename(columns = {
        'ein':'g_ein',
        'foundation_ein':'f_ein',
        'g_state_990':'state_to',
        'f_state':'state_from'
        }
        )

# from "master" edgelist, make an edgelist that has grantee information by joining all node information on grantee EIN
edges_grantees = edges.merge(
    n_jittered.rename(
        columns={'ein':'g_ein'}
        )
    ).assign(
        direction = 'in' ## designate direction of edge as going 'in' for grantees
        )

# from "master" edgelist, make an edgelist that has foundation information by joining all node information on foundation EIN
edges_foundations = edges.merge(
    n_jittered.rename(
        columns={'ein':'f_ein'}
        )
    ).assign(
        direction = 'out' ## designate direction of edge as going 'out' for foundations
        )

all_edges = pd.concat(
    [edges_grantees, edges_foundations]
    ).assign(
        in_state = lambda x: (x.state_to.str.lower() == x.state_from.str.lower()) ## designate each donation as in state or out of state based on match of state from/state to
        )[
            ['g_ein',
            'f_ein',
            'amount',
            'recordid',
            'state_to',
            'state_from',
            'state', ## take only relevant info
            'zip',
            'ntee',
            'total_amount',
            'place_name',
            'latitude',
            'longitude',
            'direction',
            'in_state']
            ]

place_to = edges.merge(n_jittered.rename(columns={'ein':'g_ein'})).assign(direction = 'in')[['g_ein','f_ein','recordid', 'place_name']].rename(columns = {'place_name':'place_to'}).drop_duplicates()
place_from = edges.merge(n_jittered.rename(columns={'ein':'f_ein'})).assign(direction = 'out')[['g_ein','f_ein','recordid', 'place_name']].rename(columns = {'place_name':'place_from'}).drop_duplicates()

out = all_edges.merge(place_from.merge(place_to), how = 'left')

## RETURN
out



