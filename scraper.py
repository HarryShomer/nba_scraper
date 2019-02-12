'''
Date: 2019-01-02
Contributor: Matthew Barlowe
Twitter: @matt_barlowe
Email: barloweanalytics@gmail.com

This file contains the main functions to scrape and compile the NBA api and
return a CSV file of the pbp for the provided game
'''
import json
import requests
import bs4
import pandas as pd

# have to pass this to the requests function or the api will return a 403 code
user_agent = {'User-agent': 'Mozilla/5.0'}

#this will catalog the shot types recorded in the NBA play by play
#not sure how accurate this is it seems to change for the same shots
shot_type_dict = {58: 'turnaround hook shot', 5: 'layup', 6: 'driving layup',
                  96: 'turnaround bank hook shot', 108: 'cutting dunk shot'
                  79: 'pullup jump shot', 72: 'putback layup', 1: 'jump shot',
                  57: 'driving hook shot', 75: 'driving finger roll layup',
                  76: 'running finger roll layup', 79: '3pt shot', 80: '3pt shot',
                  2: '3pt shot', 3: 'hook shot', 98: 'cutting layup', 67: 'hook bank shot',
                  101: 'driving floating jump shot', 102: 'driving floating bank shot jump shot',
                  73: 'driving reverse layup', 63: 'fadeaway jump shot', 47: 'turnaround jump shot',
                  52: 'alley oop dunk', 97: 'tip layup', 66: 'jump bank shot',
                  50: 'running dunk shot', 41: 'running layup', 93: 'driving bank hook shot',
                  87: 'putback dunk shot', 99:'cutting finger roll layup'
                  }

#this dictionary will categorize the event types that happen in the NBA
#play by play
event_type_dict = {1: 'shot', 2: 'missed_shot', 4: 'rebound', 5: 'turnover',
                   20: 'stoppage: out-of-bounds', 6: 'foul', 3: 'free-throw',
                   8: 'substitution', 12: 'period-start', 10: 'jump-ball',
                   9: 'team-timeout', 18: 'instant-replay', 13: 'period-end',
                   7: 'goal-tending', 0: 'game-end'
                  }
def scrape_pbp(game_id, user_agent=user_agent):
    '''
    This function scrapes both of the pbp urls and returns a joined/cleaned
    pbp dataframe

    Inputs:
    game_id - integer id of the nba game you want to scrape in question
    user_agent - this is the user agent to pass to the requests function

    Outputs:
    clean_df - final cleaned dataframe
    '''

#hard coding these in for testing purposes
    v2_api_url = 'https://stats.nba.com/stats/playbyplayv2?EndPeriod=10&EndRange=55800&GameID=0021800549&RangeType=2&Season=2018-19&SeasonType=Regular+Season&StartPeriod=1&StartRange=0kk'
    pbp_api_url = 'https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2018/scores/pbp/0021800549_full_pbp.json'

# this will be the main url used for the v2 api url once testing is done
#v2 api will contain all the player info for each play in the game while the
#pbp_api_url will contain xy coords for each event
#   v2_api_url = 'https://stats.nba.com/stats/playbyplayv2?EndPeriod=10&EndRange=55800&GameID={game_id}&RangeType=2&Season=2018-19&SeasonType=Regular+Season&StartPeriod=1&StartRange=0kk'
#   pbp_api_url = 'https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2018/scores/pbp/{game_id}_full_pbp.json'
# have to pass this to the requests function or the api will return a 403 code
    v2_rep = requests.get(v2_api_url, headers=user_agent)
    v2_dict = v2_rep.json()

#this pulls the v2 stats.nba play by play api
    pbp_v2_headers = v2_dict['resultSets'][0]['headers']
    pbp_v2_data = v2_dict['resultSets'][0]['rowSet']
    pbp_v2_df = pd.DataFrame(pbp_v2_data, columns=pbp_v2_headers)

#this pulls the data.nba api end play by play
    pbp_rep = requests.get(pbp_api_url, headers=user_agent)
    pbp_dict = pbp_rep.json()

