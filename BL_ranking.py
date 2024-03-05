#!/usr/bin/env python
# coding: utf-8

# turn time format from result file to integer number
def time2seconds(time):
    splittime = time.split(':')
    seconds = int(splittime[0])*3600 + int(splittime[1])*60 + int(splittime[2])
    return seconds


# read file into a list
def read_file(file,discipline):
    filename = sex+'/'+file
    data = []
    j = 6
    if discipline == 'swim':
        j = 1
    elif discipline == 't1':
        j = 2
    elif discipline == 'bike':
        j = 3
    elif discipline == 't2':
        j = 4
    elif discipline == 'run':
        j = 5
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the first line
        next(reader)  # Skip the second line
        if discipline != 'transition':
            data = [[unicodedata.normalize('NFC',row[0]),time2seconds(row[j])] if time2seconds(row[j]) > 1 else [unicodedata.normalize('NFC',row[0]),99999] for row in reader]
        else:
            data = [[unicodedata.normalize('NFC',row[0]),time2seconds(row[2])+time2seconds(row[4])] if time2seconds(row[2]) > 1 and time2seconds(row[4]) > 1 else [unicodedata.normalize('NFC',row[0]),99999] for row in reader]
    data = sorted(data, key=lambda x: x[1])
    if data[0][1] == 99999:
        return []
    return data


# compare two performances from different races by comparing against the same opponents
def compare(timeA,resultsA,timeB,resultsB):
    namesA = [name for name,time in resultsA]
    namesB = [name for name,time in resultsB]
    timesA = [time for name,time in resultsA if name in namesB]
    timesB = [time for name,time in resultsB if name in namesA]
    betterA = sum([True for time in timesA if time < timeA])
    worseA = sum([True for time in timesA if time > timeA])
    betterB = sum([True for time in timesB if time < timeB])
    worseB = sum([True for time in timesB if time > timeB])
    # rank x2-1 --> 1->1, 2->3, within overlap!
    overlap = len(timesA)
    rankAmin = min(1,overlap-betterA-worseA)+2*betterA 
    rankAmax = (overlap-worseA)*2-min(1,overlap-betterA-worseA)
    rankBmin = min(1,overlap-betterB-worseB)+2*betterB
    rankBmax = (overlap-worseB)*2-min(1,overlap-betterB-worseB)
    if rankAmax < rankBmin:
        return 1 # A better
    elif rankBmax < rankAmin:
        return -1 # B better
    else:
        return 0 # unclear


