from resources import manager as res_mgr
from util.spatial_util import get_voronoi_polygons
import pandas as pd
import os
import datetime
import numpy as np
import geopandas as gpd
from scipy.spatial import Voronoi

PROJECT_PATH = '/home/hasitha/QGis/output'


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


def get_voronoi_polygons_kub(points):
    shp = res_mgr.get_resource_path('kub/kelani-upper-basin.shp')
    result = get_voronoi_polygons(points, shp, ['OBJECTID', 1], output_shape_file=os.path.join('/home/hasitha/QGis/test', 'out.shp'))
    print(result.iloc[0])


def get_gage_points():
    gage_csv = res_mgr.get_resource_path('gages/CurwRainGauges.csv')
    gage_df = pd.read_csv(gage_csv)[['name', 'longitude', 'latitude']]
    gage_dict = gage_df.set_index('name').T.to_dict('list')
    return gage_dict


def get_thessian_polygon_from_gage_points(shape_file, gage_points):
    shape = res_mgr.get_resource_path(shape_file)
    # calculate the voronoi/thesian polygons w.r.t given station points.
    thessian_df = get_voronoi_polygons(gage_points, shape, ['OBJECTID', 1],
                                  output_shape_file=os.path.join(PROJECT_PATH, datetime.date.today().strftime('%Y-%m-%d')+'.shp'))
    return thessian_df


def get_catchment_area(catchment_file):
    shape = res_mgr.get_resource_path(catchment_file)
    catchment_df = gpd.GeoDataFrame.from_file(shape)
    return catchment_df


def calculate_intersection(thessian_df, catchment_df):
    for i, catchment_polygon in enumerate(catchment_df['geometry']):
        sub_catchment_name = catchment_df.iloc[i]['Name_of_Su']
        ratio_list = []
        for j, thessian_polygon in enumerate(thessian_df['geometry']):
            if catchment_polygon.intersects(thessian_polygon):
                gage_name = thessian_df.iloc[j]['id']
                intersection = catchment_polygon.intersection(thessian_polygon)
                ratio = np.round(intersection.area / thessian_polygon.area, 4)
                ratio_dic = {'gage_name': gage_name, 'ratio': ratio}
                ratio_list.append(ratio_dic)
        print('')
        sub_dic = {'sub_catchment_name': sub_catchment_name, 'ratios': ratio_list}
        print(sub_dic)


try:
    kub_points = {
        'Mahapallegama': [80.2586, 7.16984],
        'Hingurana': [80.40782, 6.90449],
        'Dickoya': [80.60312, 6.8722],
        'Waga': [80.60312, 6.90678],
        'Hanwella': [80.081667, 6.909722],
        'Norton Bridge': [80.516, 6.9],
        'Kitulgala': [80.41777, 6.98916],
        'Holombuwa': [80.26480, 7.18516],
        'Daraniyagala': [80.33805, 6.92444],
        'Glencourse': [80.20305, 6.97805],
        'Norwood': [80.61466, 6.83563]
    }

    shape_file = 'kub-wgs84/kub-wgs84.shp'
    catchment_file = 'kub/sub_catchments/sub_catchments1.shp'
    thessian_df = get_thessian_polygon_from_gage_points(shape_file, kub_points)
    catchment_df = get_catchment_area(catchment_file)
    calculate_intersection(thessian_df, catchment_df)
except Exception as e:
    print("get_thessian_polygon_from_gage_points|Exception|e : ", e)

