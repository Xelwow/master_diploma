from django.conf import settings

import json
from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import render
from operator import concat, itemgetter
from itertools import groupby

from typing import List, Tuple
from scienceworkserver.anomalies_connecter import connect_features
from scipy.special import comb

# d64e2ebb-52b3-4b64-ac18-4977315a1a5b
class BezierCurve:
    """
    Bezier curve is a weighted sum of a set of control points.
    Generate Bezier curves from a given set of control points.
    This implementation works only for 2d coordinates in the xy plane.
    """

    def __init__(self, list_of_points: List[Tuple[float, float]]):
        """
        list_of_points: Control points in the xy plane on which to interpolate. These
            points control the behavior (shape) of the Bezier curve.
        """
        self.list_of_points = list_of_points
        # Degree determines the flexibility of the curve.
        # Degree = 1 will produce a straight line.
        self.degree = len(list_of_points) - 1

    def basis_function(self, t: float) -> List[float]:
        """
        The basis function determines the weight of each control point at time t.
            t: time value between 0 and 1 inclusive at which to evaluate the basis of
               the curve.
        returns the x, y values of basis function at time t

        >>> curve = BezierCurve([(1,1), (1,2)])
        >>> curve.basis_function(0)
        [1.0, 0.0]
        >>> curve.basis_function(1)
        [0.0, 1.0]
        """
        assert 0 <= t <= 1, "Time t must be between 0 and 1."
        output_values: List[float] = []
        for i in range(len(self.list_of_points)):
            # basis function for each i
            output_values.append(
                comb(self.degree, i) * ((1 - t) **
                                        (self.degree - i)) * (t ** i)
            )
        # the basis must sum up to 1 for it to produce a valid Bezier curve.
        assert round(sum(output_values), 5) == 1
        return output_values

    def bezier_curve_function(self, t: float) -> Tuple[float, float]:
        """
        The function to produce the values of the Bezier curve at time t.
            t: the value of time t at which to evaluate the Bezier function
        Returns the x, y coordinates of the Bezier curve at time t.
            The first point in the curve is when t = 0.
            The last point in the curve is when t = 1.

        >>> curve = BezierCurve([(1,1), (1,2)])
        >>> curve.bezier_curve_function(0)
        (1.0, 1.0)
        >>> curve.bezier_curve_function(1)
        (1.0, 2.0)
        """

        assert 0 <= t <= 1, "Time t must be between 0 and 1."

        basis_function = self.basis_function(t)
        x = 0.0
        y = 0.0
        for i in range(len(self.list_of_points)):
            # For all points, sum up the product of i-th basis function and i-th point.
            x += basis_function[i] * self.list_of_points[i][0]
            y += basis_function[i] * self.list_of_points[i][1]
        return (x, y)

    def plot_curve(self, step_size: float = 0.01):
        bezier_curve = []

        t = 0.0
        while t <= 1:
            value = self.bezier_curve_function(t)
            bezier_curve.append(value)
            t += step_size
        return bezier_curve


file_folder = Path(__file__).resolve().parent
map_url = file_folder / 'a_map_2021-04-19-07_06.json'
aurora_url = file_folder / 'auroras_data.json'


def globe(request):
    return render(request, file_folder / 'globe/index.html', {})


def get_file_data():
    with open(map_url) as json_data:
        return json.load(json_data)

def get_aurora_file_data():
    with open(aurora_url) as json_data:
        return json.load(json_data)

def filter_coords(coords):
    return filter(lambda x: x[2] >= 10, coords)


def get_coordinates(request):
    file_data = get_file_data()
    return JsonResponse({"type": "Feature", "geometry": {"type": file_data['type'], "coordinates":  map_coordinates(file_data['coordinates'])}})


def get_mapped_coordinates(request):
    file_data = get_file_data()
    return JsonResponse(map_features_by_aurora(file_data['coordinates'], file_data['type']))

# Recieves coordinates with parameters: "[Longitude, Latitude, Aurora]"
# Returns: "[Longitude, Latitude]""


def map_coordinates(coordinates):
    return list(map(lambda x: [x[0], x[1]], coordinates))

# Recieves coordinates with parameters: "[Longitude, Latitude, Aurora]"
# Returns GeoJSON with type FeatureCollection filtered by aurora


def map_features_by_aurora(coordinates, geometry_type):
    filtered = filter_coords(coordinates)
    grouped = groupby(filtered, itemgetter(2))
    features = [{"type": "Feature", "geometry": {"type": geometry_type,
                                                 "coordinates": map_coordinates(coords)}} for k, coords in grouped]
    return {"type": "FeatureCollection", "features": features}


def grouped_coord(coordinates):
    filtered = filter_coords(coordinates)
    grouped = groupby(filtered, itemgetter(2))
    sads = [list(coords) for k, coords in grouped]
    return sads