# compare two performances from different races by comparing against the same opponents
def compare_times(results,i,j,indices):
    resultsA = results[i]
    timeA = resultsA[indices[i]][1]
    athleteA = resultsA[indices[i]][0]
    resultsB = results[j]
    timeB = resultsB[indices[j]][1]
    athleteB = resultsB[indices[j]][0]
    namesA = [name for name,time in resultsA]
    namesB = [name for name,time in resultsB]
    timesA = [time for name,time in resultsA if name in namesB]
    if len(timesA) > 0: # direct overlap
        timesB = [time for name,time in resultsB if name in namesA]
        betterA = sum([True for time in timesA if time < timeA])
        bettereqA = sum([True for time in timesA if time <= timeA])
        betterB = sum([True for time in timesB if time < timeB])
        bettereqB = sum([True for time in timesB if time <= timeB])
        if betterA + bettereqA < betterB + bettereqB: # A better
            return 1
        if betterB + bettereqB < betterA + bettereqA: # B better
            return -1
        rankA = 0
        rankB = 0
        if bettereqA > 0:
            low = int((betterA+bettereqA)/2-0.2)
        else:
            low = -1
        high = int((betterA+bettereqA)/2+0.2)
        while rankA > rankB - 1e-10 and rankA < rankB + 1e-10: # while equal
            if low >= 0 and high < len(timesA):
                if timesA[high]-timesA[low] > 0.5:
                    rankA = (timeA-timesA[low])/(timesA[high]-timesA[low])*(high-low)+low+1
                else:
                    rankA = (high+low)/2.+1
                if timesB[high]-timesB[low] > 0.5:
                    rankB = (timeB-timesB[low])/(timesB[high]-timesB[low])*(high-low)+low+1
                else:
                    rankB = (high+low)/2.+1
            elif high < len(timesA): # low < 0
                rankA = timeA/timesA[high]*(high+1)
                rankB = timeB/timesB[high]*(high+1)
            elif low >= 0: # high >= len(timesA):
                rankA = timeA/timesA[low]*(low+1)
                rankB = timeB/timesB[low]*(low+1)
            else: # low < 0 and high >= len(timesA)
                break # really equal
            high += 1
            low -= 1
        if rankA < rankB - 1e-10: # A better
            return 1
        if rankA > rankB + 1e-10: # B better
            return -1
    # caluclate overlap for any other race
    all_racesA = [i]
    all_timesA = [timeA]
    all_racesB = [j]
    all_timesB = [timeB]
    racesA_new = []
    timesA_new = []
    racesB_new = []
    timesB_new = []
    for k in range(len(results)): # k is index within results for the new result
        athletes_k = [name for name,time in results[k]]
        if k not in all_racesA:
            times_tmp = []
            for m,l in enumerate(all_racesA): # m is the index within all_racesA, l within results
                timeA_l = all_timesA[m]
                athletes_l = [name for name,time in results[l]]
                times_k = [time for name,time in results[k] if name in athletes_l]
                times_l = [time for name,time in results[l] if name in athletes_k]
                if len(times_k) > 0:
                    faster = sum([True for time in times_l if time < all_timesA[m]])
                    fastereq = sum([True for time in times_l if time <= all_timesA[m]])
                    if fastereq-faster == 1:
                        new_time = times_k[faster]
                    elif fastereq > faster:
                        new_time = np.median(np.array(times_k[faster:fastereq]))
                    elif faster == 0:
                        new_time = all_timesA[m]/times_l[0]*times_k[0]
                    elif faster == len(times_k):
                        new_time = all_timesA[m]/times_l[-1]*times_k[-1]
                    else:
                        new_time = (all_timesA[m]-times_l[faster-1])/(times_l[faster]-times_l[faster-1])*(times_k[faster]-times_k[faster-1])+times_k[faster-1]
                    times_tmp.append(new_time)
            if len(times_tmp) > 0:
                racesA_new.append(k)
                timesA_new.append(np.median(np.array(times_tmp)))
        if k not in all_racesB:
            times_tmp = []
            for m,l in enumerate(all_racesB): # m is the index within all_racesA, l within results
                timeB_l = all_timesB[m]
                athletes_l = [name for name,time in results[l]]
                times_k = [time for name,time in results[k] if name in athletes_l]
                times_l = [time for name,time in results[l] if name in athletes_k]
                if len(times_k) > 0:
                    faster = sum([True for time in times_l if time < all_timesB[m]])
                    fastereq = sum([True for time in times_l if time <= all_timesB[m]])
                    if fastereq-faster == 1:
                        new_time = times_k[faster]
                    elif fastereq > faster:
                        new_time = np.median(np.array(times_k[faster:fastereq]))
                    elif faster == 0:
                        new_time = all_timesB[m]/times_l[0]*times_k[0]
                    elif faster == len(times_k):
                        new_time = all_timesB[m]/times_l[-1]*times_k[-1]
                    else:
                        new_time = (all_timesB[m]-times_l[faster-1])/(times_l[faster]-times_l[faster-1])*(times_k[faster]-times_k[faster-1])+times_k[faster-1]
                    times_tmp.append(new_time)
            if len(times_tmp) > 0:
                racesB_new.append(k)
                timesB_new.append(np.median(np.array(times_tmp)))
    for k in range(len(racesA_new)):
        all_racesA.append(racesA_new[k])
        all_timesA.append(timesA_new[k])
    for k in range(len(racesB_new)):
        all_racesB.append(racesB_new[k])
        all_timesB.append(timesB_new[k])
    ratios = []
    for k in range(len(all_racesA)):
        for l in range(len(all_racesB)):
            if all_racesA[k] == all_racesB[l]:
                ratios.append(all_timesA[k]/all_timesB[l])
    if len(ratios) > 0:
        medianratio = np.median(np.array(ratios))
        if medianratio < 1-1e-10: # A better
            return 1
        if medianratio > 1+1e-10: # B better
            return -1
        else:
            ratios = sorted(ratios)
            low = int(len(ratios)/2-0.2)
            high = int(len(ratios)/2+0.2)
            while low >= 0 and medianratio > 1-1e-10 and medianratio < 1+1e-10:
                medianratio = (ratios[low]+ratios[high])/2.
                low -= 1
                high += 1
            if medianratio < 1-1e-10: # A better
                return 1
            if medianratio > 1+1e-10: # B better
                return -1
            else:
                1/0 # edge case that normally doesn't occur. If it does ever happen -> stop execution and think about how to handle it
    else:
        1/0 # edge case that normally doesn't occur. If it does ever happen -> stop execution and think about how to handle it


