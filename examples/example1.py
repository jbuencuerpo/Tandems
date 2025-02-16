# -*- coding: utf-8 -*-
import tandems

tandems.docs()

eff = tandems.effs(junctions=4, bins=6, concentration=500)    #    Include as many or as few options as needed.
eff.findGaps()
eff.plot() # Figures saved to PNG files.

eff.save() # Data saved for later reuse/replotting. Path and file name set in eff.name, some parameters and timestamp are appended to filename

eff2 = tandems.deepcopy(eff)
eff2.__init__(junctions=4,bins=8, concentration=1, R=4e-5)  # Change input parameters but keep previously found set of optimal gap combinations.
eff2.recalculate() # Recalculate efficiencies for previously found set of optimal gap combinations.
eff2.compare(eff) # Compares efficiencies in two datasets by doing eff2 - eff. Plots difference and saves PNG files.

# eff = tandems.load('/path/and file name here') # Load previusly saved data
# eff.results()
# eff.plot()

# The .npy files with the spectra used to calculate the yearly average efficiency have been generated with genBins.py

---- CONTENTS OF tandems PYTHON MODULE ----

FUNCTION tandems.generate_spectral_bins(latMin=40 , latMax=40, longitude='random', AOD='random', PW='random', tracking=True, fname='Iscs')

    Generates a file with a complete set of binned averaged spectra for yearly energy yield calculations
    Location can be randomized within given lattitude limits: latMin, latMax.
    This might be useful to optimize cell designs to yield maximum energy for a range of lattitudes and atmospheric conditions, rather than at a single specific location.

    NECESARY CHANGES IN SMARTS 2.9.5 SOURCE CODE
    # Line 189
    #       batch = .TRUE.
    # Line 1514
    #      IF(Zenit.LE.75.5224)GOTO 13
    #      WRITE(16,103,iostat = Ierr24)Zenit
    # 103  FORMAT(//,'Zenit  =  ',F6.2,' is > 75.5224 deg. (90 in original code) This is equivalent to AM < 4'
    This change is needed because trackers are shadowed by neighboring trackers when the sun is near the horizon. 
    Zenit 80 is already too close to the horizon to use in most cases due to shadowing issues.

