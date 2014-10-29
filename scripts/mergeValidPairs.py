#!/usr/bin/python
import argparse
import sys

## getIntervals
## Split line from validPairs file
def getIntervals( data ):
    data=data.strip()
    linetab = data.split("\t")
    number_of_columns = len(linetab)
    try:
        chr1, pos1, strand1, chr2, pos2, strand2 = linetab[1:7]
    except ValueError:
        print "Error - unexpected format\n", data.strip()
        
    return {'chr1':chr1, 'pos1':pos1, 'strand1':strand1, 'chr2':chr2, 'pos2':pos2, 'strand2':strand2}


## isOrdered
## Compare the order between two intervals
def isOrdered( data1, data2, side, chromosomes_list ):
    if side == "R1":
        chr1=data1['chr1']
        pos1=data1['pos1']
        chr2=data2['chr1']
        pos2=data2['pos1']
    elif side == "R2":
        chr1=data1['chr2']
        pos1=data1['pos2']
        chr2=data2['chr2']
        pos2=data2['pos2']
 
    if chromosomes_list.index(chr1) < chromosomes_list.index(chr2):
        return True
    elif chr1 == chr2 and int(pos1) <= int(pos2):
        return True
    else:
        return False

## isEqual
## Compare two intervals
def isEqual( data1, data2, side):
    if side == "R1":
        chr1=data1['chr1']
        pos1=data1['pos1']
        chr2=data2['chr1']
        pos2=data2['pos1']
    elif side == "R2":
        chr1=data1['chr2']
        pos1=data1['pos2']
        chr2=data2['chr2']
        pos2=data2['pos2']

    if chr1==chr2 and pos1==pos2:
        return True
    else:
        return False

## isDuplicated
## Compare two intervals
def isDuplicated (data1, data2):
    if data1 == None or data2 == None:
        return False

    if isEqual(data1, data2, "R1") and isEqual(data1, data2, "R2"):
        return True
    else:
         return False
        

## compareDataList
## Compare all data within the list and return the index of the upstream intervals
def  compareDataList( data_list, chromosomes_list ):
    
    min_index=None

    ## Check list of available buffers
    allindex=[]
    for i in range(0,len(data_list)):
        if data_list[i] != None:
            allindex.append(i)
        
    if len(allindex)>0:
        ## init with first data
        min_index=allindex[0]
        min_data=data_list[allindex[0]]
        ## compare with other data
        for i in allindex[1:len(allindex)]:
            cur_data=data_list[i]
            ##print "---"+ str(min_data) + str(cur_data) + str(isOrdered(min_data, cur_data, "R1", chromosomes_list))+ str(isEqual(min_data, cur_data, "R1")) + str(isOrdered(min_data, cur_data, "R2", chromosomes_list))+ "---"

            ## Compare first mate
            if not isEqual(min_data, cur_data, "R1") and not isOrdered(min_data, cur_data, "R1", chromosomes_list):
                min_data=cur_data
                min_index=i
                ## Compare second mate
            elif isEqual(min_data, cur_data, "R1") and not isOrdered(min_data, cur_data, "R2", chromosomes_list):
                    min_data=cur_data
                    min_index=i

            ##print min_data
    return min_index


################################################################################
##
##  __MAIN__
##
################################################################################

## Get Args
parser = argparse.ArgumentParser(description='Merge valid pairs Hi-C product from multiple samples.')
parser.add_argument('--rmdup', dest='rmdup', action='store_const', const=True, default=False, help='Remove duplicates')
parser.add_argument('filelist', metavar='validPairs', nargs='+', help='List of Hi-C valid pairs files. These files are expected to be sorted by chromosome and position')

chromosomes_list=['chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19', 'chrX', 'chrY']
args = parser.parse_args()
rmdup = args.rmdup
nbfiles = len(args.filelist)

## Initialize values
files_handlers = []
line_list = []
data_list = []
count_dup = 0
prec_data=None

## Open handler on valid pairs files
for cur_file in args.filelist:
    cur_pos=len(files_handlers)
    cur_handler=open(cur_file, 'r')
    files_handlers.append(cur_handler)
    
    ## Init data list with first line
    firstline = cur_handler.readline().strip()
    lastposition = cur_handler.tell()
    secondline = cur_handler.readline().strip()

    ## Remove duplicates from the same file
    if rmdup:
        while (isDuplicated(getIntervals(firstline),getIntervals(secondline))):
            lastposition = cur_handler.tell()
            secondline=cur_handler.readline().strip()
            count_dup+=1

    cur_handler.seek(lastposition)
    line_list.append(firstline)
    data_list.append(getIntervals(line_list[cur_pos]))

## Get first data line in the genome coordinate
index=compareDataList(data_list, chromosomes_list)

while (index != None):
    ##print "--------compare------------"
    ##print data_list
    ##print data_list[index]
    ##print isDuplicated(prec_data, data_list[index])

    ## Remove duplicates if require
    if not rmdup:
        print line_list[index]
        prec_data=data_list[index]
    else:
        if not isDuplicated(prec_data, data_list[index]):
            print line_list[index]
            prec_data=data_list[index]
        else:
            count_dup+=1

    ## Read a new line for this handler
    newline=files_handlers[index].readline().strip()

    ## Remove duplicates reads from the current handler
    if rmdup:
        while (newline == line_list[index]):
            newline=files_handlers[index].readline().strip()
            count_dup+=1

    line_list[index]=newline

    if line_list[index]:
        data_list[index]=getIntervals(line_list[index])
    else:
        files_handlers[index].close()
        data_list[index]=None
        line_list[index]=None
            
    index=compareDataList(data_list, chromosomes_list)
    ##print "--------------------------"

print >> sys.stderr, "## nb_duplicates\t", count_dup