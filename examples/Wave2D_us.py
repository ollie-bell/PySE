#!/usr/bin/env python
# -*- coding: iso8859-1 -*-
#
# (c) Copyright 2005
#     Author: �smund �deg�rd
#     Simula Research Laboratory AS
#     
#     This file is part of PyFDM.
#
#     PyFDM is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     PyFDM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with PyFDM; if not, write to the Free Software
#     Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#     Example usage of PyFDM.


# We want to solve u_tt = \nable \cdot (f(x) \nabla u) in \Omege_1
#              and u_tt = c^2\nabla^2 u in \Omega_2
#              
#                  u(x,0) = F(x)
#                  u_t(x,0) = G(x)
#                  
#                  and some various boundary conditions.
#
# options to the solver: 
#  -t : end time
#  -n : number of time steps
#  -mx : division in x-direction
#  -my : division in y-direction

#import getopt, sys
#from Grid import Grid
#from Stencil import Stencil
#from ImplementedStencils import DirichletBoundary
#from NeumanBoundary import createNeumanBoundary
#from StencilList import StencilSet
#from Field import Field
#from Utils import *

from pyFDM import *
from math import exp,sin,cos,pi,sqrt
from scipy.special import j0

def runstandalone():
    T=0.0001
    n=100
    mx=40
    my=40

    parasize = pypar.size()
    myrank = pypar.rank()

    if myrank == 0:
        opts = sys.argv[1:]
        numopts = len(opts)
        i = 0
        while i < numopts:
            opt = opts[i]
            if opt == "-t":
                T = float(opts[i+1])
                i += 1
            if opt == "-n":
                n = int(opts[i+1])
                i += 1
            if opt == "-mx":
                mx = int(opts[i+1])
                i += 1
            if opt == "-my":
                my = int(opts[i+1])
                i += 1
            if opt == "-h":
                usage(T,n,mx,my)
                sys.exit(0)

            i += 1
    
    if parasize > 1:
        import Numeric
        allopts = Numeric.zeros(4,typecode='d')
        if myrank == 0:
            allopts = Numeric.array((T,n,mx,my))
        pypar.broadcast(allopts,0)
        if myrank != 0:
            T = float(allopts[0])
            n = int(allopts[1])
            mx = int(allopts[2])
            my = int(allopts[3])

    solution,g = solve(T,n,mx,my)
    
    if solution.isParallel:
        pypar.finalize()

def usage(T,n,mx,my):
    print "-t T: solve from 0 to T (default %s)" % (T)
    print "-n steps: Split time in so many steps (default %s)" % (n)
    print "-mx div: Split x-direction in this many nods (default %s)" % (mx)
    print "-my div: Split y-direction in this many nods (default %s)" % (my)


def F(x,y):
    return 0.0

def G(x,y):
    return 0.0

def H(x,y):
    return 0.0


def transducerGenerator(a0,w,a,center,pulses,radius):
    # center must be given, to compute radius (may just assume (0,0,0))
    # Use j0 from scipy.special - the zero order besselfunction.
    def transducer(x,t):
        #print "t, w, maxt_pulse: ",t, w, pulses*(1./w)
        if t < pulses*(1./w):
            r = distance(center,(x,0))
            val = a0*sin(2*pi*w*t)*j0(a*r)
            #val = -a0*sin(pi*w*t)*(r**2 - radius**2)
            #print "r, val: ",r,val
            return val
        else:
            return 0.0
    return transducer

def solve(T, n, mx, my):
    print "Solve the problem from 0 to %s in %s steps, %s x %s grid-nodes" % (T,n,mx,my)

    #some constants
    dt = T/(1.0*n)

    # running time, for use in lambda's
    rt = 0
    # domain sizes (+/- xmax x +/- ymax x [0,zmax]):
    #xmax = 0.004; ymax = 0.0004; zmax = 0.0008
    xmax = 2.0; ymax = 2.0

    # speed of sound (in mm/s)
    c = 1500e+03
    #c = 10.0
    # wave frequency
    w = 2.5e+06
    #w = 2

    # transducer parameters
    tr_center = (0,0)
    #tr_radius = 0.001
    tr_radius = 1.0
    # confused on this parameter. Should there be a 1.0e+3 scaling?
    #tr_a = 3565.1
    tr_a = 2.8846
    tr_a = 5
    #tr_a = 230
    #tr_a = 5895.77
    #tr_a = 8654
    tr_scale = 1.0
    #tr_scale = 0.05
    tr_pulses = 1

    #init_pressure = 1.01e+05
    init_pressure = 0.0

    g = Grid(domain=([-xmax,xmax],[0,ymax]), div=(mx,my))

    # ensure dt according to CFL
    dt = min(dt,sqrt((1.0/c)*(1.0/((1.0/g.dx**2) + (1.0/g.dy**2) ))))
    print "Use dt: ",dt

    hx = (c**2*dt**2)/(g.dx**2)
    hy = (c**2*dt**2)/(g.dy**2)

    # A few constants for stencils and region-defs (epsilons of 1/2 gridcells)
    ex = 0.5*g.dx
    ey = 0.5*g.dy

