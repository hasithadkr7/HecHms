import os
import tempfile
import unittest

import numpy as np
import geopandas as gpd

from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point
from resources import manager as res_mgr


def _voronoi_finite_polygons_2d(vor, radius=None):
    """
    Reconstruct infinite voronoi regions in a 2D diagram to finite
    regions.

    Parameters
    ----------
    vor : Voronoi
        Input diagram
    radius : float, optional
        Distance to 'points at infinity'.

    Returns
    -------
    regions : list of tuples
        Indices of vertices in each revised Voronoi regions.
    vertices : list of tuples
        Coordinates for revised Voronoi vertices. Same as coordinates
        of input vertices, with 'points at infinity' appended to the
        end.

    from: https://stackoverflow.com/questions/20515554/colorize-voronoi-diagram

    """

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # finite region
            new_regions.append(vertices)
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                # finite ridge: already in the region
                continue

            # Compute the missing endpoint of an infinite ridge

            t = vor.points[p2] - vor.points[p1]  # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        # finish
        new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)


def get_voronoi_polygons(points_dict, shape_file, shape_attribute=None, output_shape_file=None, add_total_area=True):
    """
    :param points_dict: dict of points {'id' --> [lon, lat]}
    :param shape_file: shape file path of the area
    :param shape_attribute: attribute list of the interested region [key, value]
    :param output_shape_file: if not none, a shape file will be created with the output
    :param add_total_area: if true, total area shape will also be added to output
    :return:
    geo_dataframe with voronoi polygons with columns ['id', 'lon', 'lat','area', 'geometry'] with last row being the area of the
    shape file
    """
    if shape_attribute is None:
        shape_attribute = ['OBJECTID', 1]

    shape_df = gpd.GeoDataFrame.from_file(shape_file)
    shape_polygon_idx = shape_df.index[shape_df[shape_attribute[0]] == shape_attribute[1]][0]
    shape_polygon = shape_df['geometry'][shape_polygon_idx]

    ids = [p if type(p) == str else np.asscalar(p) for p in points_dict.keys()]
    points = np.array(list(points_dict.values()))[:, :2]
    vor = Voronoi(points)

    regions, vertices = _voronoi_finite_polygons_2d(vor)

    data = []
    for i, region in enumerate(regions):
        polygon = Polygon([tuple(x) for x in vertices[region]])
        if polygon.intersects(shape_polygon):
            intersection = polygon.intersection(shape_polygon)
            data.append({'id': ids[i], 'lon': vor.points[i][0], 'lat': vor.points[i][1], 'area': intersection.area,
                         'geometry': intersection
                         })
    # if add_total_area:
    #     data.append({'id': '__total_area__', 'lon': shape_polygon.centroid.x, 'lat': shape_polygon.centroid.y,
    #                  'area': shape_polygon.area, 'geometry': shape_polygon})

    df = gpd.GeoDataFrame(data, columns=['id', 'lon', 'lat', 'area', 'geometry'], crs=shape_df.crs)

    if output_shape_file is not None:
        df.to_file(output_shape_file)

    return df


def is_inside_geo_df(geo_df, lon, lat, polygon_attr='geometry', return_attr='id'):
    point = Point(lon, lat)
    for i, poly in enumerate(geo_df[polygon_attr]):
        if point.within(poly):
            return geo_df[return_attr][i]
    return None


class TestSpatialUtils(unittest.TestCase):
    def test_get_voronoi_polygons(self):
        points = {
            'Colombo': [79.8653, 6.898158],
            'IBATTARA3': [79.86, 6.89],
            'Isurupaya': [79.92, 6.89],
            'Borella': [79.86, 6.93, ],
            'Kompannaveediya': [79.85, 6.92],
        }

        shp = res_mgr.get_resource_path('extraction/shp/klb-wgs84/klb-wgs84.shp')
        out = tempfile.mkdtemp(prefix='voronoi_')
        result = get_voronoi_polygons(points, shp, ['OBJECTID', 1], output_shape_file=os.path.join(out, 'out.shp'))
        print(result)

    def test_is_inside_polygon(self):
        points = {
            'Colombo': [79.8653, 6.898158],
            'IBATTARA3': [79.86, 6.89],
            'Isurupaya': [79.92, 6.89],
            'Borella': [79.86, 6.93, ],
            'Kompannaveediya': [79.85, 6.92],
        }

        shp = res_mgr.get_resource_path('extraction/shp/klb-wgs84/klb-wgs84.shp')
        result = get_voronoi_polygons(points, shp, ['OBJECTID', 1])
        print(result)
        for k in points.keys():
            pp = is_inside_geo_df(result, points[k][0], points[k][1])
            print(points[k], pp)
            self.assertEqual(pp, k)

    def test_get_voronoi_polygons_kub(self):
        points = {
            'Colombo': [79.8653, 6.898158],
            'IBATTARA3': [79.86, 6.89],
            'Isurupaya': [79.92, 6.89],
            'Daraniyagala': [80.33805556, 6.924444444],
            'Glencourse': [80.20305556, 6.978055556],
            'Hanwella': [80.08166667, 6.909722222],
            'Holombuwa': [80.26480556, 7.185166667],
            'Kitulgala': [80.41777778, 6.989166667],
            'Borella': [79.86, 6.93, ],
            'Kompannaveediya': [79.85, 6.92],
        }

        shp = res_mgr.get_resource_path('extraction/shp/kelani-upper-basin.shp')
        out = tempfile.mkdtemp(prefix='voronoi_')
        print(out)
        result = get_voronoi_polygons(points, shp, ['OBJECTID', 1], output_shape_file=os.path.join(out, 'out.shp'))
        print(result)

    def test_compare_voronoi_polygons(self):

        files = ['up_in_3_thie_join.shp', 'up_in_11_thie_join.shp']
        out = tempfile.mkdtemp(prefix='voronoi_')

        for f in files:
            voronoi_shp_file = res_mgr.get_resource_path('test/shp/%s' % f)
            area_shp_file = res_mgr.get_resource_path('extraction/shp/kub-wgs84/kub-wgs84.shp')

            shape_df = gpd.GeoDataFrame.from_file(voronoi_shp_file)

            points = {}
            for i in range(len(shape_df)):
                points[shape_df['OBJECTID'][i]] = [shape_df['x'][i], shape_df['y'][i]]

            result = get_voronoi_polygons(points, area_shp_file, ['OBJECTID', 1],
                                          output_shape_file=os.path.join(out, '%s_out.shp' % f))

            for i in range(len(shape_df)):
                self.assertAlmostEqual(result['area'][i], shape_df['Shape_Area'][i], places=4)


def suite():
    s = unittest.TestSuite()
    s.addTest(TestSpatialUtils)
    return s
