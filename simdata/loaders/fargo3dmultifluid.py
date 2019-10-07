code_info = ( "fargo3d", "2.0", "multifluid")

import os
import re
import copy
import numpy as np
import astropy.units as u
import astropy.constants as const
from . import interface
from .. import fluid
from .. import field
from .. import grid
from .. import vector
from .. import particles

def identify(path):
    try:
        get_data_dir(path)
        return True
    except FileNotFoundError:
        return False

field_vars_2d = {
    "mass density" : {
        "pattern" : "{}dens{}.dat",
        "unitpowers" : {"mass" : 1, "length" : -2}
        }
    ,"energy density" : {
        "pattern" : "{}energy{}.dat",
        "unitpowers" : {"mass" : 1, "time" : -2}
        }
    ,"vrad" : {
        "pattern" : "{}vy{}.dat",
        "unitpowers" : {"length" : 1, "time" : -1},
        }
    ,"vazimuth" : {
        "pattern" : "{}vx{}.dat",
        "unitpowers" : {"length" : 1, "time" : -1},
        }
    ,"grainsize" : {
        "pattern" : "{}grainsize{}.dat",
        "unitpowers" : {"length" : 1},
        }
    ,"grainsize drift" : {
        "pattern" : "{}grainsize_drift{}.dat",
        "unitpowers" : {"length" : 1},
        }
    ,"grainsize frag" : {
        "pattern" : "{}grainsize_frag{}.dat",
        "unitpowers" : {"length" : 1},
        }
    ,"grainsize driftfrag" : {
        "pattern" : "{}grainsize_driftfrag{}.dat",
        "unitpowers" : {"length" : 1},
        }
    ,"grainsize coag" : {
        "pattern" : "{}grainsize_coag{}.dat",
        "unitpowers" : {"length" : 1},
        }

    }

planet_vars_scalar = {
    'x' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 1,
        'timecol' : 8,
        'unitpowers' : {'length' : 1} },
    'y' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 2,
        'timecol' : 8,
        'unitpowers' : {'length' : 1} },
    'z' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 3,
        'timecol' : 8,
        'unitpowers' : {'length' : 1} },
    'vx' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 4,
        'timecol' : 8,
        'unitpowers' : {'length' : 1, "time" : -1 } },
    'vy' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 5,
        'timecol' : 8,
        'unitpowers' : {'length' : 1, "time" : -1 } },
    'vz' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 6,
        'timecol' : 8,
        'unitpowers' : {'length' : 1, "time" : -1 } },
    'mass' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 7,
        'timecol' : 8,
        'unitpowers' : {'mass' : 1} },
    'mass' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 9,
        'timecol' : 8,
        'unitpowers' : {'time' : -1} },
    'time step' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 0,
        'timecol' : 8,
        'unitpowers' : {} },
    'physical time' : {
        'file' : 'bigplanet{}.dat',
        'datacol' : 8,
        'timecol' : 8,
        'unitpowers' : {"time" : 1} },
    ########################################
    ### orbital elements
    'physical time orbit' : {
        'file' : 'orbit{}.dat',
        'datacol' : 0,
        'timecol' : 0,
        'unitpowers' : {"time" : 1} },
    'eccentricity' : {
        'file' : 'orbit{}.dat',
        'datacol' : 1,
        'timecol' : 0,
        'unitpowers' : {} },
    'semi-major axis' : {
        'file' : 'orbit{}.dat',
        'datacol' : 2,
        'timecol' : 0,
        'unitpowers' : {"length" : 1} },
    'mean anomaly' : {
        'file' : 'orbit{}.dat',
        'datacol' : 3,
        'timecol' : 0,
        'unitpowers' : {} },
    'true anomaly' : {
        'file' : 'orbit{}.dat',
        'datacol' : 4,
        'timecol' : 0,
        'unitpowers' : {} },
    'argument of periapsis' : {
        'file' : 'orbit{}.dat',
        'datacol' : 5,
        'timecol' : 0,
        'unitpowers' : {} },
    'x-axis rotation angle' : {
        'file' : 'orbit{}.dat',
        'datacol' : 6,
        'timecol' : 0,
        'unitpowers' : {} },
    'inclination' : {
        'file' : 'orbit{}.dat',
        'datacol' : 7,
        'timecol' : 0,
        'unitpowers' : {} },
    'ascending node' : {
        'file' : 'orbit{}.dat',
        'datacol' : 8,
        'timecol' : 0,
        'unitpowers' : {} },
    'longitude of periapsis' : {
        'file' : 'orbit{}.dat',
        'datacol' : 9,
        'timecol' : 0,
        'unitpowers' : {} },
}

