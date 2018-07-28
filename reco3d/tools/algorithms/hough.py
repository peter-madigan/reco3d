'''
Compute the 3D Hough transform from a point cloud.
Based on the algorithm described in Dalitz, Schramke, Jeltsch [2017].

'''
import numpy as np
import sympy as sp

from larpixreco.RecoLogging import getLogger
logger = getLogger(__name__)

class Line(object):
    '''A line in 3D.'''

    def __init__(self, theta, phi, xp, yp):
        '''
            Define a new line using the "Roberts optimal line
            representation."

            Theta and phi use the usual physics spherical coordinate
            definitions and are in radians. Theta (0 to pi/2) represents
            the angle to the z axis. Phi (-pi to pi) represents the angle
            between the projection on the x-y plane and the x axis, with
            the +y direction at phi = pi/2.

            Theta and phi define the direction of the line, represented
            by the unit vector b. xp and yp define the position of the
            line in the following sense:

            - consider the rotation between the unit vector (0, 0, 1) and
              the direction vector b
            - rotate the xyz coordinate system by the same rotation to
              create the primed coordinate system, so that b is now
              pointing in the z-prime direction.
            - xp and yp are the point of intersection between the line
              and the x-prime / y-prime plane

            Angular ambiguities:
              - Theta is restricted to [0, pi/2]
              - There are additional ambiguities if the line lies exactly
                in the x-y plane but I don't think they are relevant.
        '''
        self.theta = theta
        self.phi = phi
        self.xp = xp
        self.yp = yp
        self.cov = None

    def coords(self):
        '''
            Return a tuple of coordinates (theta, phi, xp, yp).

        '''
        return (self.theta, self.phi, self.xp, self.yp)

    def points(self, coord, min_coord, max_coord, npoints):
        '''
            Return a list of n Cartesian points along the line ranging
            from coord=min_coord to coord=max_coord, where coord='x',
            'y', or 'z'.
        '''
        theta = self.theta
        phi = self.phi
        xp = self.xp
        yp = self.yp
        sintheta = np.sin(theta)
        bx = np.cos(phi)*sintheta
        by = np.sin(phi)*sintheta
        bz = np.cos(theta)
        b = np.array([bx, by, bz])
        A = -(bx * by)/(1 + bz)
        B = 1 - (bx * bx)/(1 + bz)
        C = 1 - (by * by)/(1 + bz)

        p0 = xp * np.array([B, A, -bx]) + yp * np.array([A, C, -by])
        distance = None
        num_bs_in_range = None
        if coord == 'x':
            distance = (p0[0] - min_coord)/bx
            num_bs_in_range = (max_coord - min_coord)/bx
        elif coord == 'y':
            distance = (p0[1] - min_coord)/by
            num_bs_in_range = (max_coord - min_coord)/by
        elif coord == 'z':
            distance = (p0[2] - min_coord)/bz
            num_bs_in_range = (max_coord - min_coord)/bz
        else:
            raise ValueError('Bad coord')

        p1 = p0 - distance * b
        prefactor = num_bs_in_range/(npoints-1)
        prefactor_array = (prefactor *
                np.arange(npoints).reshape((npoints, 1)))
        jumps = prefactor_array * np.tile(b, (npoints, 1))
        points = p1 + jumps
        return points

    def distance_to(self, point):
        '''
            Return the perpendicular distance of this line to the given
            point.
        '''
        point_on_line = self.points('x', point[0], point[0] + 10, 2)[0]
        theta = self.theta
        phi = self.phi
        sintheta = np.sin(theta)
        bx = np.cos(phi)*sintheta
        by = np.sin(phi)*sintheta
        bz = np.cos(theta)
        direction = np.array([bx, by, bz])
        first_part = point_on_line - point
        second_part = np.dot(direction, first_part) * direction
        vector = first_part - second_part
        distance = np.linalg.norm(vector)
        return distance

    @classmethod
    def fromDirPoint(cls, theta, phi, px, py, pz):
        '''
            Create a new line given the direction of the line and the
            coordinates of a point on the line.
        '''
        return cls(theta, phi, *compute_xp_yp(theta, phi, px, py, pz))

    @classmethod
    def applyTranslation(cls, original, translation):
        '''
            Return a new line which has been translated by the given
            translation vector.
        '''
        point = original.points('x', 0, 1, 2)[0]
        theta, phi = original.theta, original.phi
        px, py, pz = point + translation
        xp, yp = compute_xp_yp(theta, phi, px, py, pz)
        return cls(theta, phi, xp, yp)