#this will be used to concat each quarter from the play by play
    pbp_df_list = []

    for qtr in range(len(pbp_dict['g']['pd'])):
        pbp_df_list.append(pd.DataFrame(pbp_dict['g']['pd'][qtr]['pla']))

#pulling the home and away team abbreviations and the game date
    gcode = pbp_dict['g']['gcode'].split('/')
    date = gcode[0]
    teams = gcode[1]
    home_team = teams[3:]
    away_team = teams[:3]
    pbp_df = pd.concat(pbp_df_list)

#joining the two dataframes together and only pulling in relavent columns
    clean_df = pbp_v2_df.merge(pbp_df[['evt', 'locX', 'locY', 'hs', 'vs', 'de']],
                               left_on = 'EVENTNUM', right_on='evt')

#add date and team abbrev columns to dataframe
    clean_df.loc[:, 'home_team_abbrev'] = home_team_abbrev
    clean_df.loc[:, 'away_team_abbrev'] = away_team_abbrev
    clean_df.loc[:, 'game_date'] = date
    clean_df.loc[:, 'game_date'] = clean_df.loc[:, 'game_date'].astype('datetime64')
    clean_df.loc[:, ('season')] = np.where(clean_df.game_date.dt.month.isin([10, 11, 12]),
                                           clean_df.game_date.dt.year + 1,
                                           clean_df.game_date.dt.year)


#code to properly get the team ids as the scientific notation cuts off some digits
    home_team_id = clean_df[clean_df.PLAYER1_TEAM_ABBREVIATION == home_team_abbrev].PLAYER1_TEAM_ID.astype(int).unique()
    away_team_id = clean_df[clean_df.PLAYER1_TEAM_ABBREVIATION == away_team_abbrev].PLAYER1_TEAM_ID.astype(int).unique()
    clean_df.loc[:, 'home_team_id'] = home_team_id
    clean_df.loc[:, 'away_team_id'] = away_team_id

#create an event team colum
    clean_df['event_team'] = np.where(clean_df['HOMEDESCRIPTION'].isnull(),
                                    clean_df['home_team_abbrev'], clean_df['away_team_abbrev'])

#create and event type description column
    clean_df['event_type_de'] = clean_df[['etype']].replace({'etype': event_type_dict})

#create an event team colum
    clean_df['event_team'] = np.where(clean_df['HOMEDESCRIPTION'].isnull(),
                                      clean_df['home_team_abbrev'],
                                      clean_df['away_team_abbrev'])

#create column whether shot was succesful or not
    def made_shot(row):
    '''
    function to determine whether shot was made or missed

    Input:
    row - pandas row

    Output:
    shot_made - binary variable
    '''

    if row['event_type_de'] == 'shot':
        return 1
    elif row['event_type_de'] == 'missed_shot':
        return 0
    elif (row['event_type_de'] == 'free-throw') & ('Missed' in row['de']):
        return 0
    elif (row['event_type_de'] == 'free-throw') & ('Missed' not in row['de']):
        return 1
    else:
        return np.nan

    clean_df['shot_made'] = clean_df.apply(made_shot, axis=1)

#create a column that says whether the shot was blocked or not
    clean_df['is_block'] = np.where(clean_df.HOMEDESCRIPTION.str.contains('BLOCK') |
                                    clean_df.VISITORDESCRIPTION.str.contains('BLOCK'),
                                    1, 0)
#parse mtype column to get all the shot types being taken
    def parse_shot_types(row):
        '''
        function to parse what type of shot is being taken

        Inputs:
        row - pandas row of play by play dataframe

        Outputs:
        shot_type - returns a shot type of the values hook, jump, layup, dunk, tip
        '''
        if pd.isnull(row['shot_made']) == 0:
            if 'Layup' in row['de']:
                return 'layup'
            elif 'Hook' in row['de']:
                return 'hook'
            elif 'Dunk' in row['de']:
                return 'dunk'
            elif 'Free' in row['de']:
                return 'free'
            else:
                return 'jump'
        else:
            return np.nan
    clean_df['shot_type'] = clean_df.apply(parse_shot_types, axis=1)