# compare three performances from different races by comparing against the same opponents

def compare_three_times(results,i1,i2,i3,indices):
    resultsA = results[i1]
    timeA = resultsA[indices[i1]][1]
    athleteA = resultsA[indices[i1]][0]
    resultsB = results[i2]
    timeB = resultsB[indices[i2]][1]
    athleteB = resultsB[indices[i2]][0]
    resultsC = results[i3]
    timeC = resultsC[indices[i3]][1]
    athleteC = resultsC[indices[i3]][0]
    namesA = [name for name,time in resultsA]
    namesB = [name for name,time in resultsB]
    namesC = [name for name,time in resultsC]
    timesA = [time for name,time in resultsA if name in namesB and name in namesC]
    if len(timesA) > 0: # direct overlap
        timesB = [time for name,time in resultsB if name in namesA and name in namesC]
        timesC = [time for name,time in resultsC if name in namesA and name in namesB]
        betterA = sum([True for time in timesA if time < timeA])
        bettereqA = sum([True for time in timesA if time <= timeA])
        betterB = sum([True for time in timesB if time < timeB])
        bettereqB = sum([True for time in timesB if time <= timeB])
        betterC = sum([True for time in timesC if time < timeC])
        bettereqC = sum([True for time in timesC if time <= timeC])
        if betterA + bettereqA > max(betterB+bettereqB,betterC+bettereqC): # A worst
            compareBC = compare_times(results,i2,i3,indices)
            if compareBC == 1:
                return 2
            else:
                return 3
        if betterB + bettereqB > max(betterA+bettereqA,betterC+bettereqC): # B worst
            compareAC = compare_times(results,i1,i3,indices)
            if compareAC == 1:
                return 1
            else:
                return 3
        if betterC + bettereqC > max(betterA+bettereqA,betterB+bettereqB): # B worst
            compareAB = compare_times(results,i1,i2,indices)
            if compareAB == 1:
                return 1
            else:
                return 2
        if betterA + bettereqA < min(betterB+bettereqB,betterC+bettereqC): # A best
            return 1
        if betterB + bettereqB < min(betterA+bettereqA,betterC+bettereqC): # B best
            return 2
        if betterC + bettereqC < min(betterA+bettereqA,betterB+bettereqB): # C best
            return 3
        # --> A,B,C equal
        rankA = 0
        rankB = 0
        rankC = 0
        if bettereqA > 0:
            low = int((betterA+bettereqA)/2-0.2)
        else:
            low = -1
        high = int((betterA+bettereqA)/2+0.2)
        while rankA > rankB - 1e-10 and rankA < rankB + 1e-10 and rankA > rankC - 1e-10 and rankA < rankC + 1e-10: # while all equal
            if low >= 0 and high < len(timesA):
                if timesA[high]-timesA[low] > 0.5:
                    rankA = (timeA-timesA[low])/(timesA[high]-timesA[low])*(high-low)+low+1
                else:
                    rankA = (high+low)/2.+1
                if timesB[high]-timesB[low] > 0.5:
                    rankB = (timeB-timesB[low])/(timesB[high]-timesB[low])*(high-low)+low+1
                else:
                    rankB = (high+low)/2.+1
                if timesC[high]-timesC[low] > 0.5:
                    rankC = (timeC-timesC[low])/(timesC[high]-timesC[low])*(high-low)+low+1
                else:
                    rankC = (high+low)/2.+1
            elif high < len(timesA): # low < 0
                rankA = timeA/timesA[high]*(high+1)
                rankB = timeB/timesB[high]*(high+1)
                rankC = timeC/timesC[high]*(high+1)
            elif low >= 0: # high >= len(timesA):
                rankA = timeA/timesA[low]*(low+1)
                rankB = timeB/timesB[low]*(low+1)
                rankC = timeC/timesC[low]*(low+1)
            else: # low < 0 and high >= len(timesA)
                break # really equal
            high += 1
            low -= 1
        if rankA > max(rankB,rankC) + 1e-10: # A worst
            compareBC = compare_times(results,i2,i3,indices)
            if compareBC == 1:
                return 2
            else:
                return 3
        if rankB > max(rankA,rankC) + 1e-10: # B worst
            compareAC = compare_times(results,i1,i3,indices)
            if compareAC == 1:
                return 1
            else:
                return 3
        if rankC > max(rankA,rankB) + 1e-10: # C worst
            compareAB = compare_times(results,i1,i2,indices)
            if compareAB == 1:
                return 1
            else:
                return 2
        if rankA < min(rankB,rankC) - 1e-10: # A best
            return 1
        if rankB < min(rankA,rankC) - 1e-10: # B best
            return 2
        if rankC < min(rankA,rankB) - 1e-10: # C best
            return 3        
    # caluclate overlap for any other race
    all_racesA = [i1]
    all_timesA = [timeA]
    all_racesB = [i2]
    all_timesB = [timeB]
    all_racesC = [i3]
    all_timesC = [timeC]
    racesA_new = []
    timesA_new = []
    racesB_new = []
    timesB_new = []
    racesC_new = []
    timesC_new = []
    for k in range(len(results)): # k is index within results for the new result
        athletes_k = [name for name,time in results[k]]
        if k not in all_racesA:
            times_tmp = []
            for m,l in enumerate(all_racesA): # m is the index within all_racesA, l within results
                timeA_l = all_timesA[m]
                athletes_l = [name for name,time in results[l]]
                times_k = [time for name,time in results[k] if name in athletes_l]
                times_l = [time for name,time in results[l] if name in athletes_k]
                if len(times_k) > 0:
                    faster = sum([True for time in times_l if time < all_timesA[m]])
                    fastereq = sum([True for time in times_l if time <= all_timesA[m]])
                    if fastereq-faster == 1:
                        new_time = times_k[faster]
                    elif fastereq > faster:
                        new_time = np.median(np.array(times_k[faster:fastereq]))
                    elif faster == 0:
                        new_time = all_timesA[m]/times_l[0]*times_k[0]
                    elif faster == len(times_k):
                        new_time = all_timesA[m]/times_l[-1]*times_k[-1]
                    else:
                        new_time = (all_timesA[m]-times_l[faster-1])/(times_l[faster]-times_l[faster-1])*(times_k[faster]-times_k[faster-1])+times_k[faster-1]
                    times_tmp.append(new_time)
            if len(times_tmp) > 0:
                racesA_new.append(k)
                timesA_new.append(np.median(np.array(times_tmp)))
        if k not in all_racesB:
            times_tmp = []
            for m,l in enumerate(all_racesB): # m is the index within all_racesA, l within results
                timeB_l = all_timesB[m]
                athletes_l = [name for name,time in results[l]]
                times_k = [time for name,time in results[k] if name in athletes_l]
                times_l = [time for name,time in results[l] if name in athletes_k]
                if len(times_k) > 0:
                    faster = sum([True for time in times_l if time < all_timesB[m]])
                    fastereq = sum([True for time in times_l if time <= all_timesB[m]])
                    if fastereq-faster == 1:
                        new_time = times_k[faster]
                    elif fastereq > faster:
                        new_time = np.median(np.array(times_k[faster:fastereq]))
                    elif faster == 0:
                        new_time = all_timesB[m]/times_l[0]*times_k[0]
                    elif faster == len(times_k):
                        new_time = all_timesB[m]/times_l[-1]*times_k[-1]
                    else:
                        new_time = (all_timesB[m]-times_l[faster-1])/(times_l[faster]-times_l[faster-1])*(times_k[faster]-times_k[faster-1])+times_k[faster-1]
                    times_tmp.append(new_time)
            if len(times_tmp) > 0:
                racesB_new.append(k)
                timesB_new.append(np.median(np.array(times_tmp)))
        if k not in all_racesC:
            times_tmp = []
            for m,l in enumerate(all_racesC): # m is the index within all_racesA, l within results
                timeC_l = all_timesC[m]
                athletes_l = [name for name,time in results[l]]
                times_k = [time for name,time in results[k] if name in athletes_l]
                times_l = [time for name,time in results[l] if name in athletes_k]
                if len(times_k) > 0:
                    faster = sum([True for time in times_l if time < all_timesC[m]])
                    fastereq = sum([True for time in times_l if time <= all_timesC[m]])
                    if fastereq-faster == 1:
                        new_time = times_k[faster]
                    elif fastereq > faster:
                        new_time = np.median(np.array(times_k[faster:fastereq]))
                    elif faster == 0:
                        new_time = all_timesC[m]/times_l[0]*times_k[0]
                    elif faster == len(times_k):
                        new_time = all_timesC[m]/times_l[-1]*times_k[-1]
                    else:
                        new_time = (all_timesC[m]-times_l[faster-1])/(times_l[faster]-times_l[faster-1])*(times_k[faster]-times_k[faster-1])+times_k[faster-1]
                    times_tmp.append(new_time)
            if len(times_tmp) > 0:
                racesC_new.append(k)
                timesC_new.append(np.median(np.array(times_tmp)))
    for k in range(len(racesA_new)):
        all_racesA.append(racesA_new[k])
        all_timesA.append(timesA_new[k])
    for k in range(len(racesB_new)):
        all_racesB.append(racesB_new[k])
        all_timesB.append(timesB_new[k])
    for k in range(len(racesC_new)):
        all_racesC.append(racesC_new[k])
        all_timesC.append(timesC_new[k])
    ratiosA = []
    ratiosB = []
    ratiosC = []
    for k in range(len(all_racesA)):
        for l in range(len(all_racesB)):
            if all_racesA[k] == all_racesB[l]:
                for m in range(len(all_racesC)):
                    if all_racesA[k] == all_racesC[m]:
                        ratiosA.append(all_timesA[k]/min(all_timesB[l],all_timesC[m]))
                        ratiosB.append(all_timesB[l]/min(all_timesA[k],all_timesC[m]))
                        ratiosC.append(all_timesC[m]/min(all_timesA[k],all_timesB[l]))
    if len(ratiosA) > 0:
        medianratioA = np.median(np.array(ratiosA))
        medianratioB = np.median(np.array(ratiosB))
        medianratioC = np.median(np.array(ratiosC))
        if medianratioA > max(medianratioB,medianratioC)+1e-10: # A worst
            compareBC = compare_times(results,i2,i3,indices)
            if compareBC == 1:
                return 2
            else:
                return 3
        if medianratioB > max(medianratioA,medianratioC)+1e-10: # B worst
            compareAC = compare_times(results,i1,i3,indices)
            if compareAC == 1:
                return 1
            else:
                return 3
        if medianratioC > max(medianratioA,medianratioB)+1e-10: # C worst
            compareAB = compare_times(results,i1,i2,indices)
            if compareAB == 1:
                return 1
            else:
                return 2
        if medianratioA < min(medianratioB,medianratioC)-1e-10: # A best
            return 1
        elif medianratioB < min(medianratioA,medianratioC)-1e-10: # B best
            return 2
        elif medianratioC < min(medianratioA,medianratioB)-1e-10: # C best
            return 3
        else:
            1/0 # edge case that normally doesn't occur. If it does ever happen -> stop execution and think about how to handle it
    else:
        1/0 # edge case that normally doesn't occur. If it does ever happen -> stop execution and think about how to handle it