def compute_xp_yp(theta, phi, px, py, pz):
    '''
        Compute xp and yp given the direction vector's angles and the
        (unprimed) coordinates of any point on the line, compute xp and
        yp.
    '''
    sintheta = np.sin(theta)
    bx = np.cos(phi)*sintheta
    by = np.sin(phi)*sintheta
    bz = np.cos(theta)

    A = (bx * by)/(1 + bz)
    B = 1 - (bx * bx)/(1 + bz)
    C = 1 - (by * by)/(1 + bz)

    xp = B * px - A * py - bx * pz
    yp = -A * px + C * py - by * pz

    return (xp, yp)

def center_translate(points):
    '''
        Apply a constant translation so the point cloud is centered at
        the origin (judging by the distance between xmin and xmax, ymin
        and ymax, and zmin and zmax).

        The translation vector is computed and then applied according to
        ``new_points = old_points - translation``.

        Return the translated points, the translation vector, and a
        function to undo the translation, e.g. ``lambda points: points +
        translation``.
    '''
    maxes = points.max(axis=0)
    mins = points.min(axis=0)
    translation = 0.5 * (maxes + mins)
    centered_points = points - translation
    def undo_translation(new_points):
        return new_points + translation

    return (centered_points, translation, undo_translation)

def fibonacci_hemisphere(samples):
    '''
        Use the Fibonacci sphere method to create a hemisphere of
        (mostly-)evenly spaced points, usable as a set of directions to
        test for the Hough transform. Returns points in Cartesian
        coordinates.
    '''
    points = np.empty((samples, 3))
    samples = samples * 2
    offset = 2./samples
    increment = np.pi * (3. - np.sqrt(5.))

    index = 0
    for i in range(samples):
        y = ((i * offset) - 1) + (offset / 2)
        r = np.sqrt(1 - pow(y,2))

        phi = ((i + 1) % samples) * increment

        x = np.cos(phi) * r
        z = np.sin(phi) * r
        if z >= 0:
            points[index] = [x, y, z]
            index += 1
        if index == samples/2:
            break

    return points

def cartesian_to_spherical(points, constrain=False):
    '''
       Convert the given points into spherical coordinates assuming they
       are unit vectors.

       If constrain, restrict theta to [0, pi/2].

       The range of phi is [-pi, pi].

    '''
    if constrain:
        to_flip = points[:, 2] < 0
        points = np.where(to_flip, -points.T, points.T).T
    phi = np.arctan2(points[:,1], points[:,0])  # arctan(y/x)
    theta = np.arccos(points[:,2])
    return np.vstack((theta, phi)).T

def get_xp_yp_edges(points, nbins):
    '''
        Given the point cloud, return (xp_edges, yp_edges).
    '''
    maxes = points.max(axis=0)
    mins = points.min(axis=0)
    ranges = 0.5 * (maxes - mins)
    range_dist = np.linalg.norm(ranges)
    xp_edges = np.linspace(-range_dist, range_dist, nbins+1)
    yp_edges = xp_edges.copy()
    return xp_edges, yp_edges

def get_directions(npoints):
    '''
        Generate ``npoints`` distinct directions which are approximately
        uniformly distributed using the Fibonacci hemisphere algorithm.

        Returns a 2D array whose rows are [theta, phi].
    '''
    return cartesian_to_spherical(fibonacci_hemisphere(npoints))

def get_line_from_indices(dir_i, xp_i, yp_i, dirs, xp, yp, translation):
    '''
        Return the Line specified by the given direction, xprime,
        yprime, and translation.
    '''
    theta, phi = dirs[dir_i]
    xp, yp = xp[xp_i], yp[yp_i]
    raw_line = Line(theta, phi, xp, yp)
    line = Line.applyTranslation(raw_line, translation)
    return line

