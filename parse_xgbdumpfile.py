#!/usr/bin/python
#-*-coding:utf-8-*-#
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import StringIO
#function declareration.
#1.read xgb.dump file. 
#2.transform to rule.
#3.print rule paths.
import re
class XgboostTreeNode:
  def __init__(self,nodeNum=-1,splitCond=None,leftChild=None,rightChild=None,isLeaf=True,leafValue=None,cover=None,gain=None,caseMissingChild=None):
    self.__nodeNum = nodeNum
    self.__splitCond = splitCond
    self.__leftChild = leftChild
    self.__rightChild = rightChild
    self.__isLeaf = isLeaf
    self.__leafValue = leafValue
    self.__cover= cover
    self.__gain = gain
    self.__caseMissingChild = caseMissingChild
    self.__lchildCond = None
    self.__rchildCond = None
  def getNodeNum(self):
    return self.__nodeNum
  def getSplitCond(self):
    return self.__splitCond
  def getLChildCond(self):
    return self.__lchildCond
  def getRChildCond(self):
    return self.__rchildCond
  def getLeftChild(self):
    return self.__leftChild
  def getRightChild(self):
    return self.__rightChild
  def isLeaf(self):
    return self.__isLeaf
  def leafValue(self):
    return self.__leafValue
  def getGain(self):
    return self.__gain
  def getCover(self):
    return self.__cover
  def parseLine(self,line):
    if 'booster' in line:
      return
    node,attrs = line.split(':')
    self.__nodeNum = int(node)
    if 'leaf' in line:
      self.__isLeaf=True
      self.__leftChild=self.__rightChild=None
      if 'cover' in attrs:
        leafv,cover = attrs.split(',')
        self.__leafValue = float(leafv.split('=')[-1])
        self.__cover = float(cover.split('=')[-1])
      else:
        leafv = attrs
        self.__leafValue = float(leafv.split('=')[-1])
        self.__cover = None
    else:
      self.__splitCond = attrs
      cond,vals = attrs.split(' ')
      if 'gain' in attrs: 
        y,n,m,g,c = vals.split(',')
        self.__gain  = float(g.split('=')[-1])
        self.__cover = float(c.split('=')[-1])
      else:
        y,n,m = vals.split(',')
        self.__gain  = None
        self.__cover = None
      self.__leftChild = int(y.split('=')[-1])
      self.__rightChild = int(n.split('=')[-1])
      self.__caseMissingChild = int(m.split('=')[-1])
      cond=cond.replace('[','').replace(']','')
      splitFeature,splitValue = cond.split('<')
      if self.__leftChild == self.__caseMissingChild:
        #self.__lchildCond = cond
        self.__lchildCond = '(' +cond + ' or '+splitFeature+' '+'==0)'
        #self.__rchildCond = (splitFeature+'>='+'%s')%(splitValue)
        self.__rchildCond = '('+splitFeature+'>='+splitValue+' and ' + splitFeature+' ' + '<>0)'
      else:
        self.__lchildCond = '('+cond+' and '+ splitFeature + ' '+'<>0)'
        #self.__rchildCond = splitFeature+'>='+splitValue
        self.__rchildCond = ('('+splitFeature+'>='+'%s'+' or '+splitFeature+' '+'==0)')%(splitValue)

class XgboostTree:
  def __init__(self,treeNodes = None):
    self.__treeNodes = treeNodes
    self.__root = treeNodes[0] if treeNodes is not None else None
  def getRoot(self):
    return self.__root
  def getNodesNum(self):
    return len(self.__treeNodes)
  def parseLines(self,rules):
    treeNodes = [None]*len(rules)
    for r in rules:
      node = XgboostTreeNode()
      node.parseLine(r)
      treeNodes[node.getNodeNum()] = node
    self.__treeNodes = treeNodes
    self.__root = treeNodes[0]
  def printPath(self,fout):
    path = [None]*1000
    self.printPathRecur(self.__root,path,0,fout)
  def printPathRecur(self,node,path,pathLen,fout):
    if node is None:
      return
    path[pathLen] = node.getNodeNum()
    pathLen += 1
    if node.getLeftChild() is None and node.getRightChild() is None:
      self.printArray(path,pathLen,fout)
      self.printRules(path,pathLen,fout)
    else:
      self.printPathRecur( self.__treeNodes[node.getLeftChild()] , path , pathLen ,fout)
      self.printPathRecur( self.__treeNodes[node.getRightChild()], path , pathLen ,fout)
  def printArray(self,ints,len,fout):
    fout.write( '/*')
    for i in range(len):
      fout.write( str(ints[i]))
      if i<>len-1:
        fout.write( '->')
    fout.write( '*/\n')
  def printRules(self,ints,len,fout,index=False,value=True):
    for i in range(len):
      #print ints[i],
      if i==len-1:
        if index == True:
          fout.write( str(ints[i]))
        if value == True:
          fout.write( self.__treeNodes[ ints[i] ].leafValue())
      else:
        curNode  = self.__treeNodes[ ints[i] ]
        nextNode = self.__treeNodes[ ints[i+1] ] 
        if curNode.getLeftChild() == nextNode.getNodeNum():
          fout.write( curNode.getLChildCond())
          fout.write( '->')
        else:
          fout.write( curNode.getRChildCond())
          fout.write( '->')
    fout.write('\n')

def parseXgbDumpFile(xgb_dumpfile):
  xgboostTrees = []
  rules = []
  with open(xgb_dumpfile,'r') as f:
    for line in f:
      if line is None:
        break
      if 'booster' in line:
        if len(rules) > 0:
          xgbtree = XgboostTree()
          xgbtree.parseLines(rules)
          xgboostTrees.append(xgbtree)
        rules = []
      else:
        #line = line.strip()[re.search('"*"',line.strip()).start():].replace('"','')
        line = line.strip()
        rules.append(line)
    if len(rules) > 0:
      xgbtree = XgboostTree()
      xgbtree.parseLines(rules)
      xgboostTrees.append(xgbtree)
  return xgboostTrees

def printXgbDumpFile(xgb_dumpfile):
  with open(xgb_dumpfile,'r') as f:
    for line in f:
      print line,

def generateRtdRule(fin,fout):
  #initial = 's=0;'
  #fout.write( initial +'\n')
  #with open(ruleFilePath,'r') as f:
  for line in fin.readlines():
    if line is None:
      break
    if '/*' not in line:
      nodes = line.strip().split('->')
      fout.write( 'if('+' and '.join(nodes[:-1])+') then' + ' s +='+nodes[-1]+'; end if;\n')
    else:
      fout.write( line.strip() +'\n')

def main(fout,xgb_dumpfile='xgbdump.txt'):
  xgboostTrees = parseXgbDumpFile(xgb_dumpfile)
  for i in range(len(xgboostTrees)):
    fout.write( ('/*booster[%d]*/\n')%(i) )
    xgboostTrees[i].printPath(fout)

if __name__ == '__main__':
  s = StringIO.StringIO()
  main(fout = s)
  s.seek(0)
  generateRtdRule(s , sys.stdout)

