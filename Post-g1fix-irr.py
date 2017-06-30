# -*- coding: utf-8 -*-
"""
@author: payamsiyari
"""
from __future__ import division
import os
import random
from bisect import bisect_left
import fileinput
import sys
import getopt
import operator
import time
import subprocess

class SequenceType:
    Character, Integer, SpaceSeparated = ('c', 'i', 's')
class CostFunction:
    ConcatenationCost, RuleCost = ('c', 'r')
class RepeatClass:
    Repeat, MaximalRepeat, LargestMaximalRepeat, SuperMaximalRepeat = ('r', 'mr', 'lmr', 'smr')
class PairSearchMethod:
    ConstantLengthSearch, ExhausivePairSearch, GreedyPairSearch = ('c', 'e', 'g')
class LogFlag:
    ConcatenationCostLog, RuleCostLog = range(2)

class Grammar(object):
    _preprocessedInput = [] #Original input as a sequence of integers
    _dic = [] #Dictionary for correspondence of integers to original chars (only when charSeq = 'c','s')

    _inputName = ''
    _concatenatedGrammar = [] #Concatenated grammar rules with seperatorInts
    _concatenatedNTs = [] #For each grammar rule, alongside the concatenated grammar
    _separatorInts = set([]) #Used for seperating grammar rules in the concatenatedGrammar
    _separatorIntsIndices = set([]) #Indices of separatorInts in the concatenated grammar
    _nextNewInt = 0 #Used for storing ints of repeat non-terminals and separators in odd numbers
    _nextNewContextInt = 0#Used for storing ints for context non-terminals in even numbers
    _ctxNtSet = set([])#Set of context non-terminals (i.e. inside rules), used for better printing

    _MAX_LENGTH = 100 #Used for setting upper bound on fixed gap size

    _fixedGap = False#Indicates wether contexts have a fixed gap or not
    _fixedGapSavedCost = 0 #Used to correct the grammar cost when _fixedGap==True

    _quietLog = False #if true, disables logging
    _numberOfTimesRepeatPicked = 0
    _numberOfTimesPairPicked = 0
    _iterations = 0

    def __init__(self, inputFile, loadGrammarFlag, gap, chFlag = SequenceType.Character, noNewLineFlag = True):
        self._MAX_LENGTH = gap
        if loadGrammarFlag:
            self._initFromGrammar(inputFile)
        else:
            self._initFromStrings(inputFile, chFlag, noNewLineFlag)
    #Initializes (an unoptimized) grammar from inputFile. charSeq tells if inputFile is a char sequence, int sequence or space-separated sequence
    def _initFromStrings(self, inputFile, chFlag = SequenceType.Character, noNewLineFlag = True):
        self._inputName = inputFile.name.split('.')[0]
        # self.TMP_OUTPUT_FILE = self._inputName + '-' + self.TMP_OUTPUT_FILE
        # self.TMP_INPUT_FILE = self._inputName + '-' + self.TMP_INPUT_FILE
        (self._preprocessedInput, self._dic) = self._preprocessInput(inputFile, charSeq = chFlag, noNewLineFlag = noNewLineFlag)
        allLetters = set(map(int,self._preprocessedInput.split()))
        #Setting odd and even values for _nextNewInt and _nextNewContextInt
        self._nextNewInt = max(allLetters)+1
        if self._nextNewInt % 2 == 0:
            self._nextNewContextInt = self._nextNewInt
            self._nextNewInt += 1
        else:
            self._nextNewContextInt = self._nextNewInt + 1
        #Initializing the concatenated grammar
        for line in self._preprocessedInput.split('\n'):
            line = line.rstrip('\n')
            self._concatenatedGrammar.extend(map(int,line.split()))
            self._concatenatedGrammar.append(self._nextNewInt)
            self._concatenatedNTs.extend(0 for j in range(len(map(int,line.split()))))
            self._concatenatedNTs.append(self._nextNewInt)
            self._separatorInts.add(self._nextNewInt)
            self._separatorIntsIndices.add(len(self._concatenatedGrammar)-1)
            self._nextNewInt += 2
            # if len(line.split()) > self._MAX_LENGTH:
            #     self._MAX_LENGTH = len(line.split())
    #Loads the grammar from an external file
    def _initFromGrammar(self, inputFile):
        firstLine  = False
        grammar = {}
        wordDict = {}
        counterDict = {}
        counter = 0
        textFile = inputFile.read()
        textFile = textFile.replace('   ',' SPACECHAR ')
        textFile = textFile.replace('  \n',' SPACECHAR\n')
        # print textFile
        tmpRule = []
        for line in textFile.split('\n'):
            # if line == '':
            #     continue
            if firstLine:
                firstLine = False
                continue
            if len(line.split(' ->  ')) < 2:
                tmpRule = ['\n'] + line.split(' ')
                # tmpRule = line.split(' ')
                newRule = []
                for w in tmpRule:
                    if w == '':
                        continue
                    if w not in counterDict:
                        wordDict[counter] = w
                        counterDict[w] = counter
                        counter += 1
                    newRule.append(counterDict[w])
                grammar[newNt] += newRule
                continue
            else:
                nt = line.split(' ->  ')[0]
            if counter % 2 == 0:
                if counter != 0:
                    counter += 1
            if nt not in counterDict:
                wordDict[counter] = nt
                counterDict[nt] = counter
                counter += 1
            newNt = counterDict[nt]
            rule = line.split(' ->  ')[1].split(' ')
            # print rule
            newRule = []
            for w in rule:
                if w == '':
                        continue
                if w not in counterDict:
                    wordDict[counter] = w
                    counterDict[w] = counter
                    counter += 1
                newRule.append(counterDict[w])
            # print 'newRule', newRule
            if newNt in grammar:
                if type(grammar[newNt][0]) is not list:
                    grammar[newNt] = [grammar[newNt]]
                grammar[newNt].append(newRule)
            else:
                grammar[newNt] = newRule
            # print newNt, "->", grammar[newNt]
        # print grammar
        self._dic = wordDict
        self._nextNewInt = counter
        if self._nextNewInt % 2 == 0:
            self._nextNewContextInt = self._nextNewInt
            self._nextNewInt += 1
        else:
            self._nextNewContextInt = self._nextNewInt + 1
        for nt in grammar:
            if type(grammar[nt][0]) is not list:
                # print nt
                # print grammar[nt]
                self._concatenatedGrammar.extend(grammar[nt])
                self._concatenatedGrammar.append(self._nextNewInt)
                self._concatenatedNTs.extend(nt for j in range(len(grammar[nt])))
                self._concatenatedNTs.append(self._nextNewInt)
                self._separatorInts.add(self._nextNewInt)
                self._separatorIntsIndices.add(len(self._concatenatedGrammar)-1)
                self._nextNewInt += 2
            else:
                for rhs in grammar[nt]:
                    self._concatenatedGrammar.extend(rhs)
                    self._concatenatedGrammar.append(self._nextNewInt)
                    self._concatenatedNTs.extend(nt for j in range(len(rhs)))
                    self._concatenatedNTs.append(self._nextNewInt)
                    self._separatorInts.add(self._nextNewInt)
                    self._separatorIntsIndices.add(len(self._concatenatedGrammar) - 1)
                    self._nextNewInt += 2
        # print self._concatenatedGrammar
        # print len(self._concatenatedGrammar)

    #...........Main Algorithm........
    def gSGP(self, pairingEnabled, fixedGap, quiet, normalRepeatType, ctxRepeatType, costFunction, pairSearchMethod):
        self._fixedGap = fixedGap
        self._quietLog = quiet
        prevPairUsed = False #Used when a pair is replaced to avoid detecting repeats
        odd = False
        pairingEnabled = False
        firstRoundFinished = False
        while True: #Main IRR loop
            #Logging Grammar Cost
            self._logViaFlag(LogFlag.ConcatenationCostLog)
            self._logViaFlag(LogFlag.RuleCostLog)

            if not prevPairUsed:#Extracting Maximum-Gain Repeat
                (maximumRepeatGainValue, selectedRepeatOccs) = self._retreiveMaximumGainRepeat(normalRepeatType, CostFunction.RuleCost)
            if maximumRepeatGainValue == -1 and not firstRoundFinished:
                firstRoundFinished = True
                pairingEnabled=  True

            maximumPairGainValue = -1
            if pairingEnabled and prevPairUsed == False:#Extracting Maximum-Gain Pair
                (maximumPairGainValue, selectedPairOccs) = self._retreiveMaximumGainPair(ctxRepeatType,costFunction, pairSearchMethod)
                if maximumPairGainValue == -1 and firstRoundFinished:
                    break

            #Logging Maximum Gains
            if maximumPairGainValue >= 0 and pairingEnabled:
                if not self._fixedGap:
                    self._logMessage('maxP ' + str(maximumPairGainValue) + ' : ' + str(tuple((self._concatenatedGrammar[selectedPairOccs[0][0][0]-selectedPairOccs[0][1]:selectedPairOccs[0][0][0]],self._concatenatedGrammar[selectedPairOccs[0][0][1]:selectedPairOccs[0][0][1]+selectedPairOccs[0][2]]))))
                else:
                    self._logMessage('maxP ' + str(maximumPairGainValue) + ', gap=' + str(selectedPairOccs[0][0][1]-selectedPairOccs[0][0][0]) + ' : ' + str(tuple((self._concatenatedGrammar[selectedPairOccs[0][0][0]-selectedPairOccs[0][1]:selectedPairOccs[0][0][0]],self._concatenatedGrammar[selectedPairOccs[0][0][1]:selectedPairOccs[0][0][1]+selectedPairOccs[0][2]]))))
            if maximumRepeatGainValue > 0:
                self._logMessage('maxR ' + str(maximumRepeatGainValue) + ' : ' + str(self._concatenatedGrammar[selectedRepeatOccs[1][0]:selectedRepeatOccs[1][0]+selectedRepeatOccs[0]]) + '\n')

            #If gains are equal, we randomize between selecting a pair or a repeat
            if maximumPairGainValue > 0 and ((maximumPairGainValue > maximumRepeatGainValue and prevPairUsed == False) or (maximumPairGainValue == maximumRepeatGainValue and prevPairUsed == False)):
                odd = False
                prevPairUsed = True #Remembering to select the current context as a repeat in the next iteration
                (maximumRepeatGainValue, selectedRepeatOccs) = (maximumPairGainValue,self._replacePair(selectedPairOccs)) #Replacing the chosen context
                self._numberOfTimesPairPicked += 1
                self._iterations += 1
            else:
                if maximumRepeatGainValue > 0:
                    odd = True
                    prevPairUsed = False #Resetting to search for both repeats and contexts in the next iteration
                    self._replaceRepeat(selectedRepeatOccs) #Replacing the chosen repeat
                    self._numberOfTimesRepeatPicked += 1
                    self._iterations += 1
        self._logMessage('---------------')
        self._logMessage('Number of Times Iterations:' + str(self._iterations))
        self._logMessage('Number of Times Picked Repeats:' + str(self._numberOfTimesRepeatPicked))
        self._logMessage('Number of Times Picked Pairs:' + str(self._numberOfTimesPairPicked))

    #Returns the cost of the grammar according to the selected costFunction
    def grammarCost(self, costFunction):
        if costFunction == CostFunction.ConcatenationCost:
            if not self._fixedGap:
                # return len(self._concatenatedGrammar)-2*len(self._separatorInts)
                return len(self._concatenatedGrammar) - 2 * len(self._separatorInts) + self._numberOfTimesPairPicked
            else:
                return len(self._concatenatedGrammar)-2*len(self._separatorInts)+self._numberOfTimesPairPicked
        if costFunction == CostFunction.RuleCost:
            if not self._fixedGap:
                return len(self._concatenatedGrammar)
            else:
                return len(self._concatenatedGrammar)-self._fixedGapSavedCost

    def customPrint(self, string):
        nt = string.split('--')[0]
        string = string.split('--')[1]
        array = map(int,string.split(', '))
        print nt, '-> ',
        for i in range(len(array)):
            print  self._dic[array[i]],
    #...........Printing Functions........
    #Prints the grammar, optionally in integer form if intGrammarPrint==True
    def printGrammar(self, intGrammarPrint):
        sys.stderr.write('GrammarCost(Concats): ' + str(self.grammarCost(CostFunction.ConcatenationCost)) + '\n')
        print 'GrammarCost(Concats):' , str(self.grammarCost(CostFunction.ConcatenationCost))
        sys.stderr.write('GrammarCost: ' + str(self.grammarCost(CostFunction.RuleCost)) + '\n')
        print 'GrammarCost:' , str(self.grammarCost(CostFunction.RuleCost))
        print
        Grammar = self._concatenatedGrammar
        NTs = self._concatenatedNTs
        separatorInts = self._separatorInts
        Dic = self._dic
        rules = {}
        ntDic = {}
        counter = 1
        NTsSorted = set([])
        for i in range(len(NTs)):
            if NTs[i] not in ntDic and NTs[i] not in separatorInts:
                NTsSorted.add(NTs[i])
                ntDic[NTs[i]] = 'N'+str(NTs[i])
                rules['N'+str(NTs[i])] = ''
                counter += 1
        for i in range(len(Grammar)):
            if Grammar[i] not in NTsSorted:
                if Grammar[i] not in separatorInts:
                    if not intGrammarPrint:
                        try:
                            rules[ntDic[NTs[i]]] = rules[ntDic[NTs[i]]] + ' ' + Dic[Grammar[i]]
                        except:
                            print Grammar[i], NTs[i]
                            raise
                    else:
                        rules[ntDic[NTs[i]]] = rules[ntDic[NTs[i]]] + ' ' + str(Grammar[i])
                else:
                    rules[ntDic[NTs[i-1]]] = rules[ntDic[NTs[i-1]]] + ' ||'
            else:
                if not intGrammarPrint:
                    try:
                        rules[ntDic[NTs[i]]] = rules[ntDic[NTs[i]]] + ' ' + ntDic[Grammar[i]]
                    except:
                            print Grammar[i], NTs[i]
                            raise
                else:
                    rules[ntDic[NTs[i]]] = rules[ntDic[NTs[i]]] + ' ' + ntDic[Grammar[i]]
        NTsSorted = sorted(list(NTsSorted))
        ruleCounter = 0
        for nt in NTsSorted:
            if nt not in self._ctxNtSet:
                if intGrammarPrint:
                    subrules = rules[ntDic[nt]].rstrip(' ||').split(' ||')
                    for s in subrules:
                        print ntDic[nt] + ' ->' + s
                else:
                    subrules = rules[ntDic[nt]].rstrip(' ||').split(' ||')
                    for s in subrules:
                        print ntDic[nt] + ' -> ' + s
            ruleCounter += 1
            if ruleCounter == 1:
                    for nt in sorted(list(self._ctxNtSet)):
                        if intGrammarPrint:
                            subrules = rules[ntDic[nt]].rstrip(' ||').split(' ||')
                            for s in subrules:
                                print ntDic[nt] + ' ->' + s
                        else:
                            subrules = rules[ntDic[nt]].rstrip(' ||').split(' ||')
                            for s in subrules:
                                print ntDic[nt] + ' -> ' + s
    #Prints all rules corresponding to the nonterminal n (int)
    def _printRules(self, n):
        return ''
    #Prints all yields corresponding to the nonterminal n (int)
    def _yieldOfNT(self, n):
        print 'Yield'
    #Prints the yield corresponding to the rule r
    def _yieldOfRule(self, r):
        print 'Yield'
    #Log via flags
    def _logViaFlag(self, flag):
        if not self._quietLog:
            if flag == LogFlag.ConcatenationCostLog:
                sys.stderr.write('GrammarCost(Concats): ' + str(self.grammarCost(CostFunction.ConcatenationCost)) + '\n')
                print(str('GrammarCost(Concats): ' + str(self.grammarCost(CostFunction.ConcatenationCost))))
            if flag == LogFlag.RuleCostLog:
                sys.stderr.write('GrammarCost: ' + str(self.grammarCost(CostFunction.RuleCost)) + '\n')
                print(str('GrammarCost: ' + str(self.grammarCost(CostFunction.RuleCost))))
    #Log custom message
    def _logMessage(self, message):
        if not self._quietLog:
            sys.stderr.write(message + '\n')
            print(str(message))

    #...........Utility Functions........
    #Converts the input data into an integer sequence, returns the integer sequence and the dictionary for recovering orginal letters
    def _preprocessInput(self, inputFile, charSeq = SequenceType.Character, noNewLineFlag = True):
        if charSeq == SequenceType.Character:#Building an integer-spaced sequence from the input string
            letterDict = {}
            counterDict = {}
            i = 0
            counter = 1
            newContents = ''
            if noNewLineFlag:
                line = inputFile.read()
                for i in range(len(line)):
                    if line[i] not in counterDict:
                        letterDict[counter] = line[i]
                        counterDict[line[i]] = counter
                        counter += 1
                    newContents += str(counterDict[line[i]]) + ' '
            else:
                for line in inputFile:
                    line = line.rstrip('\n')
                    for i in range(len(line)):
                        if line[i] not in counterDict:
                            letterDict[counter] = line[i]
                            counterDict[line[i]] = counter
                            counter += 1
                        newContents += str(counterDict[line[i]]) + ' '
                    newContents += '\n'
            return (newContents.rstrip('\n'), letterDict)
        if charSeq == SequenceType.Integer:#input is space seperated integers
            newContents = []
            letterDict = {}
            for line in inputFile:
                try:
                    for sym in line.split():
                        letterDict[int(sym)] = sym
                except ValueError:
                    raise ValueError('Input file is not in space-separated integer form: %s'%sym)
                newContents.append(line.strip())
                newContents = " ".join(newContents)

            return (newContents , letterDict )
        if charSeq == SequenceType.SpaceSeparated:#input is space-seperated words
            wordDict = {}
            counterDict = {}
            i = 0
            counter = 1
            newContents = ''
            for line in inputFile:
                line = line.rstrip('\n')
                for w in line.split():
                    if w not in counterDict:
                        wordDict[counter] = w
                        counterDict[w] = counter
                        counter += 1
                    newContents += str(counterDict[w]) + ' '
                newContents += '\n'
            return (newContents.rstrip('\n'), wordDict)

    #Replaces a repeat's occurrences with a new nonterminal and creates a new rule in the grammar
    def _replaceRepeat(self,(repeatLength, (repeatOccs))):
        repeat = self._concatenatedGrammar[repeatOccs[0]:repeatOccs[0]+repeatLength]
        newTmpConcatenatedGrammar = []
        newTmpConcatenatedNTs = []
        prevIndex = 0
        for i in repeatOccs:
            newTmpConcatenatedGrammar += self._concatenatedGrammar[prevIndex:i] + [self._nextNewInt]
            newTmpConcatenatedNTs += self._concatenatedNTs[prevIndex:i] + [self._concatenatedNTs[i]]
            prevIndex = i+repeatLength
        self._concatenatedGrammar = newTmpConcatenatedGrammar + self._concatenatedGrammar[prevIndex:]
        self._concatenatedNTs = newTmpConcatenatedNTs + self._concatenatedNTs[prevIndex:]
        self._concatenatedGrammar = self._concatenatedGrammar + repeat
        self._concatenatedNTs = self._concatenatedNTs + [self._nextNewInt for j in range(repeatLength)]
        self._logMessage('Added Nonterminal: ' + str(self._nextNewInt))
        self._nextNewInt += 2
        self._concatenatedGrammar = self._concatenatedGrammar + [self._nextNewInt]
        self._concatenatedNTs = self._concatenatedNTs + [self._nextNewInt]
        self._separatorInts.add(self._nextNewInt)
        self._separatorIntsIndices = set([])
        for i in range(len(self._concatenatedGrammar)):
            if self._concatenatedGrammar[i] in self._separatorInts:
                self._separatorIntsIndices.add(i)
        self._nextNewInt += 2
    #Retrieves the maximum-gain repeat (randomizes within ties).
    #Output is a tuple: "(RepeatGain, (RepeatLength, (RepeatOccurrences)))"
    #1st entry of output is the maximum repeat gain value
    #2nd entry of output is a tuple of form: "(selectedRepeatLength, selectedRepeatOccsList)"
    def _retreiveMaximumGainRepeat(self, repeatClass, costFunction):
        repeats = self._extractRepeats(repeatClass)
        maxRepeatGain = 0
        candidateRepeats = []
        for r in repeats: #Extracting maximum repeat
            repeatStats = r.split()
            repeatOccs = self._extractNonoverlappingRepeatOccurrences(int(repeatStats[0]),map(int,repeatStats[2][1:-1].split(',')))
            if maxRepeatGain < self._repeatGain(int(repeatStats[0]), len(repeatOccs), costFunction):
                maxRepeatGain = self._repeatGain(int(repeatStats[0]), len(repeatOccs), costFunction)
                candidateRepeats = [(int(repeatStats[0]),len(repeatOccs),repeatOccs)]
            else:
                if maxRepeatGain > 0 and maxRepeatGain == self._repeatGain(int(repeatStats[0]), len(repeatOccs), costFunction):
                    candidateRepeats.append((int(repeatStats[0]),len(repeatOccs),repeatOccs))
        if(len(candidateRepeats) == 0):
            return (-1, (0, []))
        #Randomizing between candidates with maximum gain
        selectedRepeatStats = candidateRepeats[0]
        selectedRepeatLength = selectedRepeatStats[0]
        selectedRepeatOccs = sorted(selectedRepeatStats[2])
        return (maxRepeatGain, (selectedRepeatLength, selectedRepeatOccs))
    #Returns the repeat gain, according to the chosen cost function
    def _repeatGain(self, repeatLength, repeatOccsLength, costFunction):
        if costFunction == CostFunction.ConcatenationCost:
            return (repeatLength-1)*(repeatOccsLength-1)
        if costFunction == CostFunction.RuleCost:
            return (repeatLength-1)*(repeatOccsLength-1)-2
    #Extracts the designated class of repeats (Assumes ./repeats binary being in the same directory)
    #Output is a string, each line containing: "RepeatLength    NumberOfOccurrence  (CommaSeparatedOccurrenceIndices)"
    def _extractRepeats(self, repeatClass):
        process = subprocess.Popen(["./repeats1/repeats11", "-i", "-r"+repeatClass, "-n1", "-psol"],stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.stdin.write(' '.join(map(str, self._concatenatedGrammar)))
        text_file = ''
        while process.poll() is None:
            output = process.communicate()[0].rstrip()
            text_file += output
        process.wait()
        repeats=[]
        firstLine = False
        for line in text_file.splitlines():
            if firstLine == False:
                firstLine = True
                continue
            repeats.append(line.rstrip('\n'))
        return repeats
    #Extracts the non-overlapping occurrences of a repeat from a list of occurrences (scans from left to right)
    def _extractNonoverlappingRepeatOccurrences(self, repeatLength, occurrencesList):
        nonoverlappingIndices = []
        for i in range(len(occurrencesList)):
            if len(nonoverlappingIndices) > 0:
                if (nonoverlappingIndices[-1] + repeatLength <= occurrencesList[i]):#Not already covered
                    nonoverlappingIndices += [occurrencesList[i]]
            else:
                nonoverlappingIndices += [occurrencesList[i]]
        return  nonoverlappingIndices

    #Replaces a pair's occurrences with a new nonterminal, creates a new rule for the pairs and create corresponding rules for gaps in the grammar
    #Returns the occurrences of the (now repeated) context indices in the new concatenated grammar for use in next iteration
    def _replacePair(self, pairOccurrences):
        insideStringsSet = {}
        for o in pairOccurrences:
            insideString = ' '.join(map(str,self._concatenatedGrammar[o[0][0]:o[0][1]]))
            if insideString in insideStringsSet:
                insideStringsSet[insideString].add(o)
            else:
                insideStringsSet[insideString] = set([o])
        self._logMessage('Inside Strings: ' + str(insideStringsSet.items()))
        if len(insideStringsSet.items()) == 1:
            self._logMessage(insideStringsSet)
            self._logMessage('single inside rule selected!')
            exit()
        usedRanges = self._extractNonoverlappingPairOccurrences(pairOccurrences)
        self._logMessage('Inside Strings Ranges:' + str(usedRanges))
        newRepeatsList = [] #Used for next iteration, the case might happen that created repeats from contexts have equal gains as other repeats in the next iteration
        newRepeatsLength = usedRanges[0][2]+usedRanges[0][1]+1
        newTmpConcatenatedGrammar = []
        newTmpConcatenatedNTs = []
        prevIndex = 0
        if self._nextNewContextInt < self._nextNewInt - 1:
                self._nextNewContextInt = self._nextNewInt - 1
        for i in range(len(usedRanges)):
            tmpRange = usedRanges[i]
            newTmpConcatenatedGrammar += self._concatenatedGrammar[prevIndex:tmpRange[0][0]] + [self._nextNewContextInt]
            newRepeatsList.append(len(newTmpConcatenatedGrammar)-1-tmpRange[1])
            newTmpConcatenatedNTs += self._concatenatedNTs[prevIndex:tmpRange[0][0]] + [self._concatenatedNTs[tmpRange[0][0]-1]]
            prevIndex = tmpRange[0][1]
        newTmpConcatenatedGrammar += self._concatenatedGrammar[prevIndex:]
        newTmpConcatenatedNTs += self._concatenatedNTs[prevIndex:]
        currentNT = self._nextNewContextInt
        self._ctxNtSet.add(currentNT)
        self._logMessage('Added Nonterminal:' + str(self._nextNewContextInt))
        self._logMessage('Number of original occurrences:' + str(len(pairOccurrences)))
        self._logMessage('Number of non-overlapping occurrences:' + str(len(usedRanges)))
        self._nextNewContextInt += 2
        for i in range(len(usedRanges)):
            tmpRange = usedRanges[i]
            newTmpConcatenatedGrammar += self._concatenatedGrammar[tmpRange[0][0]:tmpRange[0][1]] + [self._nextNewInt]
            newTmpConcatenatedNTs += [currentNT for j in range(tmpRange[0][1]-tmpRange[0][0])] + [self._nextNewInt]
            self._separatorInts.add(self._nextNewInt)
            self._nextNewInt += 2
        self._separatorIntsIndices = set([])
        for i in range(len(newTmpConcatenatedGrammar)):
            if newTmpConcatenatedGrammar[i] in self._separatorInts:
                self._separatorIntsIndices.add(i)
        self._concatenatedGrammar = newTmpConcatenatedGrammar
        self._concatenatedNTs = newTmpConcatenatedNTs
        if self._fixedGap: #Correcting the extra cost in case of using fixed-gap contexts
			self._fixedGapSavedCost += len(usedRanges) #The Extra improvement added after XRCE
        return (newRepeatsLength, newRepeatsList)
    #Retrieves the maximum-gain pair (first that is found).
    #Output is a tuple: "(RepeatGain, (RepeatLength, (RepeatOccurrences)))"
    #1st entry of output is the maximum pair gain value
    #2nd entry of output is a list of tuples of the form: "(GapOccurrenceRange,R1Length,R2Length)"
    def _retreiveMaximumGainPair(self, repeatClass, costFunction, pairSearchMethod):
        pairDic = self._extractPairs(repeatClass, pairSearchMethod, costFunction)
        return self._retreiveMaximumGainPairFromPairDic(pairDic, costFunction)
    #Retrieves the maximum-gain pair from a dictionary of {pair:occurrences} (first that is found)
    #1st entry of output is the maximum pair gain value
    #2nd entry of output is a list of tuples of the form: "(GapOccurrenceRange,R1Length,R2Length)"
    def _retreiveMaximumGainPairFromPairDic(self, pairDic, costFunction):
        maxPairGain = 0
        reducedRanges = []
        pairGainDic = {}
        for key in pairDic:
            r1Length = len(key[0])
            r2Length = len(key[1])
            pairDic[key] = self._extractNonoverlappingPairOccurrences(pairDic[key])
            pairGainDic[key] = self._pairGain(r1Length, r2Length, pairDic[key], costFunction)
        if len(pairDic) != 0 and len(pairGainDic) != 0:
            sortedPairGains = sorted(pairGainDic.items(), key=operator.itemgetter(1),reverse=True)
            if (sortedPairGains[0])[1] > maxPairGain and (sortedPairGains[0])[1] != 0:
                maxPairGain = (sortedPairGains[0])[1]
                reducedRanges = pairDic[(sortedPairGains[0])[0]]
        if len(reducedRanges) == 0:
            return (-1,[])
        #Fix pair occurrences if chosen greedy pair search method
        #---------
        return (maxPairGain, reducedRanges)
    #Returns the pair gain, according to the chosen cost function
    def _pairGain(self, r1Length, r2Length, pairOccs, costFunction):
        pairOccsLength = len(pairOccs)
        if costFunction == CostFunction.ConcatenationCost:
            if not self._fixedGap:
                return (r1Length + r2Length - 4)*(pairOccsLength-1)-2
            else:
                return (r1Length + r2Length - 2)*(pairOccsLength-1)-4
        if costFunction == CostFunction.RuleCost:
            additionalGain = 0
            insideStringsSet = {}
            for o in pairOccs:
                insideString = ' '.join(map(str,self._concatenatedGrammar[o[0][0]:o[0][1]]))
                if insideString in insideStringsSet:
                    insideStringsSet[insideString].add(o)
                else:
                    insideStringsSet[insideString] = set([o])
            if len(insideStringsSet.items()) == 1:
                return 0
            if not self._fixedGap:
                return ((r1Length + r2Length - 1) * (pairOccsLength-1))
            else:
                totalGain = (r1Length + r2Length - 1) * (pairOccsLength - 1) - 4 + additionalGain # Extra Gain Added after XRCE
                return totalGain
    #Extracts the designated class of repeated-contexts (Assumes ./repeats binary being in the same directory)
    #Output is a dictionary of the form: "((R1),(R2)):(GapOccurrenceRange,R1Length,R2Length)"
    def _extractPairs(self, repeatClass, pairSearchMethod, costFunction):
        ctxRepeats = self._extractRepeats(repeatClass)
        pairDic = {}
        allRepeatOccs = []
        #Storing repeats as tuples of "(RepeatLength, OccurrenceIndex)"
        for r in ctxRepeats:
            allRepeatOccs.extend([(int((r.split())[0]),j) for j in list((map(int, ((r.split())[2])[1:-1].split(','))))])
        allRepeatOccs.extend([(-1,j) for j in self._separatorIntsIndices]) #Merging with separatorIntsIndices for easier detection of input strings' ends
        allRepeatOccs = sorted(allRepeatOccs,key=lambda x: (x[1],x[0]))
        if self._fixedGap:
            pairDic = self._fixedGapPairSearch(allRepeatOccs, costFunction)
        else:
            if pairSearchMethod == PairSearchMethod.ConstantLengthSearch:
                pairDic = self._variableGapPairSearchWithConstantMaxGap(allRepeatOccs)
            if pairSearchMethod == PairSearchMethod.ExhausivePairSearch:
                pairDic = self._exhausivePairSearch(allRepeatOccs)
            if pairSearchMethod == PairSearchMethod.GreedyPairSearch:
                pairDic = self._greedyPairSearch(allRepeatOccs)
        return pairDic
    #Fixed-Gap pair search.
    #Input is the gap and the sorted list of all repeat occurrences: [(repeatLength, repeatOccurrenceIndex)]
    #Output is a dictionary of the form: "((R1),(R2)):(GapOccurrenceRange,R1Length,R2Length)"
    def _fixedGapPairSearch(self, repeatOccurrences, costFunction):
        pairDic = {}
        reverseRepeatOccs = {}
        reverseRepeatEnds = {}
        for repOcc in repeatOccurrences:
            if repOcc[1] not in self._separatorIntsIndices:
                if repOcc[1] in reverseRepeatOccs:
                    reverseRepeatOccs[repOcc[1]].append(repOcc[0])
                else:
                    reverseRepeatOccs[repOcc[1]] = [repOcc[0]]
                if repOcc[1]+repOcc[0]-1 in reverseRepeatEnds:
                    reverseRepeatEnds[repOcc[1]+repOcc[0]-1].append(repOcc[0])
                else:
                    reverseRepeatEnds[repOcc[1]+repOcc[0]-1] = [repOcc[0]]
        maxGapGain = -1
        for k in xrange(1,self._MAX_LENGTH+1):
            sys.stderr.write(str(k) + '\n')
            tmpPairDic = {}
            currentStringRepsOccs = {}
            currentStringRepsEnds = {}
            currentStringStart = 0
            currentStringEnd = 0
            for index in range(len(self._concatenatedGrammar)):
                if index in self._separatorIntsIndices:
                    currentStringEnd = index
                    for currentIndex in range(currentStringStart,currentStringEnd):
                        if (currentStringRepsOccs.has_key(currentIndex+k+1)) and (currentStringRepsEnds.has_key(currentIndex)):
                            for repL1 in currentStringRepsEnds[currentIndex]:
                                for repL2 in currentStringRepsOccs[currentIndex+k+1]:
                                    if tmpPairDic.has_key((tuple(self._concatenatedGrammar[currentIndex-repL1+1:currentIndex+1]),tuple(self._concatenatedGrammar[currentIndex+k+1:currentIndex+k+1+repL2]))):
                                        tmpPairDic[(tuple(self._concatenatedGrammar[currentIndex-repL1+1:currentIndex+1]),tuple(self._concatenatedGrammar[currentIndex+k+1:currentIndex+k+1+repL2]))].append(((currentIndex+1,currentIndex+k+1),repL1,repL2))
                                    else:
                                        tmpPairDic[(tuple(self._concatenatedGrammar[currentIndex-repL1+1:currentIndex+1]),tuple(self._concatenatedGrammar[currentIndex+k+1:currentIndex+k+1+repL2]))] = [((currentIndex+1,currentIndex+k+1),repL1,repL2)]
                    currentStringStart = index + 1
                    currentStringRepsOccs = {}
                    currentStringRepsEnds = {}
                else:
                    if index in reverseRepeatOccs:
                        currentStringRepsOccs[index] = reverseRepeatOccs[index]
                    if index in reverseRepeatEnds:
                        currentStringRepsEnds[index] = reverseRepeatEnds[index]
            (maxPairGain, reducedRanges) = self._retreiveMaximumGainPairFromPairDic(tmpPairDic, costFunction)
            if maxPairGain > maxGapGain:
                pairDic = tmpPairDic
                maxGapGain = maxPairGain
        return pairDic
    #Variable-Gap pair search.
    #Input is the gap and the sorted list of all repeat occurrences: [(repeatLength, repeatOccurrenceIndex)]
    #Output is a dictionary of the form: "((R1),(R2)):(GapOccurrenceRange,R1Length,R2Length)"
    def _variableGapPairSearchWithConstantMaxGap(self, repeatOccurrences):
        reverseRepeatOccs = {}
        reverseRepeatEnds = {}
        for repOcc in repeatOccurrences:
            if repOcc[1] not in self._separatorIntsIndices:
                if repOcc[1] in reverseRepeatOccs:
                    reverseRepeatOccs[repOcc[1]].append(repOcc[0])
                else:
                    reverseRepeatOccs[repOcc[1]] = [repOcc[0]]
                if repOcc[1]+repOcc[0]-1 in reverseRepeatEnds:
                    reverseRepeatEnds[repOcc[1]+repOcc[0]-1].append(repOcc[0])
                else:
                    reverseRepeatEnds[repOcc[1]+repOcc[0]-1] = [repOcc[0]]
        maxGapGain = -1
        for k in xrange(1,self._MAX_LENGTH):
            sys.stderr.write(str(k) + '\n')
            tmpPairDic = {}
            currentStringRepsOccs = {}
            currentStringRepsEnds = {}
            currentStringStart = 0
            currentStringEnd = 0
            for index in range(len(self._concatenatedGrammar)):
                if index in self._separatorIntsIndices:
                    currentStringEnd = index
                    for currentIndex in range(currentStringStart,currentStringEnd):
                        if (currentStringRepsOccs.has_key(currentIndex+k+1)) and (currentStringRepsEnds.has_key(currentIndex)):
                            for repL1 in currentStringRepsEnds[currentIndex]:
                                for repL2 in currentStringRepsOccs[currentIndex+k+1]:
                                    if tmpPairDic.has_key((tuple(self._concatenatedGrammar[currentIndex-repL1+1:currentIndex+1]),tuple(self._concatenatedGrammar[currentIndex+k+1:currentIndex+k+1+repL2]))):
                                        tmpPairDic[(tuple(self._concatenatedGrammar[currentIndex-repL1+1:currentIndex+1]),tuple(self._concatenatedGrammar[currentIndex+k+1:currentIndex+k+1+repL2]))].append(((currentIndex+1,currentIndex+k+1),repL1,repL2))
                                    else:
                                        tmpPairDic[(tuple(self._concatenatedGrammar[currentIndex-repL1+1:currentIndex+1]),tuple(self._concatenatedGrammar[currentIndex+k+1:currentIndex+k+1+repL2]))] = [((currentIndex+1,currentIndex+k+1),repL1,repL2)]
                    currentStringStart = index + 1
                    currentStringRepsOccs = {}
                    currentStringRepsEnds = {}
                else:
                    if index in reverseRepeatOccs:
                        currentStringRepsOccs[index] = reverseRepeatOccs[index]
                    if index in reverseRepeatEnds:
                        currentStringRepsEnds[index] = reverseRepeatEnds[index]
        return tmpPairDic
    #Exhausive variable-length gap pair search.
    #Input is the sorted list of all repeat occurrences: [(repeatLength, repeatOccurrenceIndex)]
    #Output is a dictionary of the form: "((R1),(R2)):(GapOccurrenceRange,R1Length,R2Length)"
    def _exhausivePairSearch(self, repeatOccurrences):
        pairDic = {}
        currentStringPairOccs = []
        for r in repeatOccurrences:#Scanning pair occurrences
            if r[1] in self._separatorIntsIndices:#Reached the end of an input string
                for k in range(len(currentStringPairOccs)):#Greedy Pairing
                    r1 = currentStringPairOccs[k]
                    for j in range(len(currentStringPairOccs)-k-1):
                        r2 = currentStringPairOccs[k+1+j]
                        r1Length = r1[0]
                        r2Length = r2[0]
                        oc1 = r1[1]
                        oc2 = r2[1]
                        if (oc2 < oc1 or oc1 + r1Length >= oc2):
                            continue
                        newPair = (tuple(self._concatenatedGrammar[oc1:oc1+r1Length]),tuple(self._concatenatedGrammar[oc2:oc2+r2Length]))
                        if newPair in pairDic:
                            pairDic[newPair].append(((oc1+r1Length,oc2),r1Length,r2Length))
                        else:
                            pairDic[newPair] = [((oc1+r1Length,oc2),r1Length,r2Length)]
                currentStringPairOccs = []
            else:
                currentStringPairOccs.append(r)
        return pairDic
    #Greedy variable-length gap pair search.
    #Input is the sorted list of all repeat occurrences: [(repeatLength, repeatOccurrenceIndex)]
    #Output is a dictionary of the form: "((R1),(R2)):(GapOccurrenceRange,R1Length,R2Length)"
    def _greedyPairSearch(self, repeatOccurrences):
        pairDic = {}
        pairStart = -1 #Indicates the start of a pair
        pairEnd = -1 #Indicates the ending of a pair
        i = 0
        newString = True
        identifiedPairs = []
        while i < len(repeatOccurrences):#Scanning pair occurrences
            if repeatOccurrences[i][1] in self._separatorIntsIndices:#Reached the end of an input string
                newString = True
                i += 1
            else:
                if newString:
                    pairStart = repeatOccurrences[i]
                    j = i + 1
                    validStartings = [pairStart]
                    while j < len(repeatOccurrences) and repeatOccurrences[j][1] == pairStart[1]: #Scanning all repeats starting at the same index as pairStart
                        validStartings.append(repeatOccurrences[j])
                        #Selecting the shortest repeat as pairStart
                        if pairStart[0] > repeatOccurrences[j][0]:
                            pairStart = repeatOccurrences[j]
                        j += 1
                    pairStart = random.choice(validStartings)
                    i = j
                    while i < len(repeatOccurrences) and repeatOccurrences[i][1] <= pairStart[1] + pairStart[0]: #Skipping overlapping repeats and fixing the problem of having a gap with zero length
                        i += 1
                    newString = False
                else:
                    pairEnd = repeatOccurrences[i]
                    j = i + 1
                    validEndings = [pairEnd]
                    while j < len(repeatOccurrences) and repeatOccurrences[j][1] == pairEnd[1]: #Scanning all repeats starting at the same index as pairEnd
                        validEndings.append(repeatOccurrences[j])
                        #Selecting the shortest repeat as pairEnd
                        if pairEnd[0] > repeatOccurrences[j][0]:
                            pairEnd = repeatOccurrences[j]
                        j += 1
                    pairEnd = random.choice(validEndings)
                    i = j
                    while i < len(repeatOccurrences) and repeatOccurrences[i][1] <= pairEnd[1] + pairEnd[0]: #Setting the start position for next pair
                        i += 1
                    if (tuple(self._concatenatedGrammar[pairStart[1]:pairStart[1]+pairStart[0]]),tuple(self._concatenatedGrammar[pairEnd[1]:pairEnd[1]+pairEnd[0]])) in pairDic:
                        pairDic[(tuple(self._concatenatedGrammar[pairStart[1]:pairStart[1]+pairStart[0]]),tuple(self._concatenatedGrammar[pairEnd[1]:pairEnd[1]+pairEnd[0]]))].append(((pairStart[1]+pairStart[0],pairEnd[1]),pairStart[0],pairEnd[0]))
                    else:
                        pairDic[(tuple(self._concatenatedGrammar[pairStart[1]:pairStart[1]+pairStart[0]]),tuple(self._concatenatedGrammar[pairEnd[1]:pairEnd[1]+pairEnd[0]]))] = [((pairStart[1]+pairStart[0],pairEnd[1]),pairStart[0],pairEnd[0])]
                    newString = True
        return pairDic
    #Extracts non-overlapping occurrences of a pair from a all lists of its occurrences in exhausive pair search method
    #Input is of the form of the values from pairDic, scans from left to right)
    def _extractNonoverlappingPairOccurrences(self, occurrencesList):
        gain = 0
        reducedRanges = sorted(occurrencesList, key=lambda x: (x[0][0],x[0][1]))
        usedRanges = []
        if not self._fixedGap:
            for i in range(len(reducedRanges)):
                invalidPair = False
                tmpRange = reducedRanges[i]
                if(len(usedRanges) > 0):
                    candidateRange = usedRanges[-1]
                    if (candidateRange[0][0] >= tmpRange[0][0] and candidateRange[0][0] <= tmpRange[0][1]) or (candidateRange[0][1] >= tmpRange[0][0] and candidateRange[0][1] <= tmpRange[0][1]) or (candidateRange[0][0]-candidateRange[1] >= tmpRange[0][0] and candidateRange[0][0]-candidateRange[1] <= tmpRange[0][1]) or (candidateRange[0][1]+candidateRange[2] >= tmpRange[0][0] and candidateRange[0][1]+candidateRange[2] <= tmpRange[0][1]):
                        invalidPair = True
                if not invalidPair:
                    usedRanges += [tmpRange]
        else:#reducing fixed-gaps, only store the gap with highest number of occurrences
            gapDic = {}
            for r in reducedRanges:
                gapDic[r[0][1]-r[0][0]] = []
            for r in reducedRanges:
                gapDic[r[0][1]-r[0][0]].append(r)
            tmpUsedRanges = []
            for gap in gapDic:
                for i in range(len(gapDic[gap])):
                    invalidPair = False
                    tmpRange = gapDic[gap][i]
                    if(len(tmpUsedRanges) > 0):
                        candidateRange = tmpUsedRanges[-1]
                        if (candidateRange[0][0] >= tmpRange[0][0] and candidateRange[0][0] <= tmpRange[0][1]) or (candidateRange[0][1] >= tmpRange[0][0] and candidateRange[0][1] <= tmpRange[0][1]) or (candidateRange[0][0]-candidateRange[1] >= tmpRange[0][0] and candidateRange[0][0]-candidateRange[1] <= tmpRange[0][1]) or (candidateRange[0][1]+candidateRange[2] >= tmpRange[0][0] and candidateRange[0][1]+candidateRange[2] <= tmpRange[0][1]):
                            invalidPair = True
                    if not invalidPair:
                        tmpUsedRanges += [tmpRange]
                if len(usedRanges) < len(tmpUsedRanges):
                    usedRanges = tmpUsedRanges
                tmpUsedRanges = []
        return usedRanges


#Sets the value of parameters
def processParams(argv):
    aFlag = False #if false, the algorithm becomes equivalent to IRR-MC
    fFlag = False #if true along with p flag, only reduces the fixed-gap contexts
    chFlag = SequenceType.Character #if false, accepts integer sequence
    printIntsGrammar = False #if true, prints the grammar in integer sequence format
    quietLog = False #if true, disables logging
    rFlag = 'mr' #repeat type (for normal repeat replacements)
    cFlag = 'mr' #repeat type (for context replacements)
    pairFlag = 'e' #context pair search method, either exhausive or greedy
    functionFlag = 'r' #cost function to be optimized
    noNewLineFlag = True #consider each line as a separate string
    loadGrammarFlag = False
    gap = 50

    usage = """Usage:
    [-a]: specifies the algorithm flags
        p - if set, the algorithm enforces a repeat reduction after identifying each context-reduction
        f - if set along with p flag, only reduces the fixed-gap contexts
    [-t]: choosing between character sequence, integer sequence or space-separated sequence
        c - character sequence
        i - integer sequence
        s - space-separated sequence
    [-p]: specifies grammar printing option
        i - prints the grammar in integer sequence format
    [-q]: disables logging
    [-r]: repeat type (for normal repeat replacements)
        r - repeat
        mr - maximal repeat (default)
        lmr - largest-maximal repeat
        smr - super-maximal repeat
    [-c]: repeat type (for context replacements)
        r - repeat
        mr - maximal repeat (default)
        lmr - largest-maximal repeat
        smr - super-maximal repeat
    [-s]: variable-length context pairs search method
        c - constant maximum length (is set hardcoded)
        e - exhausive (default), searches over all pairs
        g - greedy , selects pairs greedily so that maximum number of consistent pairs are selected
    [-f]: cost function to be optimized
        c - concatenation cost
        r - rule cost (default)
    [-m]: consider each line as a separate string
    [-l]: load a grammar file (will override -r -c -t -m options)
            (as of now, only straight-line grammars are supported)
    [-g]: amount of gap in fixed-gap context-detection mode
                    """
    if len(argv) == 1 or (len(argv) == 2 and argv[1] == '-h'):
        sys.stderr.write('Invalid input\n')
        sys.stderr.write(usage + '\n')
        sys.exit()
    optlist,args = getopt.getopt(argv[1:], 'a:t:p:qr:c:s:f:mlg:')
    for opt,arg in optlist:
        if opt == '-a':
            for ch in arg:
                if ch == 'p':
                    aFlag = True
                else:
                    if ch == 'f':
                        fFlag = True
                    else:
                        sys.stderr.write('Invalid input in ' + '-a' + ' flag\n')
                        sys.stderr.write(usage + '\n')
                        sys.exit()
        if opt == '-t':
            for ch in arg:
                if ch == 'c' or ch == 'i' or ch == 's':
                    chFlag = ch
                else:
                    sys.stderr.write('Invalid input in ' + '-i' + ' flag\n')
                    sys.stderr.write(usage + '\n')
                    sys.exit()
        if opt == '-p':
            for ch in arg:
                if ch == 'i':
                    printIntsGrammar = True
                else:
                    sys.stderr.write('Invalid input in ' + '-p' + ' flag\n')
                    sys.stderr.write(usage + '\n')
                    sys.exit()
        if opt == '-q':
            quietLog = True
        if opt == '-r':
            if arg == 'r' or arg == 'mr' or arg == 'lmr' or arg == 'smr':
                rFlag = arg
            else:
                sys.stderr.write('Invalid input in ' + '-r' + ' flag\n')
                sys.stderr.write(usage + '\n')
                sys.exit()
        if opt == '-c':
            if arg == 'r' or arg == 'mr' or arg == 'lmr' or arg == 'smr':
                cFlag = arg
            else:
                sys.stderr.write('Invalid input in ' + '-c' + ' flag\n')
                sys.stderr.write(usage + '\n')
                sys.exit()
        if opt == '-s':
            if arg == 'c' or arg == 'e' or arg == 'g':
                pairFlag = arg
            else:
                sys.stderr.write('Invalid input in ' + '-s' + ' flag\n')
                sys.stderr.write(usage + '\n')
                sys.exit()
        if opt == '-f':
            if arg == 'c' or arg == 'r':
                functionFlag = arg
            else:
                sys.stderr.write('Invalid input in ' + '-f' + ' flag\n')
                sys.stderr.write(usage + '\n')
                sys.exit()
        if opt == '-m':
            noNewLineFlag = False
        if opt == '-l':
            loadGrammarFlag = True
        if opt == '-g':
            gap = int(arg)

    return (aFlag, fFlag, chFlag, printIntsGrammar, quietLog, rFlag, cFlag, pairFlag, functionFlag, noNewLineFlag, loadGrammarFlag, gap)

if __name__ == "__main__":
    (aFlag, fFlag, chFlag, printIntsGrammar, quietLog, rFlag, cFlag, pairFlag, functionFlag, noNewLineFlag, loadGrammarFlag, gap) = processParams(sys.argv)
    g = Grammar(open(sys.argv[-1],'r'), loadGrammarFlag, gap, chFlag, noNewLineFlag)
    g.gSGP(aFlag, fFlag, quietLog, rFlag, cFlag, functionFlag, pairFlag)
    g.printGrammar(printIntsGrammar)