#Clean time to get a seconds elapsed column

    def create_seconds_elapsed(row):
        '''
        this function parses the string time column and converts it into game
        seconds elapsed

        Inputs:
        row - row of play by play dataframe

        Outputs:
        time_in_seconds - the elapsed game time expressed in seconds
        '''

        time = row['PCTIMESTRING'].strip()
        time_list = time.split(':')
        max_time = 720
        ot_max_time = 300

        if row['PERIOD'] in [1,2,3,4]:
            time_in_seconds = (max_time - (int(time_list[0]) * 60 + int(time_list[1]))) + (720 * (int(row['PERIOD']) - 1))
        elif row['PERIOD'] > 4:
            time_in_seconds = (ot_max_time - (int(time_list[0]) * 60 + int(time_list[1]))) + (300 * (int(row['PERIOD']) - 5)) + 2880

        return time_in_seconds

    clean_df['seconds_elapsed'] = clean_df.apply(create_seconds_elapsed, axis=1)

#calculate event length of each even in seconds
    clean_df['event_length'] =  clean_df['seconds_elapsed'] - clean_df['seconds_elapsed'].shift(1)

#determine whether shot was a three pointer

    clean_df['is_three'] = np.where(clean_df['de'].str.contains('3pt'), 1, 0)

#determine points earned

    def calc_points_made(row):
        '''
        function to calculate the points earned by a team with each shot made

        Inputs:
        row - row of pbp dataframe

        Outputs - value of shot made
        '''

        if row['is_three'] == 1 and row['shot_made'] == 1:
            return 3
        elif row['is_three'] == 0 and row['shot_made'] == 1 and row['shot_type'] != 'free':
            return 2
        elif row['shot_type'] == 'free':
            return 1
        else:
            return 0

    clean_df['points_made'] = clean_df.apply(calc_points_made, axis=1)

#create columns that determine if rebound is offenseive or deffensive

    clean_df['is_d_rebound'] = np.where((clean_df['event_type_de'] == 'rebound') &
                                         (clean_df['event_team'] != clean_df['event_team'].shift(1)), 1, 0)

    clean_df['is_o_rebound'] = np.where((clean_df['event_type_de'] == 'rebound') &
                                        (clean_df['event_team'] == clean_df['event_team'].shift(1))
                                        & (clean_df['event_type_de'].shift(1) != 'free-throw'), 1, 0)

#create columns to determine turnovers and steals

    clean_df['is_turnover'] = np.where(clean_df['de'].str.contains('Turnover'), 1, 0)
    clean_df['is_steal'] = np.where(clean_df['de'].str.contains('Steal'), 1, 0)

#determine what type of fouls are being commited

    def parse_foul(row):
        '''
        function to determine what type of foul is being commited by the player

        Input:
        row - row of nba play by play

        Output:
        foul_type - the foul type of the fould commited by the player
        '''

        if 'Shooting' in row['de']:
            return 'shooting'
        if 'Personal' in row['de']:
            return 'personal'
        if 'Loose Ball' in row['de']:
            return 'loose_ball'
        if 'Technical' in row['de']:
            return 'technical'
        if 'Charge' in row['de']:
            return 'charge'
        if 'Defense 3 Second' in row['de']:
            return '3 second'
        if 'Flagrant' in row['de']:
            return 'flagrant'
        if 'Flagrant 2' in row['de']:
            return 'flagrant 2'
        else:
            return np.nan

    clean_df['foul_type'] = clean_df.apply(parse_foul, axis=1)

# determine if a shot is a putback off an offensive reboundk
    clean_df['is_putback'] = np.where((clean_df['is_o_rebound'].shift(1) == 1) &
                                      (clean_df['event_length'] <= 3), 1, 0)

#this part gets the lines probably should put this in a function
#since I will need to loop over each period and match them up

    home_lineup_api = ('https://stats.nba.com/stats/leaguedashlineups?Conference=&'
                       f'DateFrom={game_date}&DateTo={game_date}&Division=&'
                       'GameSegment=&GroupQuantity=5&LastNGames=0&LeagueID=&Location=&'
                       f'MeasureType=Base&Month=0&OpponentTeamID={team_id}&Outcome=&PORound=&'
                       f'PaceAdjust=N&PerMode=Totals&Period={period}&PlusMinus=N&Rank=N&'
                       'Season=2018-19&SeasonSegment=&SeasonType=Regular+'
                       'Season&ShotClockRange=&TeamID=&VsConference=&VsDivision=')


    home_lineup_req = requests.get(home_lineup_api, headers=user_agent)
    home_lineup_dict = home_lineup_req.json()