#    # variants of H-call:
#    Hxm = lambda x,y: hx*H(x-ex,y)
#    Hxp = lambda x,y: hx*H(x+ey,y)
#    Hym = lambda x,y: hy*H(x,y-ey)
#    Hyp = lambda x,y: hy*H(x,y+ey)
#    center = lambda x,y: 2.0 - (Hxp(x,y) + Hxm(x,y)) - (Hyp(x,y) + Hym(x,y))

    # regions
    front = ((-xmax,xmax),(0,0))
    sides = ((-xmax,xmax),(0+ey,ymax))

    # stencils.
    p_prev_stencil = Stencil(nsd=2, varcoeff=False, nodes={(0,0): -1.0})
    p_stencil = Stencil(nsd=2, varcoeff=False, nodes={(0,0): 2.0})

    
    #inner_stencil = 2*p_stencil + ((c**2)*(dt**2)/(g.dx**2))*s_lap_5pt

    lap = Laplace(g)
    inner_stencil = 2*p_stencil + ((c**2)*(dt**2))*lap

    # Transducer Dirichlet boundary
    transducer = transducerGenerator(tr_scale,w,tr_a,tr_center,tr_pulses,tr_radius)
    transducer_now = lambda x,y: transducer(x,rt)
    transducer_bc = DirichletBoundary(2, transducer_now)

    # StencilSets, 
    # A is the constant -1.0 (for -1.0*u^{n-1})
    A = StencilSet(g)
    A.addStencil(p_prev_stencil,g.allPoints())

    # B holds the main stencils (for u^n).
    B = StencilSet(g)
    B.addStencil(inner_stencil,g.innerPoints())

    # StencilSet for The dirichlet condition.
    #C = StencilSet(g)
    # The transducer
#    C.addStencil(transducer_bc, g.boundary(region=front, type='circle',\
#            center=tr_center, radius=tr_radius, direction='in'))
    
    B.addStencil(transducer_bc, g.boundary(region=front, type='circle',\
            center=tr_center, radius=tr_radius, direction='in'))

    # The absorbing boundary condition
    absorbing_bc_field = Field(g)
    call_absbc = lambda x,y: (-1./(c*dt))*absorbing_bc_field.getValByPoint(x,y)

    abcbc_front = createNeumanBoundary(inner_stencil, g, call_absbc, region=front,\
            type='circle', direction='out', radius=tr_radius, center=tr_center)
    abcbc_sides = createNeumanBoundary(inner_stencil, g, call_absbc, region=sides) 

    #C += abcbc_front
    #C += abcbc_sides
    B += abcbc_front
    B += abcbc_sides

    g.partition(B)
    A.doInitParallel()

    pprev = Field(g)
    # no need to create u, it will be created automatically...
    #u = Field(g) 

    # Set initial condition. uprev should be filled with the function F,
    # u should then be -dt*A(G) + 0.5*B(F), where A(G) is A applied to a field 
    # filled with the function G, and B(F) is B applied to a field filled
    # with F (which is uprev...)
    pprev.fill(init_pressure)
    p = 0.5*B(pprev)
    
    #dprev = Numeric.array(pprev.data)
    #d = Numeric.array(p.data)
    # trigger datastructure building:
    #waste = A(pprev)
    #waste = C(p)

    # check first if we can just set the _name_, maybe we have to either fill 
    # the field-values directly into the data-member, or wrap in some class, which
    # we can use an instance of in call_absbc.
    absorbing_bc_field = p - pprev

    #plot(field=p, title='Initical condition')
    rt = 0.0
#    contflag=True
    while rt < T:
        print "Next timestep: ",rt
        #pnew = C(B(p)) + A(pprev)
        pnew = B(p) + A(pprev)
        #dnew  = B.direct_matvec(d) + A.direct_matvec(dprev)

        # shift
        pprev = p
        p = pnew
        #dprev[:] = d
        #d[:] = dnew
        # update absorbing boundary condition
        absorbing_bc_field = p - pprev
        #absorbing_bc_field.data[:] = d - dprev
        #C.updateDataStructures()
        B.updateDataStructures()

        #print u.shapedata
        rt += dt
        #p.data[:] = d[:]
        plot(field=p,movie='on',allslice=True,title='Wave propagation, t = %s' % rt)
        # put the middle one up until next round.
        plot(field=p,movie='on',title='Wave propagation, t = %s' % rt)
#        if contflag:
#            print ">>return to continue - g to go on<<"
#            input = sys.stdin.readline()[:-1]
#            if input == "g":
#                contflag = False

    return (p,g)

if (__name__ == '__main__') : runstandalone()
