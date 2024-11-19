
def get_coef(f, v):
    coefs = f.coefficients()
    monos = f.monomials()

    return coefs[monos.index(v)]

def EllipticCurve_from_cubic_modified(F, P=None):
    from sage.rings.polynomial.multi_polynomial_ring import MPolynomialRing_base
    from sage.schemes.curves.constructor import Curve
    from sage.matrix.constructor import Matrix
    from sage.schemes.elliptic_curves.weierstrass_transform import \
        WeierstrassTransformationWithInverse

    # check the input
    R = F.parent()
    K = R.base_ring()
    if not isinstance(R, MPolynomialRing_base):
        raise TypeError('equation must be a polynomial')
    if R.ngens() != 3 or F.nvariables() != 3:
        raise TypeError('equation must be a polynomial in three variables')
    if not F.is_homogeneous():
        raise TypeError('equation must be a homogeneous polynomial')

    C = Curve(F)
    if P:
        try:
            CP = C(P)
        except (TypeError, ValueError):
            raise TypeError('{} does not define a point on a projective curve over {} defined by {}'.format(P,K,F))

    x, y, z = R.gens()

    # Test whether P is a flex; if not test whether there are any rational flexes:

    hessian = Matrix([[F.derivative(v1, v2) for v1 in R.gens()] for v2 in R.gens()]).det()
    if P and hessian(P) == 0:
        flex_point = P
    else:
        flexes = C.intersection(Curve(hessian)).rational_points()
        if flexes:
            flex_point = list(flexes[0])
            if not P:
                P = flex_point
                CP = C(P)
        else:
            flex_point = None

    if flex_point is not None: # first case: base point is a flex
        P = flex_point
        L = tangent_at_smooth_point(C,P)
        print(L)
        dx, dy, dz = (get_coef(L, v) for v in R.gens())

        # find an invertible matrix M such that (0,1,0)M=P and
        # ML'=(0,0,1)' where L=[dx,dy,dx].  Then the linear transform
        # by M takes P to [0,1,0] and L to Z=0:

        if P[0]:
            Q1 = [0,-dz,dy]
            Q2 = [0,1,0] if dy else [0,0,1]
        elif P[1]:
            Q1 = [dz,0,-dx]
            Q2 = [1,0,0] if dx else [0,0,1]
        else:
            Q1 = [-dy,dx,0]
            Q2 = [1,0,0] if dx else [0,1,0]

        M = Matrix([Q1,P,Q2])
        # assert M.is_invertible()
        # assert list(vector([0,1,0])*M) == P
        # assert list(M*vector([dx,dy,dz]))[:2] == [0,0]

        M = M.transpose()
        # F2 = R(M.act_on_polynomial(F))
        F2 = M.act_on_polynomial(F)

        # scale and dehomogenise
        a = get_coef(F2, x**3) # K(F3.coefficient(x**3))
        b = get_coef(F2, y*y*z) # K(F3.coefficient(y*y*z))

        F3 = F2([-x, y/b, z*a*b]) / a
        # assert F3.coefficient(x**3) == -1
        # assert F3.coefficient(y*y*z) == 1
        # E = EllipticCurve(F3([x,y,1]))
        # if not morphism:
        #     # return E
        #     return F3([x, y, 1])

        # Construct the (linear) morphism
        M = M * Matrix(K,[[-1,0,0],[0,1/b,0],[0,0,a*b]])
        inv_defining_poly = [ M[i,0]*x + M[i,1]*y + M[i,2]*z for i in range(3) ]
        inv_post = 1/a
        M = M.inverse()
        fwd_defining_poly = [ M[i,0]*x + M[i,1]*y + M[i,2]*z for i in range(3) ]
        fwd_post = a

        return F3([x, y, 1]), WeierstrassTransformationWithInverse(
            C, E, fwd_defining_poly, fwd_post, inv_defining_poly, inv_post)

    else: # Second case: no flexes
        if not P:
            raise ValueError('A point must be given when the cubic has no rational flexes')
        L = tangent_at_smooth_point(C,P)
        Qlist = [Q for Q in C.intersection(Curve(L)).rational_points() if C(Q) != CP]
        # assert Qlist
        P2 = C(Qlist[0])
        L2 = tangent_at_smooth_point(C,P2)
        Qlist = [Q for Q in C.intersection(Curve(L2)).rational_points() if C(Q) != P2]
        # assert Qlist
        P3 = C(Qlist[0])

        # NB This construction of P3 relies on P2 not being a flex.
        # If we want to use a non-flex as P when there are rational
        # flexes this would be a problem.  However, the only condition
        # which P3 must satisfy is that it is on the tangent at P2, it
        # need not lie on the cubic.

        # send P, P2, P3 to (1:0:0), (0:1:0), (0:0:1) respectively
        M = Matrix([P, list(P2), list(P3)]).transpose()
        F2 = M.act_on_polynomial(F)
        xyzM = [ M[i,0]*x + M[i,1]*y + M[i,2]*z for i in range(3) ]
        # assert F(xyzM)==F2

        # substitute x = U^2, y = V*W, z = U*W, and rename (x,y,z)=(U,V,W)
        T1 = [x*x,y*z,x*z]
        S1 = x**2*z
        F3 = F2(T1) // S1
        xyzC = [ t(T1) for t in xyzM ]
        # assert F3 == F(xyzC) // S1

        # scale and dehomogenise
        a = get_coef(F3, x**3) # K(F3.coefficient(x**3))
        b = get_coef(F3, y*y*z) # K(F3.coefficient(y*y*z))
        ab = a*b

        T2 = [-x, y/b, ab*z]
        F4 = F3(T2) / a
        # assert F4.coefficient(x**3) == -1
        # assert F4.coefficient(y*y*z) == 1
        xyzW = [ t(T2) for t in xyzC ]
        S2 = a*S1(T2)
        # assert F4 == F(xyzW) // S2

        E = EllipticCurve(F4([x,y,1]))
        # if not morphism:
        #     # return E
        #     return F4([x, y, 1])

        inv_defining_poly = xyzW
        inv_post = 1/S2
        # assert F4==F(inv_defining_poly)*inv_post
        MI = M.inverse()
        xyzI = [ (MI[i,0]*x + MI[i,1]*y + MI[i,2]*z) for i in range(3) ]
        T1I = [x*z,x*y,z*z] # inverse of T1
        xyzIC = [ t(xyzI) for t in T1I ]
        T2I = [-x, b*y, z/ab] # inverse of T2
        xyzIW = [ t(xyzIC) for t in T2I ]
        fwd_defining_poly = xyzIW
        fwd_post = a/(x*z*z)(xyzI)
        # assert F4(fwd_defining_poly)*fwd_post == F

        return F4([x, y, 1]), WeierstrassTransformationWithInverse(
            C, E, fwd_defining_poly, fwd_post, inv_defining_poly, inv_post)

    # Construct the morphism

    return WeierstrassTransformationWithInverse(
        C, E, fwd_defining_poly, fwd_post, inv_defining_poly, inv_post)