#extract the player ids of each lineup
    lineups = []
    for lineup in home_lineup_dict['resultSets'][0]['rowSet']:
        lineups.append([lineup[1]])

#clean the id strings into a list of ids for each lineup
    for x in range(len(lineups)):
        print(lineups[x][0])
        lineups[x] = list(filter(None,lineups[x][0].split('-')))

#TODO parse mtype column to get all the shot types being taken

#this pulls out the starting lineups from the play by play if every player
#on the court has done something that is recorded by the play by play
#if not then I will need to check the players against the lineups returned
#from the api and weed out which one doesn't fit. This needs to be repeated
#for every period
periods = []
for period in range(1, clean_df['PERIOD'].max()+1):
    #subsets main dataframe by period and subsets into a home and away subs
    period_df = clean_df[clean_df['PERIOD'] == period].reset_index()
    subs_df = period_df[(period_df.event_type_de == 'substitution')]
    away_subs = subs_df[pd.isnull(subs_df.VISITORDESCRIPTION) == 0]
    home_subs = subs_df[pd.isnull(subs_df.HOMEDESCRIPTION) == 0]

    #getting player ids of the players subbed into the game to check against later
    #to determine starting lineups
    away_subbed_players = list(away_subs['PLAYER2_ID'].unique())
    home_subbed_players = list(home_subs['PLAYER2_ID'].unique())
    #gets the index of the first sub for home and away to get the players who started
    #the period by subsetting the dataframe to all actions before the first sub for
    #each team
    away_indexes = list(away_subs.index)
    home_indexes = list(home_subs.index)
    #create variables for the lineup API in case just looking at
    game_date = str(period_df.game_date.unique()[0])[:10]
    away_team_id = period_df.away_team_id.unique()[0]
    home_team_id = period_df.home_team_id.unique()[0]
    api_season = f'{period_df.season.unique()[0]-1}-{str(period_df.season.unique()[0])[2:]}'
    home_lineup_api = ('https://stats.nba.com/stats/leaguedashlineups?Conference=&'
                       f'DateFrom={game_date}&DateTo={game_date}&Division=&'
                       'GameSegment=&GroupQuantity=5&LastNGames=0&LeagueID=&Location=&'
                       f'MeasureType=Base&Month=0&OpponentTeamID={away_team_id}&Outcome=&PORound=&'
                       f'PaceAdjust=N&PerMode=Totals&Period={period}&PlusMinus=N&Rank=N&'
                       f'Season={api_season}&SeasonSegment=&SeasonType=Regular+'
                       'Season&ShotClockRange=&TeamID=&VsConference=&VsDivision=')

    away_lineup_api = ('https://stats.nba.com/stats/leaguedashlineups?Conference=&'
                       f'DateFrom={game_date}&DateTo={game_date}&Division=&'
                       'GameSegment=&GroupQuantity=5&LastNGames=0&LeagueID=&Location=&'
                       f'MeasureType=Base&Month=0&OpponentTeamID={home_team_id}&Outcome=&PORound=&'
                       f'PaceAdjust=N&PerMode=Totals&Period={period}&PlusMinus=N&Rank=N&'
                       f'Season={api_season}&SeasonSegment=&SeasonType=Regular+'
                       'Season&ShotClockRange=&TeamID=&VsConference=&VsDivision=')


    home_lineup_req = requests.get(home_lineup_api, headers=user_agent)

    home_lineup_dict = home_lineup_req.json()

    #extract the player ids of each lineup
    home_lineups = []
    for lineup in home_lineup_dict['resultSets'][0]['rowSet']:
        home_lineups.append([lineup[1]])

    #clean the id strings into a list of ids for each lineup and convert them to ints
    for x in range(len(home_lineups)):
        home_lineups[x] = list(map(int,list(filter(None,home_lineups[x][0].split('-')))))

    away_lineup_req = requests.get(away_lineup_api, headers=user_agent)
    away_lineup_dict = away_lineup_req.json()

    #extract the player ids of each lineup
    away_lineups = []
    for lineup in away_lineup_dict['resultSets'][0]['rowSet']:
        away_lineups.append([lineup[1]])

    #clean the id strings into a list of ids for each lineup and convert them to ints
    for x in range(len(away_lineups)):
        away_lineups[x] = list(map(int,list(filter(None,away_lineups[x][0].split('-')))))
    #looking at the people before the first sub and if
    #it doesn't equal five then continue till next sub excluding the id of the first
    #subbed player and etc. until a list of five players is achieved if five is never
    #achieved by end of period then goto lineup api



    away_starting_line = list(period_df[(period_df.event_team == away_team_abbrev)
                                   & (~pd.isnull(period_df.PLAYER1_NAME))
                                   & (period_df.PLAYER1_TEAM_ABBREVIATION == away_team_abbrev)
                                   & (period_df.is_block == 0)
                                   & (period_df.is_steal == 0)]
                                    .loc[:away_indexes[0], :]['PLAYER1_ID'].unique())

    home_starting_line = list(period_df[(period_df.event_team == home_team_abbrev)
                                   & (~pd.isnull(period_df.PLAYER1_NAME))
                                   & (period_df.PLAYER1_TEAM_ABBREVIATION == home_team_abbrev)
                                   & (period_df.is_block == 0)
                                   & (period_df.is_steal == 0)]
                                    .loc[:home_indexes[0], :]['PLAYER1_ID'].unique())