alias_fields = {
    "velocity radial"       : "vrad"
    ,"velocity azimuthal"   : "vazimuth"
    ,"total energy density" : "energy density"
}

alias_reduced = {
    "output time step"        : "analysis time step"
    ,"simulation time"        : "physical time"
    ,"mass"                   : "mass"
    ,"angular momentum"       : "angular momentum"
    ,"total energy"           : "total energy"
    ,"internal energy"        : "internal energy"
    ,"kinetic energy"         : "kinetic energy"
    ,"eccentricity"           : "eccentricity"
    ,"periastron"             : "periastron"
    ,"mass flow inner"        : ""
    ,"mass flow outer"        : ""
    ,"mass flow wavedamping"  : ""
    ,"mass flow densityfloor" : ""
}

alias_particle = {
    "output time step"       : "time step"
    ,"simulation time"       : "physical time"
    ,"argument of periapsis" : "argument of periapsis"
    ,"velocity"              : "velocity"
    ,"mass"                  : "mass"
    ,"angular momentum"      : "angular momentum"
    ,"eccentricity"          : "eccentricity"
    ,"semi-major axis"       : "semi-major axis"
}

def var_in_files(varpattern, files):
    p = re.compile(varpattern.replace(".", "\.").format("\d+"))
    for f in files:
        if re.match(p, f):
            return True
    return False

def load_scalar(file, var):
    return [1,1]

def get_data_dir(path):
    rv = None
    ptrn = re.compile("summary\d+.dat")
    for root, dirs, files in os.walk(path):
        for f in files:
            m = re.search(ptrn, f)
            if m:
                rv = root
                break
    if rv is None:
        raise FileNotFoundError("Could not find identifier file 'summary\d+.dat' in any subfolder of '{}'".format(path))
    return rv

def find_first_summary(dataDir):
    ptrn = re.compile("summary\d+.dat")
    summaries = []
    for f in os.listdir(dataDir):
        if re.search(ptrn, f):
            summaries.append(f)
    summaries.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
    return summaries[0]

def get_unit_from_powers(unitpowers, units):
    unit = 1.0
    for u, p in unitpowers.items():
        unit = unit*units[u]**p
    return unit