def cov_evals_evecs(points):
    '''
        Return the eigenvalues and eigenvectors of the covariance matrix
        for the specified points.

        Returns (evals, evecs) sorted in descending order by eigenvalue.
        Note that the numpy convention is that the eigenvector array
        has shape (ndims, neigenvecs) so that the columns specify
        eigenvectors and the rows specify x-y-z. This is the opposite
        convention from the points array where the rows specify the
        points.

    '''
    x = points - np.mean(points, axis=0)
    cov = np.cov(x, rowvar=False)
    evals, evecs = np.linalg.eigh(cov)
    order = np.argsort(evals)[::-1]
    evecs = evecs[:, order]
    evals = evals[order]
    return evals, evecs

class HoughParameters(object):
    '''
        Keep track of the parameters used for a series of Hough
        transforms.

        The shape of the accumulator array is: (ndirections, npositions,
        npositions).

        The directions are a 2d array of [theta, prime].

        The position bin edges are an array of length
        npositions + 1 and apply to both the x-prime and y-prime axes.

        The translation is a constant vector which describes how the
        input points are translated to simplify the Hough transformation
        computation. To ensure the lines extracted from the accumulator
        are accurate, you must displace the line specified by
        (direction, xprime, yprime) by adding the
        translation vector to each of its points. This is handled
        by the ``Line.applyTranslation`` function.

        The found_mask boolean array tells which points have already
        been assigned to a line (True) or have not yet (False).
    '''
    def __init__(self):
        self.ndirections = None
        self.npositions = None
        self.directions = None
        self.position_bins = None
        self.translation = None
        self.accumulator = None
        self.dr = None

        self.found_mask = None

def compute_hough(points, params, op='+'):
    '''
        Compute the Hough transformation of the given points and return
        an updated Parameters object.

        The input point coordinates should be expressed in the same
        units/dimensions so that the discretization of parameter space
        is appropriate for the point cloud geometry.

        If ``op == '+'``, then each vote for a specific line adds to the
        accumulator array. If ``op == '-'``, then each vote subtracts
        from the accumulator array. The latter option is useful when
        running the iterative algorithm.
    '''
    # Prepare the data and accumulator array
    input_points = points
    test_directions = None
    if params.directions is None:
        test_directions = get_directions(params.ndirections)
        params.directions = test_directions
    else:
        test_directions = params.directions

    if params.translation is None:
        points, translation, undo_translation = center_translate(input_points)
        params.translation = translation
    else:
        points = input_points - params.translation
    xp_edges = None
    yp_edges = None
    if params.position_bins is None:
        xp_edges, yp_edges = get_xp_yp_edges(points, params.npositions)
        params.position_bins = xp_edges
        params.dr = xp_edges[1] - xp_edges[0]
    else:
        xp_edges = params.position_bins
        yp_edges = params.position_bins
    accumulator = None
    if params.accumulator is None:
        params.accumulator = np.zeros((
            len(test_directions),
            len(xp_edges) - 1,
            len(yp_edges) - 1))
        accumulator = params.accumulator
    else:
        accumulator = params.accumulator
    max_xp_i = accumulator.shape[1] - 1
    max_yp_i = accumulator.shape[2] - 1

    # Compute the Hough transformation
    for point in points:
        for i, (theta, phi) in enumerate(test_directions):
                xp, yp = compute_xp_yp(theta, phi, *point)
                xp_i = max(0, min(np.searchsorted(xp_edges, xp)-1, max_xp_i))
                yp_i = max(0, min(np.searchsorted(yp_edges, yp)-1,
                    max_yp_i))
                if op == '+':
                    accumulator[i, xp_i, yp_i] += 1
                elif op == '-':
                    accumulator[i, xp_i, yp_i] -= 1
                else:
                    raise ValueError('Invalid op (must be "+" or "-")')

    return params

def line_accumulator_max(params):
    '''
        Return the line specified by the maximum bin in the accumulator.
    '''
    indices = np.unravel_index(np.argmax(params.accumulator),
            params.accumulator.shape)
    dir_i, xp_i, yp_i = indices
    bins = params.position_bins
    line = get_line_from_indices(dir_i, xp_i, yp_i, params.directions,
            bins, bins, params.translation)
    return line

def points_close_to_line(points, line, dr):
    '''
        Return the indices of the points which are within dr of the
        specified line.
    '''
    is_close = []
    for i, point in enumerate(points):
        if line.distance_to(point) < dr:
            is_close.append(i)
    return is_close