#theres a large possibility that my catching of posssible lines might return
#two possible lines that fit the criteria in extreme edge cases may have to
#resort to brute forcing it if that happens often
    if len(away_starting_line) < 5:
        possible_away_lines = []
        for x in away_lineups:
            if set(away_starting_line).issubset(x):
                possible_away_lines.append(x)
        if len(possible_away_lines) > 1:
            index = 0
            for line in possible_away_lines:
                for player in line:
                    if player in away_subs and player not in away_starting_line:
                        index = possible_home_lines.index(line)
                possible_home_lines.pop(index)
        away_ids_names = [(x, period_df[period_df['PLAYER1_ID'] == x]['PLAYER1_NAME'].unique()[0]) for x in possible_away_lines[0]]
    else:
        away_ids_names = [(x, period_df[period_df['PLAYER1_ID'] == x]['PLAYER1_NAME'].unique()[0]) for x in away_starting_line]
    #repeating the process for home players
    if len(home_starting_line) < 5:
        possible_home_lines = []
        for x in home_lineups:
            if set(home_starting_line).issubset(x):
                possible_home_lines.append(x)
        if len(possible_home_lines) > 1:
            index = 0
            for line in possible_home_lines:
                for player in line:
                    if player in home_subs and player not in home_starting_line:
                        index = possible_home_lines.index(line)
                possible_home_lines.pop(index)
        home_ids_names = [(x, period_df[period_df['PLAYER1_ID'] == x]['PLAYER1_NAME'].unique()[0]) for x in possible_home_lines[0]]
    else:
        home_ids_names = [(x, period_df[period_df['PLAYER1_ID'] == x]['PLAYER1_NAME'].unique()[0]) for x in home_starting_line]




    for x in range(period_df.shape[0]):
        if period_df.iloc[x, :]['event_type_de'] == 'substitution' and pd.isnull(period_df.iloc[x, :]['VISITORDESCRIPTION']) == 1:
            home_ids_names = [ids for ids in home_ids_names if ids[0] != period_df.iloc[x, :]['PLAYER1_ID']]
            home_ids_names.append((period_df.iloc[x, 21], period_df.iloc[x,22]))
            period_df.iloc[x, 63] = home_ids_names[0][0]
            period_df.iloc[x, 62] = home_ids_names[0][1]
            period_df.iloc[x, 65] = home_ids_names[1][0]
            period_df.iloc[x, 64] = home_ids_names[1][1]
            period_df.iloc[x, 67] = home_ids_names[2][0]
            period_df.iloc[x, 66] = home_ids_names[2][1]
            period_df.iloc[x, 69] = home_ids_names[3][0]
            period_df.iloc[x, 68] = home_ids_names[3][1]
            period_df.iloc[x, 71] = home_ids_names[4][0]
            period_df.iloc[x, 70] = home_ids_names[4][1]
            period_df.iloc[x, 73] = away_ids_names[0][0]
            period_df.iloc[x, 72] = away_ids_names[0][1]
            period_df.iloc[x, 75] = away_ids_names[1][0]
            period_df.iloc[x, 74] = away_ids_names[1][1]
            period_df.iloc[x, 77] = away_ids_names[2][0]
            period_df.iloc[x, 76] = away_ids_names[2][1]
            period_df.iloc[x, 79] = away_ids_names[3][0]
            period_df.iloc[x, 78] = away_ids_names[3][1]
            period_df.iloc[x, 81] = away_ids_names[4][0]
            period_df.iloc[x, 80] = away_ids_names[4][1]
        elif period_df.iloc[x, :]['event_type_de'] == 'substitution' and pd.isnull(period_df.iloc[x, :]['HOMEDESCRIPTION']) == 1:
            away_ids_names = [ids for ids in away_ids_names if ids[0] != period_df.iloc[x, :]['PLAYER1_ID']]
            away_ids_names.append((period_df.iloc[x,21], period_df.iloc[x,22]))
            period_df.iloc[x, 63] = home_ids_names[0][0]
            period_df.iloc[x, 62] = home_ids_names[0][1]
            period_df.iloc[x, 65] = home_ids_names[1][0]
            period_df.iloc[x, 64] = home_ids_names[1][1]
            period_df.iloc[x, 67] = home_ids_names[2][0]
            period_df.iloc[x, 66] = home_ids_names[2][1]
            period_df.iloc[x, 69] = home_ids_names[3][0]
            period_df.iloc[x, 68] = home_ids_names[3][1]
            period_df.iloc[x, 71] = home_ids_names[4][0]
            period_df.iloc[x, 70] = home_ids_names[4][1]
            period_df.iloc[x, 73] = away_ids_names[0][0]
            period_df.iloc[x, 72] = away_ids_names[0][1]
            period_df.iloc[x, 75] = away_ids_names[1][0]
            period_df.iloc[x, 74] = away_ids_names[1][1]
            period_df.iloc[x, 77] = away_ids_names[2][0]
            period_df.iloc[x, 76] = away_ids_names[2][1]
            period_df.iloc[x, 79] = away_ids_names[3][0]
            period_df.iloc[x, 78] = away_ids_names[3][1]
            period_df.iloc[x, 81] = away_ids_names[4][0]
            period_df.iloc[x, 80] = away_ids_names[4][1]
        else:
            period_df.iloc[x, 63] = home_ids_names[0][0]
            period_df.iloc[x, 62] = home_ids_names[0][1]
            period_df.iloc[x, 65] = home_ids_names[1][0]
            period_df.iloc[x, 64] = home_ids_names[1][1]
            period_df.iloc[x, 67] = home_ids_names[2][0]
            period_df.iloc[x, 66] = home_ids_names[2][1]
            period_df.iloc[x, 69] = home_ids_names[3][0]
            period_df.iloc[x, 68] = home_ids_names[3][1]
            period_df.iloc[x, 71] = home_ids_names[4][0]
            period_df.iloc[x, 70] = home_ids_names[4][1]
            period_df.iloc[x, 73] = away_ids_names[0][0]
            period_df.iloc[x, 72] = away_ids_names[0][1]
            period_df.iloc[x, 75] = away_ids_names[1][0]
            period_df.iloc[x, 74] = away_ids_names[1][1]
            period_df.iloc[x, 77] = away_ids_names[2][0]
            period_df.iloc[x, 76] = away_ids_names[2][1]
            period_df.iloc[x, 79] = away_ids_names[3][0]
            period_df.iloc[x, 78] = away_ids_names[3][1]
            period_df.iloc[x, 81] = away_ids_names[4][0]
            period_df.iloc[x, 80] = away_ids_names[4][1]
    periods.append(period_df)

new_df = pd.concat(periods).reset_index()