class Loader(interface.Interface):

    code_info = code_info

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_dir = get_data_dir(self.path)
        self.output_times = np.array([])

    def set_data_dir(self, data_dir):
        self.data_dir = data_dir

    def scout(self):
        self.get_domain_size()
        self.get_units()
        self.apply_units()
        self.get_fluids()
        self.get_fields()
        #self.get_vectors()
        self.get_planets()
        self.get_nbodysystems()
        self.register_alias()

    def apply_units(self):
        self.planet_vars_scalar = planet_vars_scalar
        self.field_vars_2d = copy.deepcopy(field_vars_2d)
        for vardict in [self.planet_vars_scalar, self.field_vars_2d]:
            for var, info in vardict.items():
                info["unit"] = get_unit_from_powers(info["unitpowers"], self.units)

    def register_alias(self):
        for particlegroup in self.particlegroups:
            particlegroup.alias.register_dict(alias_particle)
        for planet in self.planets:
            planet.alias.register_dict(alias_particle)
        for name, fluid in self.fluids.items():
            fluid.alias.register_dict(alias_fields)
            fluid.alias.register_dict(alias_reduced)

    def get_nbodysystems(self):
        pass

    def get_planets(self):
        planet_ids = []
        p = re.compile("bigplanet(\d).dat")
        for s in os.listdir(self.data_dir):
            m = re.match(p, s)
            if m:
                planet_ids.append(m.groups()[0])
        planet_ids.sort()
        # create planets
        self.planets = []
        for pid in planet_ids:
            self.planets.append(particles.Planet(str(pid), pid))
        # add variables to planets
        for pid, planet in zip(planet_ids, self.planets):
            for varname in planet_vars_scalar:
                planet.register_variable( varname, VectorLoader( varname, {"datafile" : os.path.join(self.data_dir, "bigplanet{}.dat".format(pid))}, self) )

    def get_fluids(self):
        ptrn = re.compile("output(.*)\.dat")
        fluid_names = [ m.groups()[0] for m in (re.search(ptrn, f) for f in os.listdir(self.data_dir))
                        if m is not None]
        for name in fluid_names:
            self.fluids[name] = fluid.Fluid(name)

    def get_fields(self):
        self.get_fields_2d()

    def get_fields_2d(self):
        files = os.listdir(self.data_dir)
        for fluidname in self.fluids.keys():
            for varname, info in self.field_vars_2d.items():
                info_formatted = copy.deepcopy(info)
                info_formatted["pattern"] = info_formatted["pattern"].format(fluidname, "{}")
                if var_in_files(info_formatted["pattern"], files):
                    fieldLoader = FieldLoader(varname, info_formatted, self)
                    self.fluids[fluidname].register_variable(varname, "2d", fieldLoader)

    def get_vectors(self):
        gas = self.fluids["gas"]
        datafile = os.path.join(self.data_dir, "Quantities.dat")
        variables = load_text_data_variables(datafile)
        for varname, (column, unitstr) in variables.items():
            gas.register_variable(varname, "vector", VectorLoader(varname, {"datafile" : datafile }, self))
        # add multi axis vectors
        if all([v in variables for v in ["radial kinetic energy", "azimuthal kinetic energy"]]):
            gas.register_variable("kinetic energy", "vector", VectorLoader(varname, {"datafile" : datafile, "axes" : { "r" : "radial kinetic energy", "phi" : "azimuthal kinetic energy" } }, self))

    def get_domain_size(self):
        self.Nphi, self.Nr = loadNcells(self.data_dir)

    def get_output_time(self, n):
        if self.output_times.size == 0:
            self.output_times = loadCoarseOutputTimes(self.data_dir, self.units["time"])
        return self.output_times[n]

    def get_units(self):
        self.units = loadUnits(self.data_dir)

class FieldLoader:

    def __init__(self, name, info, loader, *args, **kwargs):
        self.loader = loader
        self.info = info
        self.name = name

    def __call__(self, n):
        t = self.loader.get_output_time(n)
        f = field.Field(self.load_grid(n), self.load_data(n), t, self.name)
        return f

    def load_data(self, n):
        unit = self.info["unit"]
        Nr = self.loader.Nr + (1 if "interfaces" in self.info and "r" in self.info["interfaces"] else 0)
        Nphi = self.loader.Nphi + (1 if "interfaces" in self.info and "phi" in self.info["interfaces"] else 0)
        rv = np.fromfile(self.loader.data_dir + "/" + self.info["pattern"].format(n)).reshape(Nr, Nphi)*unit
        return rv

    def load_grid(self, n):
        r_i = np.genfromtxt(self.loader.data_dir + "/domain_y.dat")[3:-3]*self.loader.units["length"]
        phi_i = np.genfromtxt(self.loader.data_dir + "/domain_x.dat")*u.Unit(1)
        active_interfaces = self.info["interfaces"] if "interfaces" in self.info else []
        g = grid.PolarGrid(r_i = r_i, phi_i = phi_i, active_interfaces=active_interfaces)
        return g