def tangent_at_smooth_point(C,P):
    try:
        return C.tangents(P)[0]
    except NotImplementedError:
        return C.tangents(P,factor=False)[0]


def chord_and_tangent(F, P):
    from sage.schemes.curves.constructor import Curve
    # check the input
    R = F.parent()
    if not isinstance(R, MPolynomialRing_base):
        raise TypeError('equation must be a polynomial')
    if R.ngens() != 3:
        raise TypeError('{} is not a polynomial in three variables'.format(F))
    if not F.is_homogeneous():
        raise TypeError('{} is not a homogeneous polynomial'.format(F))
    x, y, z = R.gens()
    if len(P) != 3:
        raise TypeError('{} is not a projective point'.format(P))
    K = R.base_ring()
    try:
        C = Curve(F)
        P = C(P)
    except (TypeError, ValueError):
        raise TypeError('{} does not define a point on a projective curve over {} defined by {}'.format(P,K,F))

    L = Curve(tangent_at_smooth_point(C,P))
    Qlist = [Q for Q in C.intersection(L).rational_points() if Q != P]
    if Qlist:
        return Qlist[0]
    return P


import time

def method1(alpha, beta):
    P.<n> = PolynomialRing(QQ)
    R.<x,y,z> = PolynomialRing(P)

    f = (x / (alpha * y + beta * z) + y / (alpha * z + beta * x) + z / (alpha * x + beta * y) - n).numerator()
    P = [beta, -alpha, 0]
    E, morph = EllipticCurve_from_cubic_modified(f, P)

    T = EllipticCurve(E)

    res = (2 * T(0, 0)).xy()

    a, b, c = morph.inverse()(res)._coords
    assert c == 1

    l = lcm(a.denominator(), b.denominator())
    a, b, c = l * a, l * b, l * c

    res = []
    for i in range(1, 101):
        a2, b2, c2 = a(i), b(i), c(i)
        l = lcm(a2.denominator(), lcm(b2.denominator(), c2.denominator()))
        a2, b2, c2 = l * a2, l * b2, l * c2
        res.append((a2, b2, c2))
    
    return res

def method2(alpha, beta):
    R.<x, y, z> = PolynomialRing(QQ)

    res = []
    for n in range(1, 1 + 100):
        f = (x / (alpha * y + beta * z) + y / (alpha * z + beta * x) + z / (alpha * x + beta * y) - n).numerator()
        P = [beta, -alpha, 0]

        E = EllipticCurve_from_cubic(f, P, morphism=False)
        morph = EllipticCurve_from_cubic(f, P, morphism=True)

        P = 2 * E(0, 0)

        a, b, c = morph.inverse()(P.xy())._coords
        assert c == 1

        l = lcm(a.denominator(), b.denominator())
        a, b, c = l * a, l * b, l * c
        res.append((a, b, c))
    return res


for _ in range(100):
    alpha = randint(1, 100)
    beta = randint(1, 100)

    st = time.perf_counter()
    method1(alpha, beta)
    md = time.perf_counter()
    method2(alpha, beta)
    ed = time.perf_counter()

    print(f"Result on ({alpha}, {beta}) - Method 1: {md - st}, 2: {ed - md}")
