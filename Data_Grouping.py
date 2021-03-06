# -*- coding: utf-8 -*-

import Data_Classes
from collections import deque, Counter

## grouping several samples into units
##    ---> for feature calculation
def build_units(sender, annotation, unit_length=1.0, skip_seconds=0):
#    ## XXX testing
#    max_timespan = 300
#    max_timespan = 500

    ## init
    beginning = sender.samples[0].timestamp
    begin_float = sender.samples[0].get_timestamp_as_float()
    unit_start = 0.0
    l = annotation.get_label_for(unit_start+begin_float, unit_length)
    unit = Data_Classes.Unit(l, unit_start, unit_length, beginning)
    
    units = list()
    if ( unit_start >= skip_seconds ):
        units.append(unit)
    
    ## put samples into units
    for sample in sender.samples:
        ## XXX debug output
#        sample.show()
        
        # rel. timestamp
        t = sample.get_normalized_timestamp(beginning)
        
        # sanity checks
        assert( t >= unit_start )
#        assert ( t < unit_start + unit_length * 100 )

        # create new units if nescessary
        while ( t >= unit_start + unit_length ):
            ## unit limit reached, abort
#            print "|||", len(units) * unit_length, "<-->", max_timespan
#            if ( len(units) * unit_length >= max_timespan ):
#                return units
            
            unit_start += unit_length
            
            l = annotation.get_label_for(unit_start+begin_float, unit_length)
            unit = Data_Classes.Unit(l, unit_start, unit_length, beginning)
            if ( unit_start >= skip_seconds ):
                units.append(unit)
                
#                ## XXX debug output
#                print "|||", unit.start, unit.label

                
        # * put into unit *
        assert( t >= unit_start )
        assert( t < unit_start + unit_length )
        unit.add_sample(sample)
        
    return units  # see also the return statement above



#######################################################################################################

class look_ahead_iterator(object):
    def __init__(self, inner_list):
        self.inner_list = inner_list
        self.i = 0
        
    ## returns next element (but don't iterates forward)
    def look(self):
        try:
            return self.inner_list[self.i]
        except IndexError:
            raise StopIteration
        
    ## iterate forward (but don't return anything)
    def consume(self):
        self.i += 1
        
        
    ## returns all remeining items as list
    def remaining_sublist(self):
        sub = self.inner_list[self.i:]
        self.i = len(self.inner_list) + 1

        return sub
        
        
    ## TODO für später wär es vielleicht sinnvoll eine ähnliche funktion wie "remaining_sublist" zu implementieren, mit der man einen startwert markieren kann und dann die sublist bis zur aktuellen position kriegt..
        
        


## Calibration: calculate average over first empty phase (consume this phase)
##   ---> get's called from "separation"
def _seperation_calibration(it):
    sum = 0
    num = 0

    while ( True ):
        unit = it.look()
        
        ## skip all invalids in this phase
        if ( "INVALID" in unit.label ):
            it.consume()
            continue
            
        ## OK: still in first empty-phase
        if ( unit.label == "empty" ):
            mean = unit.calc_mean()
            if ( mean != 0 ):
                sum += mean
                num += 1
                
            it.consume()
            continue
        
        ## FIN: first empty-phase just finished
        ##   ---> stop iteration, don't consume current element
        else:
            break
      
        
    ## calc calibration info (average)
    cal_info = float(sum) / float(num)
    return cal_info

    
    

## Separation
def separation(units):
    parts = list()
    it = look_ahead_iterator(units)
    
    ## calibration
#    cal_info = _seperation_calibration(it)
    cal_info = 0  ## XXX for legacy data
    
    
    ## data   (no further semparation at the moment..)
    part = Data_Classes.Recording_Part()
    part.calibration_info = cal_info
    part.units = it.remaining_sublist()

    parts.append(part)
    
    return parts




#######################################################################################################


## Windowing: groups units together in windows
def windowing(part, window_size, overlapping=False):
    units = part.units
    windows = list()
    us = deque()
    start = units[0].start


    ## * create windows *
    for unit in units:
        ## on window completion
        if ( unit.start >= start + window_size ):
            # create window
            w = Data_Classes.Window(list(us))
            windows.append(w)
                        
            # BRANCH: non-overlapping windows ---> clear
            if ( not overlapping ):
                us.clear()
                start = unit.start
            # BRANCH: overlapping windows ---> pop-front
            else:
                us.popleft()
                start = us[0].start

            
        ## collect units
        us.append(unit)
        
    # create window last window (if any)
    if ( len(us) > 0 ):
        w = Data_Classes.Window(list(us))
        windows.append(w)
    ## [* create windows *]

    return windows
    
    