OBJECT CLASS tandems.effs( input variables ): 
    Object class to hold results sets of yearly average photovoltaic efficiency 

    # ---- Input variables ----
    
    junctions = 6
    topJunctions = 0 # Number of series conected juctions in top stack (topJunctions = 0 in 2 terminal devices)
    concentration = 1000
    gaps = [0, 0, 0, 0, 0, 0] # If a gap is 0, it is randomly chosen by tandems.findGaps(), otherwise it is kept fixed at value given here.
    ERE = 0.01 #external radiative efficiency without mirror. With mirror ERE increases by a factor (1 + beta)
    beta = 11 #n^2 squared refractive index  =  radiative coupling parameter  =  substrate loss.
    bins = 8 # bins is number of spectra used to evaluate eff, an array can be used to test the effect of the number of spectral bins. See convergence = True. 
    Tmin = 15+273.15 # Minimum ambient temperature at night in K
    deltaT = np.array([30, 55]) # Device T increase over Tmin caused by high irradiance (1000 W/m2), first value is for flat plate cell, second for high concentration cell
    convergence = False # Set to True to test the effect of changing the number of spectral bins  used to calculate the yearly average efficiency
    transmission = 0.02 # Subcell thickness cannot be infinite, 3 micron GaAs has transmission in the 2 to 3 % range (depending on integration range)
    thinning = False # Automatic subcell thinning for current matching
    thinSpec = 1 # Spectrum used to calculate subcell thinning for current matching. Integer index in specs array. 
    effMin = 0.02 # Lowest sampled efficiency value relative to maximum efficiency. Gaps with lower efficiency are discarded.
    d = 1 # 0 for global spectra, 1 for direct spectra
    # T = 70 for a 1mm2 cell at 1000 suns bonded to copper substrate. Cite I. Garcia, in CPV Handbook, ed. by: I. Rey-Stolle, C. Algora
    name = './Test' # Can optionally include path to destination of generated files. Example: "/home/documents/test". Some parameters and timestamp are appended to filename
    cells = 1000 # Desired number of calculated tandem cells. Will not exactly match number of returned results.
    R = 5e-7 # Series resistance of each stack in Ohm*m2. Default is optimistic value for high concentration devices
    # R = 4e-5 is suggested as optimistic value for one sun flat plate devices
    EQE = 0.7453*np.exp(-((Energies-1.782)/1.384)**4)+0.1992 # EQE model fitted to current record device, DOI.: 10.1109/JPHOTOV.2015.2501729
    mirrorLoss = 1 # Default value = 1 implies the assumption that back mirror loss = loss due to an air gap.
    opticallyCoupledStacks = False # Bottom junction of the top terminal stack can either have photon recycling or radiative coupling to the botttom stack. 
    coe = 0.9 # Concentrator optical efficiency. Optimistic default value. Used only for yield calculation.
    cloudCover = 0.26 # Fraction of the yearly energy that is lost due to clouds. Location dependent, used only for yield calculation. Default value 0.26 is representative of area near Denver, CO.
    # If using experimental spectra, set cloudCover = 0. If temporal resolution is low, it might be appropriate to set Tmin = Tmin + deltaT to keep T constant.
    specsFile = 'lat40.npy' # Name of the file with the spectral set obtained from tandems.generate_spectral_bins(). See genBins.py
    
    # ---- Results ----
    
    rgaps = 0 # Results Array with high efficiency Gap combinations found by trial and error
    Is = 0 # Results Array with Currents as a function of the number of spectral bins, 0 is standard spectrum 
    effs = 0 # Results Array with Efficiencies as a function of the number of spectral bins, 0 is standard spectrum
    
    # ---- Internal variables ----
    
    Irc = 0 # Radiative coupling current
    Itotal = 0 # Isc
    Pout = 0 # Power out
    Ijx = 0 # Array with the external photocurrents integrated from spectrum. Is set by getIjx()
    T = 0 # Set from irradiance at run time
    auxEffs = 0 # Aux array for efficiencies. Has the same shape as rgaps for plotting and array masking. 
    auxIs = 0 # Aux array for plotting. sum of short circuit currents from all terminals.
    specs = [] # Spectral set loaded from file
    P = [] # Array with integrated power in each spectrum
    Iscs = [] # Array with current in each spectrum
    thinTrans = 1 # Array with transmission of each subcell
    timeStamp = 0
    daytimeFraction = 1
    
    ---- Methods and functions ----
    
    .__init__( any of the input variables here )
        Use to change input parameters but keeping previously found set of optimal gap combinations.
        Call this to change input parameters without discarding previously found gaps before calling .recalculate()
        
    .intSpec(energy,spec)
         Returns integrated photocurrent from given photon energy to UV 
        
    .getIjx(spec)
         Get current absorbed in each junction, external photocurrent only 
        
    .thin(topJ,bottomJ)
         Calculate transmission factors for each subcell in series to maximize current under spectrum given in .thinSpec 
        
    .serie(topJ,bottomJ)
         Get power from series connected subcells with indexes topJ to bottomJ. topJ = bottomJ is single junction. 
        
    .stack(spec)
         Use a single spectrum to get power from 4 terminal tandem. If topJunctions = junctions the result is for 2 terminal tandem. 
        
    .findGaps()
         Calculate efficiencies for random band gap combinations. 
        
    .plot()
         Saves efficiency plots to PNG files  
        
    .save()
         Saves data for later reuse/replotting. Path and file name set in eff.name, some parameters and timestamp are appended to filename 
               
    .recalculate():
         Recalculate efficiencies with new set of input parameters using previously found gaps. Call __init__() to change parameters before recalculate() 
        
    .compare(s0): 
         Plots relative differences of effiency for two results sets based on the same set of optimal band gap combinations.
            Input is dataset used as reference. Plots current object instance data - s0

FUNCTION tandems.Varshni(T): Gives gap correction in eV relative to 300K using GaAs parameters. T in K

FUNCTION tandems.show_assumptions():  Shows the used EQE model and the AOD and PW statistical distributions

FUNCTION tandems.load(fname):  Usage: eff = tandems.load('/path/and file name here') 

FUNCTION tandems.docs()   Shows this HELP file