# Arcgis contur layer
# matplotlib с контуром
# Contur to geojson
# turf.js -> contur // to json in plob // кривая бизие и аркгис не понимает их.
# Библиотека для работы
def mapped_coord(request):
    file_data = get_file_data()
    coordinates = file_data['coordinates']
    geometry_type = file_data['type']
    filtered = filter_coords(coordinates)
    return JsonResponse({"type": "Feature", "geometry": {"type": geometry_type, "coordinates":  map_coordinates(filtered)}})


def bezier_coord_all(coords):
    return BezierCurve(coords).plot_curve()


def bezier_coords(coords):
    #print(len(coords))
    beziered_coords = []
    t = 0
    slicer = 100
    if len(coords) < 3:
        return coords
    if slicer >= len(coords):
        curve = BezierCurve(coords)
        curved = curve.plot_curve()
        for x in curved:
            beziered_coords.append(x)
    else:
        while t < len(coords) - slicer:
            curve = BezierCurve(coords[t:t+slicer-1])
            curved = curve.plot_curve()
            for x in curved:
                beziered_coords.append(x)
            t += slicer
    # print(len(beziered_coords))
    return beziered_coords


def bezier_curve(request):
    file_data = get_file_data()
    geometry_type = file_data['type']
    coords = file_data['coordinates']
    filtered = filter_coords(coords)
    mapped = map_coordinates(filtered)
    divided_poles = divide_poles(mapped)
    beziered = bezier_coords(divided_poles[1])
    return JsonResponse({"type": "Feature", "geometry": {"type": geometry_type, "coordinates": beziered}})

def bezier_curve_with_groups(request):
    file_data = get_file_data()
    coords = file_data['coordinates']
    geometry_type = file_data['type']
    return JsonResponse(get_feature_collection(coords))


def coords(request):
    file_data = get_file_data()
    coordinates = file_data['coordinates']
    filtered = filter_coords(coordinates)
    return JsonResponse({"coordinates": map_coordinates(filtered)})


def divide_poles(coordinates):
    south = []
    north = []
    for coord in coordinates:
        if coord[1] > 0:
            north.append(coord)
        else:
            south.append(coord)
    return [south, north]

def bezier_group(group):
    beziered = []
    for obj in group:
        mapped = map_coordinates(obj)
        beziered_obj = bezier_coords(mapped)
        beziered.append(beziered_obj)
    return beziered

def beziered_divided_grouped(coords):
    filtered = filter_coords(coords)
    divided_poles = divide_poles(filtered)
    north_groups = grouped_coord(divided_poles[0])
    south_groups = grouped_coord(divided_poles[1])
    north_beziered = bezier_group(north_groups)
    south_beziered = bezier_group(south_groups)
    return [north_beziered, south_beziered]

def convert_to_features(coords):
    features = []
    for coord in  coords:
        features.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": coord}})
    return features

def convert_features_to_feature_collection(features):
    return {"type": "FeatureCollection", "features": features}

def get_feature_collection(coords):
    grouped = beziered_divided_grouped(coords)
    #north_features = []
    #for north in grouped[0]:
    #   north_features.append(convert_to_features(north))
    #south_features = []
    #for south in grouped[1]:
    #    south_features.append(convert_to_features(south))
    north_features = convert_to_features(grouped[0])
    south_features = convert_to_features(grouped[1])
    concated = north_features + south_features
    converted = convert_features_to_feature_collection(concated)
    print(converted)
    return converted

def bizer_feature(feature):
    copy = feature
    coords = copy['geometry']['coordinates']
    curve = BezierCurve(coords)
    curved_coords = curve.plot_curve()
    copy['geometry']['coordinates'] = curved_coords
    return copy

def auroras_data(request):
    file_data = get_aurora_file_data()
    features = file_data['features']
    beziered_features = []
    for feature in features:
        beziered_features.append(bizer_feature(feature))
    return JsonResponse({"type": "FeatureCollection", "features": beziered_features})

def make_it_short(coords):
    return [coords[0], coords[-1]]

def connect_anomalies(request):
    file_data = get_aurora_file_data()
    features = file_data['features']
    filtered = list(filter(lambda x: x['properties']['title'] == '4.00 ', features))
    i = 10
    #points = []
    #for feature in filtered:
    #    short = make_it_short(feature['geometry']['coordinates'])
    #    points.append({'type': 'Feature', "properties": {"level-index": 6,"level-value": 10.0,"stroke": "#ff0000","stroke-width": 30,"title": str(i)}, 'geometry': {'type': 'LineString', 'coordinates': short}})
    #    i += 1
    connected_features = connect_features(features)
    #beziered_features = []
    #for feature in connected_features:
    #    beziered_features.append(bizer_feature(feature))
    #print(beziered_features)
    #print(points)
    return JsonResponse({"type": "FeatureCollection", "features": connected_features})