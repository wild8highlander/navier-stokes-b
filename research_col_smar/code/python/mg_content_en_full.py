# -*- coding: utf-8 -*-
"""Assemble the full English monograph content + references."""

from mg_content_en import C, META

import mg_content_en2  # noqa: F401
import mg_content_en4  # noqa: F401  (chapter 12: 3D smoothness, P5)
import mg_content_en3  # noqa: F401
import mg_content_en5  # noqa: F401  (sections 12.7/12.8: P5-B 96^3 and P5-C ensembles)

REFS = [
    "Kolmogorov A. N. The local structure of turbulence in incompressible viscous fluid for very large Reynolds numbers // Dokl. Akad. Nauk SSSR. 1941. V. 30. P. 301-305.",
    "Kolmogorov A. N. Dissipation of energy in locally isotropic turbulence // Dokl. Akad. Nauk SSSR. 1941. V. 32. P. 16-18.",
    "Obukhov A. M. On the distribution of energy in the spectrum of turbulent flow // Dokl. Akad. Nauk SSSR. 1941. V. 32. P. 22-24.",
    "Heisenberg W. Zur statistischen Theorie der Turbulenz // Z. Phys. 1948. V. 124. P. 628-657.",
    "Kraichnan R. H. The structure of isotropic turbulence at very high Reynolds numbers // J. Fluid Mech. 1959. V. 5. P. 497-543.",
    "Kraichnan R. H. Lagrangian-history closure approximation for turbulence // Phys. Fluids. 1965. V. 8. P. 575-598.",
    "Kraichnan R. H. Inertial ranges in two-dimensional turbulence // Phys. Fluids. 1967. V. 10. P. 1417-1423.",
    "Smagorinsky J. General circulation experiments with the primitive equations // Mon. Wea. Rev. 1963. V. 91. P. 99-164.",
    "Lilly D. K. The representation of small-scale turbulence in numerical simulation experiments // Proc. IBM Sci. Comput. Symp. 1967. P. 195-210.",
    "Lilly D. K. A proposed modification of the Germano subgrid-scale closure method // Phys. Fluids A. 1992. V. 4. P. 633-635.",
    "Deardorff J. W. A numerical study of three-dimensional turbulent channel flow at large Reynolds numbers // J. Fluid Mech. 1970. V. 41. P. 453-480.",
    "Deardorff J. W. Stratocumulus-capped mixed layers derived from a three-dimensional model // Bound.-Layer Meteor. 1974. V. 7. P. 81-106.",
    "Germano M. Turbulence: the filtering approach // J. Fluid Mech. 1992. V. 238. P. 325-336.",
    "Germano M., Piomelli U., Moin P., Cabot W. H. A dynamic subgrid-scale eddy viscosity model // Phys. Fluids A. 1991. V. 3. P. 1760-1765.",
    "Moin P., Kim J. Numerical investigation of turbulent channel flow // J. Fluid Mech. 1982. V. 118. P. 341-377.",
    "Piomelli U., Zang T. A., Speziale C. G., Hussaini M. Y. On the large-eddy simulation of transitional wall-bounded flows // Phys. Fluids A. 1990. V. 2. P. 257-265.",
    "Pope S. B. Turbulent Flows. Cambridge University Press, 2000.",
    "Frisch U. Turbulence: The Legacy of A. N. Kolmogorov. Cambridge University Press, 1995.",
    "Sagaut P. Large Eddy Simulation for Incompressible Flows. 3rd ed. Springer, 2006.",
    "Meneveau C., Katz J. Scale-invariance and turbulence models for large-eddy simulation // Annu. Rev. Fluid Mech. 2000. V. 32. P. 1-32.",
    "Sreenivasan K. R. On the universality of the Kolmogorov constant // Phys. Fluids. 1995. V. 7. P. 2778-2784.",
    "Yeung P. K., Zhou Y. Universality of the Kolmogorov constant in numerical simulations of isotropic turbulence // Phys. Rev. E. 1997. V. 56. P. 1746-1752.",
    "Kaneda Y., Ishihara T., Yokokawa M., Itakura K., Uno A. Energy dissipation rate and energy spectrum in high resolution direct numerical simulations of turbulence in a periodic box // Phys. Fluids. 2003. V. 15. L21-L24.",
    "Ishihara T., Gotoh T., Kaneda Y. Study of high-Reynolds number isotropic turbulence by direct numerical simulation // Annu. Rev. Fluid Mech. 2009. V. 41. P. 165-180.",
    "Grant H. L., Stewart R. W., Moilliet A. Turbulence spectra from a tidal channel // J. Fluid Mech. 1962. V. 12. P. 241-268.",
    "Champagne F. H. The fine-scale structure of the turbulent velocity field // J. Fluid Mech. 1978. V. 86. P. 67-108.",
    "Gledzer E. B. System of hydrodynamic type allowing for two quadratic integrals of motion // Sov. Phys. Dokl. 1973. V. 18. P. 216-217.",
    "Yamada M., Ohkitani K. Lyapunov spectrum of a chaotic model of three-dimensional turbulence // J. Phys. Soc. Jpn. 1987. V. 56. P. 4210-4213.",
    "L'vov V. S., Podivilov E., Stepanov A., Bloom-Garden I., Frisch U. Improved shell model of turbulence // Phys. Rev. E. 1998. V. 58. P. 4146-4157.",
    "Biferale L. Shell models of energy cascade in turbulence // Annu. Rev. Fluid Mech. 2003. V. 35. P. 441-468.",
    "Ditlevsen P. D. Turbulence and Shell Models. Cambridge University Press, 2011.",
    "Porte-Agel F., Meneveau C., Parlange M. B. A scale-dependent dynamic model for large-eddy simulation // J. Fluid Mech. 2000. V. 415. P. 261-284.",
    "Vreman A. W. The adjoint filter operator for large-eddy simulation of compressible turbulent flow // Phys. Fluids. 2004. V. 16. P. 2012-2018.",
    "Silvis M. H., Remmerswaal R. A., Verstappen R. Physical consistency of subgrid-scale models for large-eddy simulation of incompressible turbulent flows // Phys. Fluids. 2016. V. 28. 015105.",
    "Buaria D., Pumir A., Bodenschatz E., Yeung P. K. Extreme velocity gradients in turbulent flows // New J. Phys. 2022. V. 24. 013007.",
    "Leray J. Essai sur le mouvement plan d'un fluide visqueux que limitent des parois // J. Math. Pures Appl. 1934. V. 13. P. 331-418.",
    "Ladyzhenskaya O. A. Sixth problem of the millennium: what is new? // Russ. Math. Surv. 2003. V. 58. No. 2. P. 295-311.",
    "Ladyzhenskaya O. A. On the uniqueness and global estimability of solutions of the Navier-Stokes equations // Dokl. Akad. Nauk SSSR. 1967. V. 175. P. 267-270.",
    "Prodi G. Un teorema di unicità per le equazioni di Navier-Stokes // Ann. Mat. Pura Appl. 1959. V. 48. P. 173-182.",
    "Serrin J. On the interior regularity of weak solutions of the Navier-Stokes equations // Arch. Ration. Mech. Anal. 1962. V. 8. P. 187-195.",
    "Caffarelli L., Kohn R., Nirenberg L. Partial regularity of suitable weak solutions of the Navier-Stokes equations // Comm. Pure Appl. Math. 1982. V. 35. P. 771-831.",
    "Lin F. H. A new proof of the Caffarelli-Kohn-Nirenberg theorem // Comm. Pure Appl. Math. 1986. V. 39. P. 273-292.",
    "Beale J. T., Kato T., Majda A. Remarks on the breakdown of smooth solutions for the 3-D Euler equations // Comm. Math. Phys. 1984. V. 94. P. 61-66.",
    "Constantin P., Fefferman C. Direction of vorticity and the problem of global regularity for the Navier-Stokes equations // Indiana Univ. Math. J. 1993. V. 42. P. 775-789.",
    "Ashurst W. T. R., Kerstein A. R., Kerr R. M., Gibson C. H. Alignment of vorticity and scalar gradient with strain rate in simulated Navier-Stokes turbulence // Physics of Fluids. 1987. V. 30. P. 2343-2353.",
    "Ladyzhenskaya O. A., Seregin G. A. On partial regularity of suitable weak solutions to the three-dimensional Navier-Stokes equations // J. Math. Fluid Mech. 1999. V. 1. P. 356-387.",
    "Rípamonti M. F., Seregin G. A. Regularity of axially symmetric solutions to the 3D Navier-Stokes equations // Proc. Steklov Inst. Math. 2013. V. 283. P. 121-132.",
    "Doering C. R., Gibbon J. D. Applied Analysis of the Navier-Stokes Equations. Cambridge University Press, 1995.",
    "Foias C., Manley O., Rosa R., Temam R. Navier-Stokes Equations and Turbulence. Cambridge University Press, 2001.",
    "Tao T. Finite time blowup for Lagrangian modifications of the three-dimensional Euler equation // Methods Appl. Anal. 2016. V. 23. P. 165-176.",
    "Colombo M., Haffter D. Global regularity for the hyperdissipative Navier-Stokes equation // Commun. Math. Phys. 2018. V. 358. P. 193-208.",
    "Brachet M., Meiron D. I., Orszag S. A., Nickel B. G., Morf R. H., Frisch U. Small-scale structure of the Taylor-Green vortex // J. Fluid Mech. 1983. V. 130. P. 411-452.",
    "wild8highlander. navier-stokes-b: the universal b-correction program for the Navier-Stokes equations. Repository, 2026.",
]

insert_at = None
for i, block in enumerate(C):
    if block[0] == "h1" and block[1].startswith("Appendix A"):
        insert_at = i
        break
lit_blocks = [("h1", "References")] + [("ref", r) for r in REFS]
if insert_at is not None:
    C[insert_at:insert_at] = lit_blocks
else:
    C.extend(lit_blocks)

CONTENT_EN = C