def split_by_distance(points, line, dr):
    '''
        Return two new arrays and a list, containing the points closer to and
        farther from the line than the given dr, as well as a boolean
        mask array where True means "farther than dr".

        Returned as a tuple (closer, farther, mask).
    '''
    close_to_line_index = points_close_to_line(points, line, dr)
    mask = np.ones(len(points), dtype=bool)
    mask[close_to_line_index] = False
    closer = np.empty((len(close_to_line_index), 3))
    farther = np.empty((len(mask) - len(closer), 3))
    closer[:] = points[~mask]
    farther[:] = points[mask]
    return closer, farther, mask

def setup_fit_errors():
    '''
        Set up the framework for computing fit errors and return the
        setup object.

        The object contains precomputed symbolic derivatives.

    '''
    ax, ay, az, bx, by, bz = sp.symbols('ax ay az bx by bz')
    yx, yy, yz = sp.symbols('yx yy yz')
    theta, phi = sp.symbols('theta phi')
    conversions_b = []
    conversions_b.append((bx, sp.cos(phi)*sp.sin(theta)))
    conversions_b.append((by, sp.sin(phi)*sp.sin(theta)))
    conversions_b.append((bz, sp.cos(theta)))
    avec = sp.Matrix([[ax], [ay], [az]])
    bvec = sp.Matrix([[bx], [by], [bz]])
    y = sp.Matrix([[yx], [yy], [yz]])
    I = sp.eye(3)
    # Split the chi2 up by each term in the summation
    chi2_cartesian = ((I - bvec*bvec.T)*(avec-y)).T*(I - bvec*bvec.T)*(avec-y)
    chi2_angles = chi2_cartesian.subs(conversions_b)
    coords = sp.symbols('theta phi ax ay az')
    coords_deriv = coords[:-1]
    points = sp.symbols('yx yy yz')
    deriv_coords = []
    derivs = []
    for i, coord1 in enumerate(coords_deriv):
        for j, coord2 in enumerate(coords_deriv[i:]):
            deriv_coords.append((i, i+j, coord1, coord2))
    for i, j, coord1, coord2 in deriv_coords:
        term_abstract = sp.diff(chi2_angles, coord1, coord2)[0]
        derivs.append((i, j, coord1, coord2, term_abstract))
    return derivs

def fit_errors(fit_points, line, precomputed):
    r'''
        Return the covariance matrix for the fit parameters theta, phi,
        and a (anchor point) specified by the given line.

        The rows and columns of the matrix returned are in the order
        theta, phi, a_x, a_y. (a_z is by definition 0 in this
        parametrization.)

        If any diagonal element of the covariance matrix is not strictly
        positive, return None.

        The formula for the chi-square for minimizing the distance from
        points $$\{y_i\}$$ to a line specified by anchor $$a$$ and
        direction $$b$$ is:

        $$ \chi^2 = \sum_i \lvert (I - b^T b)(a - y_i) \rvert^2, $$

        assuming constant errors on each point $$y_i$$. ($$I$$ is the
        identity matrix.)

        The derivatives and evaluations are computed using the Sympy
        module for symbolic manipulation.

        There are 2 linear dependencies in the parameter space (a, b),
        one involving the anchor and one involving the direction. Hence
        there must be 2 parameters eliminated. I will force $$a_z = 0$$
        and use angles on the unit sphere to represent $$b$$. Note the
        first change means tracks parallel to the x-y plane are not
        representable.

    '''
    if precomputed is None:
        return None
    hessian = compute_hessian(fit_points, line, precomputed)
    cov = np.linalg.inv(hessian)
    if any(np.diag(cov) <= 0):
        return None
    return cov

def compute_hessian(fit_points, line, precomputed):
    '''
        Return the Hessian matrix for the least-squares fit.

    '''
    theta_best, phi_best, _, _ = line.coords()
    a_best = line.points('z', 0, 0.1, 3)[0]

    coords = sp.symbols('theta phi ax ay az')
    points = sp.symbols('yx yy yz')
    subs = {coord:val for coord, val in zip(coords, [theta_best,
        phi_best, *a_best])}
    result = np.empty((4, 4))
    for i, j, coord1, coord2, term_abstract in precomputed:
        term = term_abstract.subs(subs.items())
        result[i, j] = 0
        for point in fit_points:
             point_eval = term.evalf(subs={p:pval for p, pval in
                zip(points, point)})
             result[i, j] += point_eval
        result[j, i] = result[i, j]
    return 0.5*result