class VectorLoader:

    def __init__(self, name, info, loader, *args, **kwargs):
        self.loader = loader
        self.info = info
        self.name = name

    def __call__(self):
        axes = [] if not "axes" in self.info else [key for key in self.info["axes"]]
        time = self.load_time()
        data = self.load_data()
        if len(data.shape) == 2:
            time_dim = 0
            axes_dim = 1
        else:
            time_dim = 0
            axes_dim = None
        f = vector.Vector(time, data, name=self.name, axes=axes, time_dim=time_dim, axes_dim=axes_dim )
        return f

    def load_data(self):
        if "axes" in self.info:
            rv = []
            unit = None
            for ax, varname in self.info["axes"].items():
                d = load_text_data_file(self.info["datafile"], varname)
                if unit is None:
                    unit = d.unit
                else:
                    if unit != d.unit:
                        raise ValueError("Units of multiaxis vector don't match")
                rv.append(d)
            rv = np.array(rv).transpose()*unit
        else:
            rv = load_text_data_file(self.info["datafile"], self.name, self.loader.units)
        return rv

    def load_time(self):
        # dirty hack to handle bigplanet{}.dat vs orbit{}.dat
        if self.info["datafile"].split("/")[-1][:5] == "orbit":
            time_name = "physical time orbit"
        else:
            time_name = "physical time"
        rv = load_text_data_file(self.info["datafile"], time_name, self.loader.units)
        return rv


def loadCoarseOutputTimes(dataDir, unit):
    # search all summary.dat files for the time
    outputTimes = []
    pattern = re.compile('OUTPUT [0-9]* at simulation time ([0-9\.eE+-]*)')
    for f in sorted([f for f
                     in os.listdir(dataDir)
                     if 'summary' in f],
                    key=lambda x: int(x[7:-4])):
        with open(os.path.join(dataDir,f), 'r') as infile:
            datastr = infile.read()
            matches = re.findall(pattern, datastr)
            try:
                outputTimes.append( float(matches[0]) )
            except ValueError:
                break
    times =  np.array(outputTimes)
    # fall back to reading the planet file for multifluid version
    # which is missing the summary files
    #times = np.genfromtxt( os.path.join(dataDir, 'planet0.dat'))[:,8]
    #times = times*unit
    # correct for double entries in the planet file

    return times*unit


def getParamFromSummary(dataDir, param):
    # parse the 0th summary file to get a parameter value
    search_active = False
    with open( os.path.join(dataDir, find_first_summary(dataDir)) ) as f:
        for line in f:
            if not search_active:
                # look for the parameter section identifier
                if line.strip() == "PARAMETERS SECTION:":
                    search_active = True
            else:
                parts = line.strip().split()
                if parts[0].lower() == param.lower():
                    return parts[1]


def loadRadius(dataDir, unit, interface=False):
    r = np.genfromtxt(os.path.join(dataDir, 'domain_y.dat'))*unit
    r = r[3:-3] #remove ghost cells
    dr = r[1:] - r[:-1]
    if not interface:
        r = 0.5*(r[1:] + r[:-1])
    return (r, dr)

def loadPhi(dataDir, interface=False):
    #phiMin, phiMax, Nphi = np.genfromtxt(os.path.join(dataDir, 'dimensions.dat'), usecols=(0,1,6))
    #phi = np.linspace(phiMin, phiMax, Nphi)
    phi = np.genfromtxt(os.path.join(dataDir, 'domain_x.dat'))
    if not interface:
        phi = 0.5*(phi[1:] + phi[:-1])
    return phi

def loadMeshGrid(dataDir, unit):
    # return a meshgrid for the disk to plot data
    R, Phi = loadMeshGridPolar(dataDir, unit)
    X = R*np.cos(Phi)
    Y = R*np.sin(Phi)
    return (X,Y)

def loadMeshGridPolar(dataDir, unit):
    phi = loadPhi(dataDir)
    r, dr = loadRadius(dataDir, unit)
    Phi, R = np.meshgrid(phi, r)
    return (R, Phi)


