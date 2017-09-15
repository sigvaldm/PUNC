from __future__ import print_function, division
import sys
if sys.version_info.major == 2:
	from itertools import izip as zip
	range = xrange

import dolfin as df
import numpy as np
from punc import *
import itertools as itr

def get_circles(index):
	"""
	Returns circles corresponding to a predefined mesh.
	"""
	tol = 1e-8
	r = 0.5
	s = [np.array([np.pi, np.pi]), np.array([np.pi, np.pi + 3*r]),
	     np.array([np.pi, np.pi - 3*r]), np.array([np.pi + 3*r, np.pi])]

	class Circle(df.SubDomain):
		def inside(self, x, on_boundary):
			return on_boundary and func(x)

	func = lambda x, s = s[index], r = r: np.dot(x-s, x-s) <= r**2+tol
	return Circle()

class CircleDomain(object):
	"""
	Return the mesh and creates the object for the circular object demo.
	"""
	def get_mesh(self):
		return df.Mesh("mesh/circle.xml")

	def get_objects(self, V):
		return [Object(V, get_circles(0))]

class CircuitDomain(object):
	"""
	Return the mesh and creates the objects for the demo of circuits.
	"""
	def get_mesh(self):
		return df.Mesh("mesh/circuit.xml")

	def get_circuits(self, objects, inv_cap_matrix):
		circuits_info = [[0, 2], [1, 3]]
		bias_potential = [[0.1], [0.2]]

		num_circuits = len(circuits_info)
		inv_bias_matrix = bias_matrix(inv_cap_matrix, circuits_info)

		bias_potential = list(itr.chain(*bias_potential))

		bias_0 = np.dot(inv_bias_matrix[:,:len(bias_potential)], bias_potential)
		# print("num_circuits: ", num_circuits)
		# print("inv_bias_matrix: ", inv_bias_matrix)
		# print("bias_potential: ", bias_potential)
		# print("bias_0: ", bias_0)
		circuits = []
		for i in range(num_circuits):
		    circuit_comps = []
		    circuit = circuits_info[i]; print("circuit: ", inv_bias_matrix[circuit, len(bias_potential):])
			# print("bias_0[circuit]: ", bias_0[circuit])
			# print("inv_bias_matrix[circuit,len(bias_potential):]: ",inv_bias_matrix[circuit, len(bias_potential):])
		    for j in circuit:
		        circuit_comps.append(objects[j])

		    circuits.append(Circuit(circuit_comps, bias_0[circuit],\
		                    inv_bias_matrix[circuit,len(bias_potential):]))

		return circuits

	def get_objects(self, V):
		num_objects = 4
		objects = [None]*num_objects
		for i in range(num_objects):
			objects[i] = Object(V, get_circles(i))
		return objects

class SphereDomain(object):
	"""
	Return the mesh and creates the object for the spherical object demo.
	"""
	def get_mesh(self):
		return df.Mesh("mesh/sphere.xml")

	def get_objects(self, V):
		tol = 1e-8
		r = 0.5
		s = np.array([np.pi, np.pi, np.pi])
		class Sphere(df.SubDomain):
			def inside(self, x, on_boundary):
				return on_boundary and func(x)

		func = lambda x, s = s, r = r: np.dot(x-s, x-s) <= r**2+tol
		return [Object(V, Sphere())]

class CylinderDomain(object):
	"""
	Return the mesh and creates the object for the cylindrical object demo.
	"""
	def get_mesh(self):
		return df.Mesh('mesh/cylinder_object.xml')

	def get_objects(self, V):
		tol = 1e-8
		r = 0.5
		h0, h = 2.0, 2*np.pi
		z0 = (h-h0)/2.      # Bottom point of cylinder
		z1 = (h+h0)/2.      # Top point of cylinder
		s = np.array([np.pi, np.pi])
		class Cylinder(df.SubDomain):
			def inside(self, x, on_boundary):
				return on_boundary and func(x)

		func = lambda x, s = s, r = r, h = h: x[2] >= z0 and x[2] <= z1 and\
		                                  np.dot(x[:-1]-s, x[:-1]-s) <= r**2+tol
		return [Object(V, Cylinder())]


