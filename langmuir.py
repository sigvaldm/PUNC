from dolfin import *
import LagrangianParticles as lp
import numpy as np
import matplotlib.pyplot as plt

show_plot = True

#==============================================================================
# SOLVER
#------------------------------------------------------------------------------

if not has_linear_algebra_backend("PETSc"):
    info("langmuir.py needs PETSc")
    exit()

parameters["linear_algebra_backend"] = "PETSc"

#==============================================================================
# MESH
#------------------------------------------------------------------------------

Lx = 2*DOLFIN_PI
Ly = 2*DOLFIN_PI
Nx = 32
Ny = 32
mesh = RectangleMesh(Point(0,0),Point(Lx,Ly),Nx,Ny)

if(show_plot): plot(mesh)

#==============================================================================
# FUNCTION SPACE
#------------------------------------------------------------------------------

class PeriodicBoundary(SubDomain):

	# Target domain
	def inside(self, x, on_bnd):
		return bool(		(near(x[0],0)  or near(x[1],0))	 # On a lower bound
					and not (near(x[0],Lx) or near(x[1],Ly)) # But not an upper
					and on_bnd)

	# Map upper edges to lower edges
	def map(self, x, y):
		y[0] = x[0]-Lx if near(x[0],Lx) else x[0]
		y[1] = x[1]-Ly if near(x[1],Ly) else x[1]

constrained_domain=PeriodicBoundary()

D =       FunctionSpace(mesh, 'DG', 0, constrained_domain=constrained_domain)
S =       FunctionSpace(mesh, 'CG', 1, constrained_domain=constrained_domain)
V = VectorFunctionSpace(mesh, 'CG', 1, constrained_domain=constrained_domain)

#==============================================================================
# PARTICLES
#------------------------------------------------------------------------------

Npx = Nx*16
Npy = Ny*16
Np = Npx*Npy

q = np.array([-1., 1.])
m = np.array([1., 1836.])

multiplicity = (Lx*Ly/Np)*m[0]/(q[0]**2)

q *= multiplicity
m *= multiplicity

qm = q/m

lpart = lp.LagrangianParticles(S)

# Place particls in lattice

#x = np.arange(0,Lx,Lx/Npx)
#y = np.arange(0,Ly,Ly/Npy)
#x = np.linspace(0,Lx,Npx,endpoint=False)
#y = np.linspace(0,Ly,Npy,endpoint=False)
##x = x+0.001*np.sin(x)
#xcart = np.tile(x,Npy)
#ycart = np.repeat(y,Npx)
#pos = np.c_[xcart,ycart]

#pos = lp.RandomCircle(Point(Lx/2,Ly/2),Lx/4).generate([Npx,Npy])

# Electrons
pos = lp.RandomRectangle(Point(0,0),Point(Lx,Ly)).generate([Npx,Npy])
pos[:,0] += 0.052*np.sin(2*pos[:,0])

q0 = q[0]*np.ones(len(pos))
lpart.add_particles(pos,{'q':q0})

# Ions
pos = lp.RandomRectangle(Point(0,0),Point(Lx,Ly)).generate([Npx,Npy])

q1 = q[1]*np.ones(len(pos))
lpart.add_particles(pos,{'q':q1})

#for (i,p) in enumerate(lpart):
#	p.properties = {'q':q[i/Np], 'qm':qm[i/Np], 'm':m[i/Np]}

fig = plt.figure()
lpart.scatter(fig)
fig.suptitle('Initial Particle Position')
plt.axis([0, Lx, 0, Ly])
fig.savefig("particles.png")

#==============================================================================
# RHO
#------------------------------------------------------------------------------

rhoD = Function(D)
dofmap = D.dofmap()

## Simply count particles
#for c in cells(mesh):
#	cindex = c.index()
#	dofindex = dofmap.cell_dofs(cindex)[0]
#	try:
#		count = len(lpart.particle_map[cindex])
#	except:
#		count = 0
##	print cindex, count
#	rhoD.vector()[dofindex] = count

for c in cells(mesh):
	cindex = c.index()
	dofindex = dofmap.cell_dofs(cindex)[0]
	cellcharge = 0
	for particle in lpart.particle_map[cindex].particles:
		cellcharge += particle.properties['q']
	rhoD.vector()[dofindex] = cellcharge

rho = project(rhoD,S)
#rho = Expression('sin((2*DOLFIN_PI/%f)*x[0])'%Lx)

if(show_plot): plot(rhoD)
if(show_plot): plot(rho)

#==============================================================================
# RHO -> PHI
#------------------------------------------------------------------------------

# Fix undetermined constant in phi
bc = DirichletBC(S,Constant(0),"near(x[0],0)")
bc = []

phi = TrialFunction(S)
phi_ = TestFunction(S)

a = inner(nabla_grad(phi), nabla_grad(phi_))*dx
L = rho*phi_*dx

A = assemble(a)
b = assemble(L)

solver = PETScKrylovSolver("cg")
solver.set_operator(A)

phi = Function(S)

null_vec = Vector(phi.vector())
S.dofmap().set(null_vec, 1.0)
null_vec *= 1.0/null_vec.norm("l2")

null_space = VectorSpaceBasis([null_vec])
as_backend_type(A).set_nullspace(null_space)

null_space.orthogonalize(b);

#solve(a == L, phi, bc)
solver.solve(phi.vector(), b)

if(show_plot): plot(phi)

#==============================================================================
# PHI -> E
#------------------------------------------------------------------------------

# TBD:
# Possibly replace by fenicstools WeightedGradient.py
# Need to take check boundary artifacts

E = project(-grad(phi), V)

x_hat = Expression(('1.0','0.0'))
Ex = dot(E,x_hat)

if(show_plot): plot(Ex)
interactive()
