#
# PC-BASIC 3.23 - stat_os.py
#
# OS statements
# 
# (c) 2013 Rob Hagemans 
#
# This file is released under the GNU GPL version 3. 
# please see text file COPYING for licence terms.
#

import os
import datetime


import error
import vartypes
import expressions
import oslayer

import util
import console

def exec_chdir(ins):
    name = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    name = oslayer.dospath_read_dir(name, '', 76)
    try:
        os.chdir(name)
    except EnvironmentError as ex:
        oslayer.handle_oserror(ex)
    util.require(ins, util.end_statement)
    

def exec_mkdir(ins):
    name = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    try:
        os.mkdir(oslayer.dospath_write_dir(name,'', 76))
    except EnvironmentError as ex:
        oslayer.handle_oserror(ex)
    util.require(ins, util.end_statement)
    
    

def exec_rmdir(ins):
    name = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    name = oslayer.dospath_read_dir(name, '', 76)
    
    try:
        os.rmdir(name)
    except EnvironmentError as ex:
        oslayer.handle_oserror(ex)
    util.require(ins, util.end_statement)
    

def exec_name(ins):
    oldname = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    oldname = oslayer.dospath_read(oldname, '', 76)
    
    # AS is not a tokenised word
    word = util.skip_white_read(ins)+ins.read(1)
    if word.upper() != 'AS':
        raise error.RunError(2)
            
    newname = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    newname = oslayer.dospath_write(newname, '', 76)
    
    if os.path.exists(newname):
        # file already exists
        raise error.RunError(58)
    
    try:
        os.rename(oldname, newname)
    except EnvironmentError as ex:
        oslayer.handle_oserror(ex)

    util.require(ins, util.end_statement)
    

def exec_kill(ins):
    name = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    name = oslayer.dospath_read(name, '')
    util.require(ins, util.end_statement)
    try:
        os.remove(name)    
    except EnvironmentError as ex:
        oslayer.handle_oserror(ex)

    
    

    

def exec_files(ins):
    path, mask = '.', '*.*'
    if util.skip_white(ins) not in util.end_statement:
        pathmask = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
        
        pathmask = pathmask.rsplit('\\',1)
        if len(pathmask)>1:
            path = pathmask[0]
            mask = pathmask[1]
        else:
            if pathmask[0]!='':
                mask=pathmask[0]            
    
    mask = mask.upper()
        
    # get top level directory for '.'
    try:
        for root, dirs, files in os.walk(path):
            break
    except EnvironmentError as ex:
        oslayer.handle_oserror(ex)

    dosfiles = oslayer.pass_dosnames(files, mask)
    dosfiles =[ name+'     ' for name in dosfiles ]
    dirs += ['.','..']
    dosdirs = oslayer.pass_dosnames(dirs, mask)
    #dosdirs = ['        .   ', '        ..  '] + pass_dosnames(dirs)
    dosdirs = [ name+'<DIR>' for name in dosdirs ]
    
    dosfiles.sort()
    dosdirs.sort()    
    output = dosdirs+dosfiles
    
    # get working dir, replace / with \
    cwd=os.path.abspath(path).replace(os.sep,'\\')
    
    console.write(cwd+util.endl)
    num = console.width/20
    
    if len(output)==0:
        # file not found
        raise error.RunError(53)
        
    while len(output)>0:
        line = ' '.join(output[:num])
        output = output[num:]
        console.write(line+util.endl)       
        # allow to break during dir listing & show names flowing on screen
        console.check_events()             
    
    console.write(str(oslayer.disk_free(path))+' Bytes free'+util.endl)
    
    util.require(ins, util.end_statement)
    
    
def exec_shell(ins):
    if util.skip_white(ins) in util.end_statement:
        cmd = oslayer.shell
    else:
        cmd = oslayer.shell_cmd + ' ' + vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    
    savecurs = console.show_cursor()
    oslayer.spawn_interactive_shell(cmd) 
    console.show_cursor(savecurs)
    
    util.require(ins, util.end_statement)
    
        
def exec_environ(ins):
    envstr = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    eqs = envstr.find('=')
    if eqs<=0:
        raise error.RunError(5)
    var=envstr[:eqs]
    val=envstr[eqs+1:]
    os.environ[var] = val
        
    util.require(ins, util.end_statement)
    
    
       
def exec_time(ins):
    #time$=
    util.require_read(ins,'\xe7')
        
    # allowed formats:
    # hh
    # hh:mm
    # hh:mm:ss
    # where hh 0-23, mm 0-59, ss 0-59
    
    timestr = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    util.require(ins, util.end_statement)
    
    now = datetime.datetime.today() + oslayer.time_offset
    timelist= [0,0,0]
    
    pos=0
    listpos=0
    word=''
    while pos<len(timestr):
        if listpos>2:
            break
             
        c = timestr[pos]
        if c in (':', '.'):
            timelist[listpos]=int(word)
            listpos+=1
            word=''
        elif (c < '0' or c > '9'): 
            raise error.RunError(5)
        else:
            word += c
            
        pos += 1
        
    if word !='':
        timelist[listpos] = int(word)     
    
    if timelist[0]>23 or timelist[1]>59 or timelist[2]>59:
        raise error.RunError(5)
    
    newtime = datetime.datetime(now.year, now.month, now.day, timelist[0], timelist[1], timelist[2], now.microsecond)
    oslayer.time_offset += newtime - now    
        
        
def exec_date(ins):
    #date$=
    util.require_read(ins,'\xe7') # =
        
    # allowed formats:
    # mm/dd/yy   mm 0--12 dd 0--31 yy 80--00--77
    # mm-dd-yy
    # mm/dd/yyyy   yyyy 1980--2099
    # mm-dd-yyyy   
    
    datestr = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    
    util.require(ins, util.end_statement)
    
    now = datetime.datetime.today() + oslayer.time_offset
    datelist= [1,1,1]
    
    pos=0
    listpos=0
    word=''
    while pos<len(datestr):
        if listpos>2:
            break
            
        c = datestr[pos]
        if c in ('-', '/'):
            datelist[listpos]=int(word)
            listpos+=1
            word=''
        elif (c < '0' or c > '9'): 
            if listpos==2:
                break
            else:
                raise error.RunError(5)
        else:
            word += c
            
        pos += 1
        
    if word !='':
        datelist[listpos] = int(word)     
        
    if datelist[0] > 12 or datelist[1]>31 or (datelist[2]>77 and datelist[2]<80) or \
                (datelist[2]>99 and datelist[2]<1980 or datelist[2]>2099):
        raise error.RunError(5)
    
    if datelist[2]<77:
        datelist[2] = 2000+datelist[2]
    
    if datelist[2]<100 and datelist[2]>79:
        datelist[2] = 1900+datelist[2]
        
    newtime = datetime.datetime(datelist[2], datelist[0], datelist[1], now.hour, now.minute, now.second, now.microsecond)
    oslayer.time_offset += newtime - now    
        
        
    
    
