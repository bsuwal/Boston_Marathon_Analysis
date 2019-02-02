""" Comments to self:
        The 2015 file is not working correctly
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import seaborn as sns; sns.set()
from datetime import datetime
import numpy as np

def main():
    # load data
    df = pd.read_csv("marathon_results_2017.csv")
    df_2016 = pd.read_csv("marathon_results_2016.csv")
    df = pd.concat([df, df_2016], sort=True)

    # preprocessing
    df["Finish_Time"]= pd.to_datetime(df["Official Time"], format="%H:%M:%S") 

    plot_histogram(df)

    # plot line plots
    start = pd.Timestamp('1900-01-01 02:00:00')
    end = pd.Timestamp('1900-01-01 06:00:00')
    interval = 5
    plot_lineplots(df, start, end, interval)
    

def plot_lineplots(df, start, end, interval):
    """ Plots a lineplot of the runners with their paces (in minute miles)
        vs the distance of marathon run

        Args: df (Dataframe)          - Dataframe containing all runners
          start (Datetime object) - timestamp to start grouping from
          end   (Datetime object) - timestamp to end grouping
          interval (int)          - size of groups in minutes
    """
    runners = group_runners_by_finish_time(df, start, end, interval)

    for i in range(len(runners)):
        ax = sns.lineplot(x="Distances in km", y="Pace in minute mile", data=runners[i])

    annotate_lines(ax, interval, start)
    plt.title(x=0.5, y=1.00, s="Pace of runners over the course of the marathon, grouped by finish times", fontsize=12, weight='bold')
    plt.figtext(.5, 0.82,'Each line is the average runner that finished within a 5 minute chunk\nLower lines are faster',fontsize=10, ha='center')

    plt.savefig("all_runners_lineplot.jpg")
    plt.close()

def annotate_lines(ax, interval, start):
    """ Annotates the lines at the right side of the graph with the group's 
        finish times

        Args:
            ax (Matplotlib fig)
            interval (int)             - Interval in minutes
            start    (Datetime object) - start time of the fastest runner
    """

    # finish time of the first group
    time_stamp = start + pd.Timedelta(minutes=interval)

    for line in ax.lines:
        y = line.get_ydata()[-1]
        hour = "%02d" % time_stamp.hour
        minute = "%02d" % time_stamp.minute
        time = hour + ":" + minute
        ax.annotate(time, xy=(1,y), xytext=(6,0), color=line.get_color(), xycoords = ax.get_yaxis_transform(), textcoords="offset points",
                    size=14, va="center")

        # update time_stamp for the next group
        time_stamp += pd.Timedelta(minutes=interval)

def group_runners_by_finish_time(df, start, end, interval):
    """ Groups runners by finish times of size interval
        Returns an array of dataframes of runners grouped by finish time

        Args: df (Dataframe)          - Dataframe containing all runners
              start (Datetime object) - timestamp to start grouping from
              end   (Datetime object) - timestamp to end grouping
              interval (int)          - size of groups in minutes

        If group + interval > end, ignore that last chunk of time
    """
    group_start = start
    group_end = start + pd.Timedelta(minutes=interval)
    runners = []

    while group_start < end:
        runners.append(get_runners(df, group_start, group_end))

        group_start = group_end
        group_end = group_end + pd.Timedelta(minutes=interval)

    return runners

def plot_histogram(df, num_bins=300):
    """ Plots histogram of the completed time
    """
    fig = df['Finish_Time'].hist(bins=num_bins, color = "skyblue", grid=True, ec="skyblue")
    fig.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    fig.xaxis.set_major_formatter(mdates.DateFormatter('%H'))

    plt.xlabel('Hours after the start')
    plt.ylabel('Number of Finishers')
    plt.title("Histogram of Boston Marathon finishing times 2016 and 2017")
    plt.annotate(s='Everybody wants to \nmake it by 4:00:00!', xy=(pd.Timestamp('1900-01-01 04:00:00'), 800), xytext=(pd.Timestamp('1900-01-01 05:00:00'), 900),
                arrowprops=dict(arrowstyle="->", color="black"));

    # the time stamp starts at 1900-01-01 when converting date-less time to 
    # datetime format
    plt.xlim(pd.Timestamp('1900-01-01 01:00:00'), pd.Timestamp('1900-01-01 07:00:00'))

    plt.savefig("histogram_2016_and_2017.jpg")
    plt.close()
    # plt.show()

def get_runners(df, start, end):
    """ Paces are in minute-miles, as in a '4 minute mile'
    """
    num_km = 5 # space between milestones

    runners = df.loc[(df['Finish_Time'] >= start) & (df['Finish_Time'] < end)]
    
    # clean the data 
    milestones = ["5K", "10K", "15K", "20K", "25K", "30K", "35K", "40K"]
    for m in milestones:
        runners = runners[runners[m] != '-']

    # convert their times to datetime formats
    for m in milestones:
        runners[m]= pd.to_datetime(runners[m], format="%H:%M:%S") 

    # calculate the paces in miles/min
    for i in range(1, len(milestones)):
        time_in_minutes =  (runners[milestones[i]]-runners[milestones[i-1]]).astype('timedelta64[s]') / 60

        # make new columns with paces
        runners[milestones[i]+"_Pace"] = calculate_minute_mile(5, time_in_minutes) 

    # get pace of final 2.2 km / 1.367 miles in minute-miles
    time_in_minutes = (runners["Finish_Time"] - runners["40K"]).astype('timedelta64[s]') / 60
    runners["Finishing_Pace"] = calculate_minute_mile(2.2, time_in_minutes)

    columns = {
        "10K_Pace" : "10",
        "15K_Pace" : "15",
        "20K_Pace" : "20",
        "25K_Pace" : "25",
        "30K_Pace" : "30",
        "35K_Pace" : "35",
        "40K_Pace" : "40",
        "Finishing_Pace": "42.2"
    }

    runners = runners.rename(columns=columns)
    distances = ["10", "15", "20", "25", "30", "35", "40", "42.2"]
    
    final_df = pd.melt(runners, value_vars=distances, var_name="Distances in km", value_name="Pace in minute mile")
    final_df["Distances in km"].astype(float)

    return final_df


def calculate_minute_mile(dist, time):
    """ Calculates and returns a speed in 'minute mile' as in 
        'minute mile' as in "She ran a 4 minute mile"

        Args:
            dist (float) : distance in km
            time (float) : time in minutes
    """
    MILE = 1.60934 # km

    # convert distance to miles
    dist_miles = dist / MILE

    # calculate miles / min speed
    speed = dist_miles / time

    # change speed into minute miles
    minute_mile_speed = 1 / speed

    return minute_mile_speed

if __name__== "__main__":
  main()


