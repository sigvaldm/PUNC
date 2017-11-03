from __future__ import print_function, division
import sys
if sys.version_info.major == 2:
    from itertools import izip as zip
    range = xrange

import dolfin as df
import numpy as np
import matplotlib.pyplot as plt
from punc import *

# Simulation parameters
N        = 300                   # Total simulation time
dt       = 0.1                   # Time step
npc      = 8

# Get the mesh
mesh, boundaries = load_mesh("mesh/2D/langmuir_probe_circle_in_square")
ext_bnd_id = 9
int_bnd_id = 10

ext_bnd = ExteriorBoundaries(boundaries, ext_bnd_id)

V = df.FunctionSpace(mesh, 'CG', 1)

bc = df.DirichletBC(V, df.Constant(0.0), boundaries, ext_bnd_id)

objects = [Object(V, int_bnd_id, boundaries)]

ds = df.Measure("ds", domain=mesh, subdomain_data=boundaries)
normal = df.FacetNormal(mesh)

# Get the solver
poisson = PoissonSolver(V, bc)

# The inverse of capacitance matrix
inv_cap_matrix = capacitance_matrix(V, poisson, objects, boundaries, ext_bnd_id)

# Probe radius in mesh and debye lengths
Rp = 1. #0.000145 # m
Rpd = 5. # debye lengths
debye = Rp/Rpd
vthe = debye
vthi = debye/np.sqrt(1836.)

Vnorm = debye**2
Inorm = vthe*np.sqrt(2*np.pi)

# Initialize particle positions and velocities, and populate the domain
pop = Population(mesh, boundaries, normalization='particle scaling')
pop.init_new_specie('electron', ext_bnd, v_thermal=vthe, num_per_cell=npc)
pop.init_new_specie('proton',   ext_bnd, v_thermal=vthi, num_per_cell=npc)


# boltzmann = 1.38064852e-23 # J/K
# pfreq =
# denorm = pop.species.get_denorm(pfreq, debye, debye)
# Vnorm = denorm['V']
# Inorm = denorm['I']

dv_inv = voronoi_volume_approx(V)

KE  = np.zeros(N-1)
PE  = np.zeros(N-1)
KE0 = kinetic_energy(pop)

current_collected = -1.549*Inorm
# current_collected = 0
current_measured = np.zeros(N)
potential = np.zeros(N)
particles = np.zeros(N)

num_particles = np.zeros(N)
num_particles_outside = np.zeros(N)
num_injected_particles = np.zeros(N)
num_particles[0] = pop.num_of_particles()

timer = TaskTimer(N-1,'compact')
num_e = np.zeros(N)
num_i = np.zeros(N)
num_e[0] = num_particles[0]/2
num_i[0] = num_particles[0]/2

for n in range(1,N):

    timer.task("Distribute charge")
    rho = distribute(V, pop, dv_inv)

    timer.task("Calculate potential")
    reset_objects(objects)
    phi     = poisson.solve(rho, objects)
    E       = electric_field(phi)
    obj_flux = df.inner(E, -1*normal)*ds(0)
    image_charge = df.assemble(obj_flux)
    object_potential = (objects[0].charge-image_charge)*inv_cap_matrix[0,0]
    objects[0].set_potential(df.Constant(object_potential))

    timer.task("Solving Poisson")
    phi     = poisson.solve(rho, objects)
    E       = electric_field(phi)
    PE[n-1] = potential_energy(pop, phi)

    timer.task("Move particles")
    KE[n-1] = accel(pop, E, (1-0.5*(n==1))*dt)
    tot_num0 = pop.num_of_particles()
    move(pop, dt)

    timer.task("Relocating particles")
    old_charge = objects[0].charge
    pop.relocate(objects)

    timer.task("Impose current")
    tot_num1 = pop.num_of_particles()
    num_particles_outside[n] = tot_num0 - tot_num1
    objects[0].add_charge(-current_collected*dt)
    current_measured[n] = ((objects[0].charge-old_charge)/dt)/Inorm
    potential[n] = objects[0]._potential/Vnorm
    particles[n] = pop.num_of_particles()

    timer.task("Inject particles")
    inject(pop, ext_bnd, dt)

    timer.task("Count particles")
    tot_num2 = pop.num_of_particles()
    num_injected_particles[n] = tot_num2 - tot_num1
    num_particles[n] = tot_num2

    num_i[n] = pop.num_of_positives()
    num_e[n] = pop.num_of_negatives()

    timer.end()

timer.summary()


KE[0] = KE0

plt.figure()
plt.plot(potential,label='potential')
plt.legend(loc="lower right")
plt.grid()
plt.savefig('potential.png', format='png', dpi=1000)

plt.figure()
plt.plot(particles,label='number of particles')
plt.legend(loc="lower right")
plt.grid()
plt.savefig('particles.png', format='png', dpi=1000)

plt.figure()
plt.plot(current_measured,label='current collected')
plt.grid()
plt.legend(loc="lower right")
plt.savefig('current.png', format='png', dpi=1000)

plt.figure()
plt.plot(num_particles, label="Total number denisty")
plt.legend(loc='lower right')
plt.grid()
plt.xlabel("Timestep")
plt.ylabel("Total number denisty")
plt.savefig('total_num.png', format='png', dpi=1000)

plt.figure()
plt.plot(num_injected_particles[1:], label="Number of injected particles")
plt.plot(num_particles_outside[1:], label="Number of particles leaving the domain")
plt.legend(loc='lower right')
plt.grid()
plt.xlabel("Timestep")
plt.ylabel("Number of particles")
plt.savefig('injected.png', format='png', dpi=1000)

plt.figure()
plt.plot(num_i, label="Number of ions")
plt.plot(num_e, label="Number of electrons")
plt.legend(loc='lower right')
plt.grid()
plt.xlabel("Timestep")
plt.ylabel("Number of particles")
plt.savefig('e_i_numbers.png', format='png', dpi=1000)

# np.savetxt('data1.txt', (potential, num_e, num_i))
# np.savetxt('data2.txt', (num_particles_outside, num_injected_particles, particles, current_measured))

to_file = open('data.txt', 'w')
for i,j,k,l,m,n,o in zip(potential, num_e, num_i,num_particles_outside, num_injected_particles, particles, current_measured ):
    to_file.write("%f %f %f %f %f %f %f\n" %(i, j, k, l, m, n, o))
to_file.close()

df.File('phi_laframboise.pvd') << phi
df.File('rho_laframboise.pvd') << rho
df.File('E_laframboise.pvd') << E

plt.show()

# df.plot(rho)
# df.plot(phi)

# ux = df.Constant((1,0,0))
# Ex = df.project(df.inner(E, ux), V)
# df.plot(Ex)
# df.interactive()