if __name__=='__main__':

	def test_cylinder():
		circle = CylinderDomain()
		mesh = circle.get_mesh()
		Ld = get_mesh_size(mesh)

		V = df.FunctionSpace(mesh,'CG',1)

		objects = circle.get_objects(V)

		phi = [5,10,15, 20]
		for i, obj in enumerate(objects):
			obj.set_potential(phi[i])
			print("phi: ", obj._potential)
			print("inside: ", obj.inside([np.pi, np.pi, np.pi], True))
			dof = obj.get_boundary_values().keys()#dofs
			val = obj.get_boundary_values().values()
			print("dofs: ", dof)
			print("vals: ", val)

			f = df.Function(V)
			f.vector()[dof] = 5
			df.plot(f, interactive=True)
			obj.compute_interpolated_charge(f)
			print("interpolated_charge: ", obj.interpolated_charge)
			df.File("test_f.pvd") << f

	def test_sphere():
		circle = SphereDomain()
		mesh = circle.get_mesh()
		Ld = get_mesh_size(mesh)

		V = df.FunctionSpace(mesh,'CG',1)

		objects = circle.get_objects(V)

		phi = [5,10,15, 20]
		for i, obj in enumerate(objects):
			obj.set_potential(phi[i])
			print("phi: ", obj._potential)
			print("inside: ", obj.inside([np.pi, np.pi, np.pi], True))
			dof = obj.get_boundary_values().keys()#dofs
			val = obj.get_boundary_values().values()
			print("dofs: ", dof)
			print("vals: ", val)

			f = df.Function(V)
			f.vector()[dof] = 5
			df.plot(f, interactive=True)
			obj.compute_interpolated_charge(f)
			print("interpolated_charge: ", obj.interpolated_charge)
			df.File("test_f.pvd") << f

	def test_circuit():
		circle = CircuitDomain()
		mesh = circle.get_mesh()
		Ld = get_mesh_size(mesh)

		V = df.FunctionSpace(mesh,'CG',1)

		objects = circle.get_objects(V)

		phi = [5,10,15, 20]
		for i, obj in enumerate(objects):
			obj.set_potential(phi[i])
			print("phi: ", obj._potential)
			print("inside: ", obj.inside([np.pi, np.pi], True))
			dof = obj.get_boundary_values().keys()#dofs
			val = obj.get_boundary_values().values()
			print("dofs: ", dof)
			print("vals: ", val)

			f = df.Function(V)
			f.vector()[dof] = 5
			df.plot(f, interactive=True)
			obj.compute_interpolated_charge(f)
			print("interpolated_charge: ", obj.interpolated_charge)

	def test_circle_object():
		circle = CircleDomain()
		mesh = circle.get_mesh()
		Ld = get_mesh_size(mesh)

		V = df.FunctionSpace(mesh,'CG',1)

		objects = circle.get_objects(V)

		phi = [5,10,15, 20]
		for i, obj in enumerate(objects):
			obj.set_potential(phi[i])
			print("phi: ", obj._potential)
			print("inside: ", obj.inside([np.pi, np.pi], True))
			dof = obj.get_boundary_values().keys()#dofs
			val = obj.get_boundary_values().values()
			print("dofs: ", dof)
			print("vals: ", val)

			f = df.Function(V)
			f.vector()[dof] = 5
			df.plot(f, interactive=True)
			obj.compute_interpolated_charge(f)
			print("interpolated_charge: ", obj.interpolated_charge)

	def test_simple():
		from pylab import axis, show, triplot
		Ld = [1., 2.]
		N = [20, 10]
		mesh = simple_mesh(Ld, N)
		coords = mesh.coordinates()
		triplot(coords[:,0], coords[:,1], triangles=mesh.cells())
		axis('equal')
		show()

	def test_unit():
		from pylab import axis, show, triplot
		N = [20, 10]
		mesh = unit_mesh(N)
		coords = mesh.coordinates()
		triplot(coords[:,0], coords[:,1], triangles=mesh.cells())
		axis('equal')
		show()


	test_simple()
	# test_unit()
	# test_circle_object()
	# test_circuit()
	# test_sphere()
	# test_cylinder()
