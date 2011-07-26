"""
Storage for radio spectral line information.
"""

import numpy as np
import re

try:
    import atpy
    atpyOK = True
except ImportError:
    print "Failed to import atpy"
    import readcol
    atpyOK = False

try:
    import query_splatalogue
    webOK = True
except ImportError:
    webOK = False

greekletterlist = ["Alpha","Nu","Beta","Xi","Gamma","Omicron","Delta","Pi","Epsilon","Rho","Zeta","Sigma","Eta","Tau","Theta","Upsilon","Iota","Phi","Kappa","Chi","Lambda","Psi","Mu","Omega"]
greekletterlist += ["alpha","nu","beta","xi","gamma","omicron","delta","pi","epsilon","rho","zeta","sigma","eta","tau","theta","upsilon","iota","phi","kappa","chi","lambda","psi","mu","omega"]
# regular expressions are complicated...
greekletter2  = re.compile("([^\\\]%s)" % ("|[^\\\]".join(greekletterlist)))

greekletter = re.compile("&([A-Za-z][a-z]*);?")
sub = re.compile("<sub>(.*)</sub>")
sup = re.compile("<sup>(.*)</sup>")
junk =  re.compile("&([^a-zA-Z]*);?")
R = re.compile('\W')  # find and remove all non-alphanumeric characters

import os
selfpath = os.path.split(os.path.abspath(__file__))[0]

def LineName(species,qn):
    if greekletter.search(species) is not None:
        #spn = greekletter.sub(greekletter.search(species).groups()[0][0],species)
        name = greekletter.sub(greekletter.search(species).groups()[0][0],qn.replace("(","").replace(")",""))
    else:
        name = species+qn
    if sub.search(name) is not None:
        name = sub.sub("("+sub.search(name).groups()[0]+")",name)
    if sup.search(name) is not None:
        name = sup.sub("("+sup.search(name).groups()[0]+")",name)
    return name.replace(" ","")

def LatexName(species,qn):
    #while greekletter2.search(species) is not None:
    #    species=greekletter2.sub(greekletter2.search(species).groups()[0][0]+"$\\"+greekletter2.search(species).groups()[0][1:]+"$",species)
    if greekletter.search(species) is not None:
        spn = greekletter.sub(r"$\\%s$" % greekletter.search(species).groups()[0],species)
        name = qn.replace("(","$_{").replace(")","}$").replace("&","$\\").replace(";","$")
        if greekletter.search(name) is not None:
            name = greekletter.sub("\\%s" % greekletter.search(name).groups()[0],name) 
    else:
        spn = species
        name = spn+"$(%s)$" % (qn.replace("(","_{").replace(")","}"))
        if greekletter.search(name) is not None:
            name = greekletter.sub(r"\\%s" % greekletter.search(name).groups()[0],name) 
    if junk.search(name) is not None:
        name = junk.sub("",name)
    if sub.search(name) is not None:
        name = sub.sub("_{"+sub.search(name).groups()[0]+"}",name)
    if sup.search(name) is not None:
        name = sup.sub("^{"+sup.search(name).groups()[0]+"}",name)
    if "&" in name:
        raise ValueError("But... that's... not... possible!")
    return name.replace(" ","")

#def radio_lines(minwav=0.0,maxwav=1.0):
#    lines = dict([(LineName(species,qn),[freq,'GHz',True, LatexName(species,qn)]) for
#        species,freq,qn in zip(splat.Species,splat.FreqGHz,splat.ResolvedQNs)])
#
#    #splat = query_splatalogue(minwav,maxwav)
 
def radio_lines(webquery=False, savename=None, **kwargs):
    if webquery and webOK:
        splat = query_splatalogue.query_splatalogue(**kwargs)
        splat.describe()
        splat.rename_column('frequency','FreqGHz')
        splat.FreqGHz /= 1e3
        splat.columns['FreqGHz'].unit = 'GHz'
        splat.rename_column('molecular formula','Species')
        splat.rename_column('quantum numbers','ResolvedQNs')
        try:
            splat.rename_column('chemicalname','ChemicalName')
        except:
            print "Failed to rename chemicalname."
    elif atpyOK:
        splat = atpy.Table(selfpath+"/splatalogue.csv",type='ascii',delimiter=':')
    else:
        splat = readcol.readcol(selfpath+"/splatalogue.csv",fsep=":",asStruct=True)

    for cn in splat.columns:
        if cn != R.sub('',cn):
            splat.rename_column(cn,R.sub('',cn))

    if '' in splat.FreqGHz:
        splat.FreqGHz[splat.FreqGHz == ''] = '-999'
        splat.MeasFreqGHz[splat.MeasFreqGHz == ''] = '-999'
        splat.rename_column('FreqGHz','FreqGHzTxt')
        splat.add_column('FreqGHz',splat.FreqGHzTxt.astype('float'))
        splat.remove_columns('FreqGHzTxt')
        if 'MeasFreqGHz' in splat.columns:
            splat.rename_column('MeasFreqGHz','MeasFreqGHzTxt')
            splat.add_column('MeasFreqGHz',splat.MeasFreqGHzTxt.astype('float'))
            splat.remove_columns('MeasFreqGHzTxt')

    latex_names = [LatexName(species,qn) for species,qn in zip(splat.Species,splat.ResolvedQNs)]
    line_names  = [LineName(species,qn) for species,qn in zip(splat.Species,splat.ResolvedQNs)]
    if hasattr(splat,'add_column'):
        splat.add_column("LineName",line_names)
        splat.add_column("LatexName",latex_names)

    if savename is not None:
        splat.write(savename)

    return splat