# In[537]:


sex = 'f' # f or m
import os
import csv
import numpy as np
import unicodedata
from collections import defaultdict
import pandas as pd
files = [file for file in os.listdir(sex) if not file.startswith('.')]
files_by_category = [[file for file in files if '23' in file],[file for file in files if '22' in file],[file for file in files if '21' in file]]
final_names = []
final_ratings = []
for discipline in ['overall','swim','bike','run','transition']:
    print(discipline)
    ranking = [] 
    results = [[] for category in files_by_category]
    for i,category in enumerate(files_by_category):
        for file in category:
            results[i].append(read_file(file,discipline))
    all_results = [result for category in results for result in category]
    all_files = [file for category in files_by_category for file in category]
    athletes23 = np.unique(np.array([name for result in results[0] for name,time in result if time < 99999]))
    athletes_tmp = []
    athletes_relevant = []
    for result in all_results:
        for name,time in result:
            if name in athletes23 and name not in athletes_relevant and time < 99999:
                if name in athletes_tmp:
                    athletes_relevant.append(name)
                else:
                    athletes_tmp.append(name)
    # compare results (rank vs same opponents)
    indices = np.zeros(len(all_results),dtype=int)
    while True:
        candidates = np.ones(len(indices),dtype=bool)
        for i in range(len(indices)):
            if indices[i] == len(all_results[i]) or all_results[i][indices[i]][1] == 99999:
                candidates[i] = False
        if sum(candidates) == 0:
            break
        head2head = np.zeros((len(indices),len(indices)),dtype=int)
        for i in range(len(indices)-1):
            for j in range(i+1,len(indices)):
                if not candidates[i]:
                    head2head[i,j] = -1
                    continue
                if not candidates[j]:
                    head2head[j,i] = -1
                    continue
                comparison = compare(all_results[i][indices[i]][1],all_results[i],all_results[j][indices[j]][1],all_results[j])
                head2head[i,j] = comparison
                head2head[j,i] = -comparison
        sums = np.array([sum(head2head[i,:]) for i in range(len(indices))])
        notcandidates = np.where((sums < 0))[0]
        while len(notcandidates) > 0:
            for i in notcandidates:
                head2head[i,:] = 0
                head2head[:,i] = 0
                candidates[i] = False
            sums = np.array([sum(head2head[i,:]) for i in range(len(indices))])
            notcandidates = np.where(sums < 0)[0]
        winners_list = []
        for i in np.where(candidates)[0]:
            time_tmp = all_results[i][indices[i]][1]
            for name_tmp in [name for name,time in all_results[i][indices[i]:] if time == time_tmp]:
                winners_list.append(name_tmp)
        winners = np.unique(np.array(winners_list))
        # direct comparisons (with 2023 as priority)
        while True:
            head2head2 = np.zeros((len(winners),len(winners)),dtype=int)
            for category in results:
                for result in category:
                    winners_in_race = [[name,time] for name,time in result if name in winners]
                    for winner,winnertime in winners_in_race:
                        if winnertime > winners_in_race[0][1]: # not a winner if slower than fastest athlete
                            break
                        for loser,losertime in winners_in_race:
                            if losertime == winners_in_race[0][1]: # not a loser if as fast as fastest athlete
                                continue
                            head2head2[np.where(winners==winner)[0][0],np.where(winners==loser)[0][0]] += 1
                            head2head2[np.where(winners==loser)[0][0],np.where(winners==winner)[0][0]] -= 1
                sums2 = np.array([sum(head2head2[i,:]) for i in range(len(winners))])
                notwinners = np.where((sums2 < 0))[0]
                if len(notwinners) > 0:
                    winners = np.array([winners[i] for i in range(len(winners)) if i not in notwinners])            
                    break # restart
            if len(notwinners) == 0: # if at the end still no change
                break
        for i in range(len(all_results)): # remove all not-winners from candidates
            if not candidates[i]:
                continue
            if all_results[i][indices[i]][0] not in winners:
                j = 1 # check if other athletes with same time are still in winners
                keep = False
                if indices[i]+j < len(all_results[i]):
                    while all_results[i][indices[i]][1] == all_results[i][indices[i]+j][1]:
                        if all_results[i][indices[i]+j][0] in winners: # in this case keep this race as candidate
                            keep = True
                            break
                        j += 1
                        if indices[i]+j == len(all_results[i]):
                            break
                if keep:
                    continue
                candidates[i] = False
        # compare times
        head2head = np.zeros((len(indices),len(indices)),dtype=int)
        for i in range(len(indices)-1):
            if candidates[i]:
                for j in range(i+1,len(indices)):
                    if candidates[j]:
                        comparison = compare_times(all_results,i,j,indices)
                        head2head[i,j] = comparison
                        head2head[j,i] = -comparison
        sums = np.array([sum(head2head[i,:]) for i in range(len(indices))])
        notcandidates = np.where((sums < 0))[0]
        while len(notcandidates) > 0:
            for i in notcandidates:
                head2head[i,:] = 0
                head2head[:,i] = 0
                candidates[i] = False
            sums = np.array([sum(head2head[i,:]) for i in range(len(indices))])
            notcandidates = np.where(sums < 0)[0]
        # compare three times at once
        if sum(candidates) != 1:
            head2head3 = np.zeros((len(indices),len(indices)),dtype=int)
            for i in range(len(indices)-2):
                if candidates[i]:
                    for j in range(i+1,len(indices)-1):
                        if candidates[j]:
                            for k in range(j+1,len(indices)):
                                if candidates[k]:
                                    comparison = compare_three_times(all_results,i,j,k,indices)
                                    if comparison == 1:
                                        head2head3[i,j] = 1
                                        head2head3[i,k] = 1
                                        head2head3[j,i] = -1
                                        head2head3[k,i] = -1
                                    elif comparison == 2:
                                        head2head3[j,i] = 1
                                        head2head3[j,k] = 1
                                        head2head3[i,j] = -1
                                        head2head3[k,j] = -1
                                    else:
                                        head2head3[k,i] = 1
                                        head2head3[k,j] = 1
                                        head2head3[i,k] = -1
                                        head2head3[j,k] = -1
            sums3 = np.array([sum(head2head3[i,:]) for i in range(len(indices))])
            notcandidates = np.where((sums3 < 0))[0]
            while len(notcandidates) > 0:
                for i in notcandidates:
                    head2head[i,:] = 0
                    head2head[:,i] = 0
                    head2head3[i,:] = 0
                    head2head3[:,i] = 0
                    candidates[i] = False
                sums = np.array([sum(head2head[i,:]) for i in range(len(indices))])
                notcandidates = np.where(sums < 0)[0]
                if len(notcandidates) == 0:
                    sums3 = np.array([sum(head2head3[i,:]) for i in range(len(indices))])
                    notcandidates = np.where(sums3 < 0)[0]
        if sum(candidates) != 1:
            1/0 # edge case that normally doesn't occur. If it does ever happen -> stop execution and think about how to handle it
        winners_list = []
        not_winners_list = []
        i = np.where(candidates)[0][0]
        time_tmp = all_results[i][indices[i]][1]
        for name_tmp in [name for name,time in all_results[i][indices[i]:] if time == time_tmp]:
            if name_tmp in winners:
                winners_list.append(name_tmp)
            else:
                not_winners_list.append(name_tmp)
        if len(not_winners_list) > 0: # reorder in result list (in order for indices to be correct!)
            j = 0
            for winner in winners_list:
                all_results[i][indices[i]+j][0] = winner
                j += 1
            for not_winner in not_winners_list:
                all_results[i][indices[i]+j][0] = not_winner
                j += 1
        nr_entries = len(winners_list)
        winners_list = [entry for entry in winners_list if entry in athletes_relevant]
        if len(winners_list) > 0:
            print(len(ranking))
            ranking.append([len(ranking)+1,winners_list,all_files[np.where(candidates)[0][0]].split('.')[0],indices[np.where(candidates)[0][0]]+1])
        indices[np.where(candidates)[0][0]] += nr_entries
    best = np.zeros((len(athletes_relevant),3),dtype=int) # first entry is best 2023 result, second entry is best overall result and third entry is second best overall result
    for index,names_list,race,rank in ranking:
        for name in names_list:
            ix = athletes_relevant.index(name)
            if race+'.csv' in files_by_category[0]:
                if best[ix,0] == 0:
                    best[ix,0] = index
            if best[ix,1] == 0:
                best[ix,1] = index
            elif best[ix,2] == 0:
                best[ix,2] = index
    maxbest = [max(best[i,:]) for i in range(len(athletes_relevant))]
    combined = zip(athletes_relevant, maxbest)
    sorted_combined = sorted(combined, key=lambda x: x[1])
    ranking_sorted = [item[0] for item in sorted_combined]
    names = []
    ratings = []
    for index,name in enumerate(ranking_sorted):
        names.append(name)
        ratings.append(max(99-index,int(90-(index-9)/(len(ranking_sorted)-10)*50)))
    final_names.append(names)
    final_ratings.append(ratings)
result_dict = {}
for i in range(len(final_names)): # iteration over disciplines
    for j in range(len(final_names[i])): # iteration over names
        name = final_names[i][j]
        if name not in result_dict:
            result_dict[name] = [np.nan] * 5
        result_dict[name][i]  = final_ratings[i][j]
df = pd.DataFrame(result_dict)
df = df.transpose()
df.columns = ['overall','swim','bike','run','transition']
df.to_excel("ratings_"+sex+".xlsx", index_label="Name")