def fit_line_least_squares(points, start_line, dr):
    '''
        Return the best fit line determined by least-squares fit to the
        points within dr of start_line.
        Specific algorithm used is:
         - direction is the eigenvector corresponding to the largest
           eigenvalue of the covariance matrix
         - anchor point is the average position of the relevant points

        If there are <= 2 points near the guess line, return None.

    '''
    closer, farther, mask = split_by_distance(points, start_line, dr)
    if len(closer) <= 2:
        return None

    anchor = np.mean(closer, axis=0)
    evals, evecs = cov_evals_evecs(closer)
    direction_unnorm = (evecs.T)[0]
    direction_norm = direction_unnorm/np.linalg.norm(direction_unnorm)
    # Guard against the coordinate degeneracy when parallel to xy plane
    if abs(direction_norm[2]) < 1e-3:
        return None
    directions = cartesian_to_spherical(direction_norm.reshape((1,
        3)), constrain=True)
    theta, phi = directions[0]
    best_fit_line = Line.fromDirPoint(theta, phi, *anchor)
    return best_fit_line

def get_fit_line(points, params):
    '''
        Return the best fit line determined by least-squares fit to the
        points identified by the Hough parameters.

        The line identified by the accumulator bin with the most votes
        is taken as the guess. The x-prime/y-prime bin spacing is taken
        as the dr distance.

        Return None if the fit fails.

        Points within dr of the guess line are fed in to the
        least-squares fitter. The best fit line is returned as a
        ``Line`` object.
    '''
    guess_line = line_accumulator_max(params)
    bins = params.position_bins
    dr = bins[1] - bins[0]
    best_fit_line = fit_line_least_squares(points, guess_line, dr)
    return best_fit_line

def iterate_hough_once(points, params, threshold, undo_points=None):
    '''
        Compute the next iteration of the Hough transform and return
        (closer, farther, params, mask, line).

        A track must have at least <threshold> points on it. If there is
        no such track found, return (None, None, params, None, None).

        - closer and farther are arrays with the points split by
          distance to the best fit line.
        - params is the ``HoughParameters`` object to feed to compute_hough
        - mask is a boolean array specifying which indices in points are
          in farther (i.e. True means yes, included in farther).
        - line is the ``Line`` object representing the best fit line
          from the Hough transformation + least-squares.
    '''
    if params.accumulator is None and undo_points is None:
        params = compute_hough(points, params, op='+')
    else:
        params = compute_hough(undo_points, params, op='-')
    best_fit_line = get_fit_line(points, params)
    if best_fit_line is None:
        closer, farther, mask, best_fit_line = None, None, None, None
        return (closer, farther, params, mask, best_fit_line)
    closer, farther, mask = split_by_distance(points, best_fit_line,
            params.dr)
    available_points = points[~params.found_mask]
    new_found_points, _, _ = split_by_distance(available_points, best_fit_line,
            params.dr)
    if len(new_found_points) < threshold:
        closer, farther, mask, best_fit_line = None, None, None, None
    return (closer, farther, params, mask, best_fit_line)

def run_iterative_hough(points, params, threshold, cache=None):
    '''
        Execute the iterative Hough transform on the given points.
        Returns ``(lines, points, params)`` where:
         - ``lines`` is a dict mapping ``Line`` ->  [point_index] (list of
           indices of corresponding points in the ``points`` array)
         - ``points`` is a numpy array of shape (npoints, 3) (= x,y,z)
         - ``params`` is the ``HoughParameters`` object associated with the
           fit
    '''
    original_points = points
    points = original_points.copy()
    lines = {}
    params.found_mask = np.array([False for point in points])
    found_mask = params.found_mask
    undo_points = None
    found_good_line = True
    while found_good_line:
        closer, farther, params, mask, best_fit_line = (
                iterate_hough_once(points, params, threshold,
                    undo_points))
        found_good_line = (closer is not None)
        if found_good_line:
            best_fit_line.cov = fit_errors(closer, best_fit_line, cache)
            lines[best_fit_line] = np.where(~mask)[0]
            undo_points = points[[i for i in lines[best_fit_line] if
                    not found_mask[i]]]
            for i in lines[best_fit_line]:
                found_mask[i] = True
            logger.debug('found good line with %d points' % len(closer))

    return lines, points, params