def loadUnits(dataDir):
    ### load data units
    first_summary = os.path.join(dataDir, find_first_summary(dataDir))
    if os.path.exists(first_summary):
        ptrn = "COMPILATION OPTION SECTION:\n==============================\n.*\-DCGS.*\nGhost"
        with open(first_summary, 'r') as infile:
            if re.search( ptrn, infile.read() ):
                # have cgs units
                units = { "mass" : u.g,
                          "time" : u.s,
                          "length" : u.cm,
                          "temperature" : u.K }
                return units

        # Try to extract unit normalisation from summary
        units = {}
        units["mass"] = 1.0
        units["time"] = 1.0
        units["length"] = 1.0

        with open(first_summary, 'r') as infile:
            ptrn = "(?<=R0 = \()\d+.\d+"
            m = re.search( ptrn, infile.read() )
            if m:
                units["length"] *= float(m.group()[0])

        with open(first_summary, 'r') as infile:
            ptrn = "(?<=MSTAR = \()\d+.\d+"
            m = re.search( ptrn, infile.read() )
            if m:
                units["mass"] *= float(m.group()[0])

        with open(first_summary, 'r') as infile:
            ptrn = r"STEFANK =.*\*pow\(\(\d+\.\d+\)\/\((\d+\.*\d*\*\d+\.\d*\w+\d*)\),-0\.5"
            m = re.search( ptrn, infile.read() )
            if m:
                components = m.group(1).split('*')
                units["length"] *= float(components[0]) * float(components[1]) * u.cm

        with open(first_summary, 'r') as infile:
            ptrn = r"STEFANK =.*\*pow\(\(\d+\.\d*\)\/(\d+\.\d*\w+\d*),-1\.5\)\*"
            m = re.search( ptrn, infile.read() )
            if m:
                components = m.group(1).split('*')
                units["mass"] *= float(m.group(1)) * u.g
        units["time"] = (np.sqrt(units["length"]**3 / (const.G.cgs * units["mass"]))).to(u.s)

    return units
    # now try units file
    # try:
    #     units = {l[0] : float(l[1])*u.Unit(l[2]) for l in
    #              [l.split() for l in open(os.path.join(dataDir,'units.dat'),'r')
    #               if l.split()[0] != '#' and len(l.split())==3]}
    #     ### fix temperature unit
    #     units['temperature'] = 1*u.K
    # except FileNotFoundError:
        # Fall back to default units
        # units = { 'mass' : u.solMass, 'time' : 5.2**1.5*u.yr/(2*np.pi), 'length' : 5.2*u.au }
        # Fall back to dimensionless units
        #units = { bu : 1 for bu in ['mass', 'time', 'length'] }

def loadNcells(dataDir):
    # Nphi, Nr = np.genfromtxt(os.path.join(dataDir, 'dimensions.dat'), usecols=(6,7), dtype=int)
    Nphi = int(getParamFromSummary(dataDir, "Nx"))
    Nr = int(getParamFromSummary(dataDir, "Ny"))
    return (Nphi, Nr)


def load1dRadialMonitorRaw(n, dataFile, Ncells, unit):
    # load data by first seeking the right position
    # and then reading Nrad floats
    f = open(dataFile, "rb")  # reopen the file
    f.seek(n*Ncells*8, os.SEEK_SET)  # seek
    v = np.fromfile(f, dtype=np.float64, count=Ncells)
    f.close()
    v = v*unit
    return v

def load1dRadialMonitorDensity(n, dataFile, r, dr, unit):
    # Fargo3d outputs monitor variables as the integral over Phi
    # Correct this by computing the density
    rv = load1dRadialMonitorRaw(n, dataFile, len(r), unit)
    rv = rv/np.pi/((r+dr/2)**2 - (r-dr/2)**2)
    return rv

def load1dRadialDensityAveragedFrom2d(n, dataFilePattern, Nr, Nphi, r, dr, unit):
    rv = load1dRadialAveragedFrom2d(n, dataFilePattern, Nr, Nphi, unit)
    # make it a 2d density
    rv = rv/np.pi/((r+dr/2)**2 - (r-dr/2)**2)
    return rv

def load1dRadialAveragedFrom2d(n, dataFilePattern, Nr, Nphi, unit):
    # Load 2d data and average over the azimuthal domain
    data = load2d(n, dataFilePattern, Nr, Nphi, unit)
    rv = np.mean(data, axis=1)
    return rv

def load2d(n, dataFilePattern, Nr, Nphi, unit):
    # Load 2d data an reshape it
    rv = np.fromfile(dataFilePattern.format(n)).reshape(Nr, Nphi)*unit
    return rv


def load_text_data_file(filepath, varname, units):
    # get info
    info = planet_vars_scalar[varname]
    col = info["datacol"]
    # get data
    unit = get_unit_from_powers(info["unitpowers"], units)
    data = np.genfromtxt(filepath, usecols=int(col))*unit
    return data
